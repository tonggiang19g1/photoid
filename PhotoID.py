import sys
import os
import cv2
import time
from PIL import Image, ImageDraw
from appdirs import user_data_dir
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QRadioButton,
    QButtonGroup, QProgressBar, QMessageBox, QAction, QMenu
)
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QIcon, QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import requests

current_version = "4.0" 
face_size = 800
bg_color = (54, 113, 157)
path_save_acc = user_data_dir('PhotoID', 'TouchPro')
os.makedirs(path_save_acc, exist_ok=True)

def taifile(url, path_save):
    response = requests.get(url)
    with open(path_save, 'wb') as file:
        file.write(response.content)

haarcascade_frontalface_default = os.path.join(path_save_acc, 'haarcascade_frontalface_default.xml')
if not os.path.exists(haarcascade_frontalface_default):
    taifile('http://chonanhcuoi.1touch.pro/photoid/haarcascade_frontalface_default.xml', haarcascade_frontalface_default)
    
haarcascade_eye = os.path.join(path_save_acc, 'haarcascade_eye.xml')
if not os.path.exists(haarcascade_eye):
    taifile('http://chonanhcuoi.1touch.pro/photoid/haarcascade_eye.xml', haarcascade_eye)

face_cascade = cv2.CascadeClassifier(path_save_acc + '/haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(path_save_acc + '/haarcascade_eye.xml')
thumuc = os.path.dirname(os.path.realpath(__file__))
logo = os.path.join(thumuc, "images", "icon.ico")
hinhnen = os.path.join(thumuc, "images", "hinhnen.png")

class Worker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    imageSizeIssue = pyqtSignal()
    imagePath = pyqtSignal(str)

    def __init__(self, input_dir, output_dir, aspect_ratio):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.aspect_ratio = aspect_ratio
        self.fix_count = 0

    def run(self):
        if not self.check_image_size(self.input_dir):
            return

        aspect_ratio_str = f"{self.aspect_ratio[0]}x{self.aspect_ratio[1]}"
        if aspect_ratio_str == '600x900':
            aspect_ratio_folder = "2x3"
        elif aspect_ratio_str == '900x1200':
            aspect_ratio_folder = "3x4"
        elif aspect_ratio_str == '1200x1800':
            aspect_ratio_folder = "4x6"
        else:
            self.status.emit(f"Vui lòng chọn tỉ lệ cắt: {aspect_ratio_str}")
            return

        output_dir = os.path.join(self.output_dir, aspect_ratio_folder)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        total_images = sum(1 for filename in os.listdir(self.input_dir)
                          if filename.lower().endswith((".jpg", ".png", ".jpeg", ".bmp", ".tif", ".tiff")))
        progress = 0

        for filename in os.listdir(self.input_dir):
            if filename.lower().endswith((".jpg", ".png", ".jpeg", ".bmp", ".tif", ".tiff")):
                input_path = os.path.join(self.input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                self.crop_faces(input_path, output_path)
                progress += 1
                self.progress.emit(int(progress * 100 / total_images))
                self.status.emit(f'Đang xử lý {progress}/{total_images} hình ảnh...')
                self.imagePath.emit(output_path)

        while True:
            self.status.emit(f'Đang sửa ảnh cắt lỗi lần {self.fix_count + 1}/10...')
            if not self.fix_face(self.input_dir, output_dir, aspect_ratio_folder):
                break
            if self.fix_count >= 10:
                self.status.emit('Một số hình ảnh không thể sửa được. Vui lòng cắt chúng theo cách thủ công.')
                break
            self.fix_count += 1

        for filename in os.listdir(output_dir):
            if filename.lower().endswith((".jpg", ".png", ".jpeg", ".bmp", ".tif", ".tiff")):
                output_path = os.path.join(output_dir, filename)
                in_path = os.path.join(output_dir, 'in')
                if not os.path.exists(in_path):
                    os.makedirs(in_path)
                if aspect_ratio_folder == "2x3":
                    self.trai_anh_2x3(output_path, in_path, filename)
                elif aspect_ratio_folder == "3x4":
                    self.trai_anh_3x4(output_path, in_path, filename)
                elif aspect_ratio_folder == "4x6":
                    self.trai_anh_4x6(output_path, in_path, filename)

        self.status.emit('Xử lý ảnh thẻ hoàn tất.')

    def detect_faces(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        if len(faces) > 0:
            for x, y, w, h in faces:
                roi_gray = gray[y:y + h, x:x + w]
                eyes = eye_cascade.detectMultiScale(roi_gray)
                if len(eyes) >= 1:
                    return True
        return False

    def crop_faces(self, image_path, output_path):
        size = (face_size, face_size)
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=2, minSize=size)
        if len(faces) == 0:
            return
        for i, (x, y, w, h) in enumerate(faces):
            shoulder_height = int(h * 0.8)
            crop_y1 = max(y - shoulder_height + 350, 0)
            crop_y2 = min(y + h + shoulder_height + 350, image.shape[0])
            aspect_ratio = self.aspect_ratio[0] / self.aspect_ratio[1]
            new_w = int((crop_y2 - crop_y1) * aspect_ratio)
            center_x = x + w // 2
            crop_x1 = max(center_x - new_w // 2, 0)
            crop_x2 = min(crop_x1 + new_w, image.shape[1])
            crop_x1 = max(crop_x1, 0)
            crop_x2 = min(crop_x2, image.shape[1])
            crop_y1 = max(crop_y1, 0)
            crop_y2 = min(crop_y2, image.shape[0])
            cropped_image = image[crop_y1:crop_y2, crop_x1:crop_x2]
            resized_image = cv2.resize(cropped_image, (self.aspect_ratio[0], self.aspect_ratio[1]))
            cv2.imwrite(output_path, resized_image)
            break

    def fix_face(self, input_dir, output_dir, aspect_ratio):
        self.fix_count += 1
        images_without_faces = self.detect_faces_in_directory(output_dir)
        if not images_without_faces:
            return False
        for image_name in images_without_faces:
            self.crop_faces(os.path.join(input_dir, image_name), os.path.join(output_dir, image_name))
        return True

    def detect_faces_in_directory(self, directory):
        images_without_faces = []
        for filename in os.listdir(directory):
            if filename.lower().endswith((".jpg", ".png", ".jpeg", ".bmp", ".tif", ".tiff")):
                image_path = os.path.join(directory, filename)
                image = cv2.imread(image_path)
                if not self.detect_faces(image):
                    images_without_faces.append(filename)
        return images_without_faces

    def check_image_size(self, input_dir):
        for filename in os.listdir(input_dir):
            if filename.lower().endswith((".jpg", ".png", ".jpeg", ".bmp", ".tif", ".tiff")):
                input_path = os.path.join(input_dir, filename)
                original_image = Image.open(input_path)
                width, height = original_image.size
                if width < 4000 or height < 4000:
                    self.imageSizeIssue.emit()
                    return False
        return True

    def trai_anh_3x4(self, path_input, path_output, filename):
        if not os.path.exists(path_input):
            return
        canvas_width = 4500
        canvas_height = 3000
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        photo = Image.open(path_input)
        num_photos_per_row = 4
        num_photos_per_column = 2
        photo_width = 900
        photo_height = 1200
        spacing = 25
        row_spacing = (canvas_width - (num_photos_per_row * photo_width + (num_photos_per_row - 1) * spacing)) // 2
        column_spacing = (canvas_height - (num_photos_per_column * photo_height + (num_photos_per_column - 1) * spacing)) // 2
        x = row_spacing
        y = column_spacing
        for _ in range(num_photos_per_column):
            for _ in range(num_photos_per_row):
                canvas.paste(photo, (x, y))
                x += photo_width + spacing
            x = row_spacing
            y += photo_height + spacing
        canvas.save(path_output + '/' + filename)

    def trai_anh_2x3(self, path_input, path_output, filename):
        if not os.path.exists(path_input):
            return
        canvas_width = 3000
        canvas_height = 4500
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        photo_2x3 = Image.open(path_input)
        num_rows = 4
        num_cols = 4
        photo_width = 600
        photo_height = 900
        spacing = 25
        total_width = num_cols * photo_width + (num_cols - 1) * spacing
        total_height = num_rows * photo_height + (num_rows - 1) * spacing
        start_x = (canvas_width - total_width) // 2
        start_y = (canvas_height - total_height) // 2
        x = start_x
        y = start_y
        for row in range(num_rows):
            for col in range(num_cols):
                canvas.paste(photo_2x3, (x, y))
                x += photo_width + spacing
            x = start_x
            y += photo_height + spacing
        canvas.save(path_output + '/' + filename)

    def trai_anh_4x6(self, path_input, path_output, filename):
        if not os.path.exists(path_input):
            return
        canvas_width = 3000
        canvas_height = 4500
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        photo = Image.open(path_input)
        num_photos_per_row = 2
        num_rows = 2
        photo_width = 1200
        photo_height = 1800
        spacing = 25
        total_width = num_photos_per_row * photo_width + (num_photos_per_row - 1) * spacing
        total_height = num_rows * photo_height + (num_rows - 1) * spacing
        start_x = (canvas_width - total_width) // 2
        start_y = (canvas_height - total_height) // 2
        x = start_x
        y = start_y
        for _ in range(num_rows):
            for _ in range(num_photos_per_row):
                canvas.paste(photo, (x, y))
                x += photo_width + spacing
            y += photo_height + spacing
            x = start_x
        canvas.save(path_output + '/' + filename)

class PhotoProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        self.setWindowTitle(f'PhotoID V{current_version} Crack By Giang Design - Bản quyền vĩnh viễn')
        self.setFixedSize(560, 750)
        self.setWindowIcon(QIcon(logo))
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout()

        title_label = QLabel('PhotoID - Ảnh Thẻ Tự Động ')
        title_label.setFont(QFont('Arial', 18))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        input_layout = QHBoxLayout()
        self.input_label = QLabel('Chọn Thư Mục Ảnh:')
        input_layout.addWidget(self.input_label)
        self.input_folder = QLineEdit()
        self.input_folder.setFixedWidth(300)
        input_layout.addWidget(self.input_folder)
        self.browse_input_button = QPushButton('Chọn Thư Mục')
        self.browse_input_button.setObjectName('browseButton')
        self.browse_input_button.clicked.connect(self.browse_input)
        input_layout.addWidget(self.browse_input_button)
        main_layout.addLayout(input_layout)

        output_layout = QHBoxLayout()
        self.output_label = QLabel('Chọn Thư Mục Lưu Ảnh')
        output_layout.addWidget(self.output_label)
        self.output_folder = QLineEdit()
        self.output_folder.setFixedWidth(300)
        output_layout.addWidget(self.output_folder)
        self.browse_output_button = QPushButton('Chọn Thư Mục')
        self.browse_output_button.setObjectName('browseButton')
        self.browse_output_button.clicked.connect(self.browse_output)
        output_layout.addWidget(self.browse_output_button)
        main_layout.addLayout(output_layout)

        aspect_ratio_layout = QHBoxLayout()
        self.aspect_ratio_label = QLabel('Chọn Kích Thước:')
        self.aspect_ratio_label.setFont(QFont('Arial', 10))
        aspect_ratio_layout.addWidget(self.aspect_ratio_label)

        self.aspect_ratio_group = QButtonGroup(self)
        self.aspect_ratio_2x3 = QRadioButton('2x3')
        self.aspect_ratio_3x4 = QRadioButton('3x4')
        self.aspect_ratio_4x6 = QRadioButton('4x6')
        self.aspect_ratio_group.addButton(self.aspect_ratio_2x3)
        self.aspect_ratio_group.addButton(self.aspect_ratio_3x4)
        self.aspect_ratio_group.addButton(self.aspect_ratio_4x6)

        aspect_ratio_layout.addWidget(self.aspect_ratio_2x3)
        aspect_ratio_layout.addWidget(self.aspect_ratio_3x4)
        aspect_ratio_layout.addWidget(self.aspect_ratio_4x6)
        aspect_ratio_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(aspect_ratio_layout)

        self.start_button_widget = QPushButton('Bắt Đầu')
        self.start_button_widget.setObjectName('blueButton')
        self.start_button_widget.clicked.connect(self.start_processing)
        main_layout.addWidget(self.start_button_widget)

        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel('Trạng Thái')
        main_layout.addWidget(self.status_label)

        current_image_layout = QVBoxLayout()
        current_image_layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel('Hình Ảnh Xem Trước')
        self.image_label.setAlignment(Qt.AlignCenter)
        current_image_layout.addWidget(self.image_label)

        self.current_image_display = QLabel(self)
        self.current_image_display.setStyleSheet(f"""
            QLabel {{
                background-image: url({hinhnen.replace("\\", "/")});
                background-repeat: no-repeat;
                background-position: center;
                border: 1px solid #ddd;
            }}
        """)
        self.current_image_display.setFixedSize(300, 400)
        current_image_layout.addWidget(self.current_image_display)

        centered_layout = QHBoxLayout()
        centered_layout.addStretch(1)
        centered_layout.addLayout(current_image_layout)
        centered_layout.addStretch(1)

        main_layout.addLayout(centered_layout)
        self.central_widget.setLayout(main_layout)

        # Add menu bar
        self.menu_bar = self.menuBar()
        self.setup_menu_bar()

    def setup_menu_bar(self):
        info_menu = self.menu_bar.addMenu('Thông tin')
        about_action = QAction('Giới thiệu', self)
        about_action.triggered.connect(self.open_about)
        info_menu.addAction(about_action)

        support_menu = self.menu_bar.addMenu('Hỗ trợ')
        support_menu.addAction(QtGui.QIcon(os.path.join(thumuc, "images", "home.png")), "Trang chủ", self.touch_pro)
        support_menu.addAction(QtGui.QIcon(os.path.join(thumuc, "images", "group.png")), "Nhóm hỗ trợ", self.Facebook)

    def open_about(self):
        about_text = f"PhotoID V{current_version}\nPhiên bản mới nhất\nBản quyền: Vĩnh viễn"
        QMessageBox.information(self, 'Giới thiệu', about_text)

    def touch_pro(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://dulieucuoi.com'))

    def Facebook(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://dulieucuoi.com'))

    def apply_styles(self):
        self.setStyleSheet("""
        #browseButton {
            background-color: #3498db;
            border: none;
            color: white;
            padding: 10px 10px;
            font-size: 14px;
            border-radius: 4px;
        }
        #browseButton:hover {
            background-color: #2980b9;
        }
        #blueButton {
            background-color: #3498db;
            border: none;
            color: white;
            padding: 10px 10px;
            font-size: 14px;
            border-radius: 4px;
        }
        #blueButton:hover {
            background-color: #2980b9;
        }
        QLineEdit {
            background-color: #D9E6F5;
            color: black;
            border-radius: 5px;
            padding: 8px;
        }
        """)

    def browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, 'Vui lòng chọn thư chứa ảnh')
        if folder:
            self.input_folder.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, 'Vui lòng chọn thư mục lưu ảnh')
        if folder:
            self.output_folder.setText(folder)

    def start_processing(self):
        input_dir = self.input_folder.text()
        output_dir = self.output_folder.text()
        aspect_ratio = self.get_aspect_ratio()
        if not input_dir or not output_dir or not aspect_ratio:
            QMessageBox.warning(self, 'Cảnh báo', 'Vui lòng cung cấp tất cả thông tin được yêu cầu.')
            return

        self.thread = Worker(input_dir, output_dir, aspect_ratio)
        self.thread.progress.connect(self.update_progress)
        self.thread.status.connect(self.update_status)
        self.thread.imageSizeIssue.connect(self.check_image_size)
        self.thread.imagePath.connect(self.update_image_display)
        self.thread.start()
        
    def get_aspect_ratio(self):
        if self.aspect_ratio_2x3.isChecked():
            return (600, 900)
        elif self.aspect_ratio_3x4.isChecked():
            return (900, 1200)
        elif self.aspect_ratio_4x6.isChecked():
            return (1200, 1800)
        return None

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_label.setText(message)

    def update_image_display(self, image_path):
        if os.path.exists(image_path):
            image = QImage(image_path)
            pixmap = QPixmap.fromImage(image)
            self.current_image_display.setPixmap(pixmap.scaled(400, 450, Qt.KeepAspectRatio))

    def check_image_size(self):
        QMessageBox.warning(self, 'Cảnh báo', 'Một số hình ảnh chưa đạt kích thước chuẩn')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoProcessor()
    window.show()
    sys.exit(app.exec_())