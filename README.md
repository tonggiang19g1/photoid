# PhotoID - Ứng dụng xử lý ảnh thẻ tự động

PhotoID là một ứng dụng desktop được phát triển bằng Python với giao diện PyQt5, giúp tự động xử lý ảnh thẻ (ID photo) với các kích thước chuẩn như 2x3, 3x4, 4x6. Ứng dụng sử dụng OpenCV để phát hiện khuôn mặt và ghép ảnh theo bố cục in ấn.

**Phiên bản hiện tại:** V4.0  
**Trạng thái bản quyền:** Vĩnh viễn  

---

## Tính năng chính
- **Phát hiện và cắt ảnh tự động:** Tự động phát hiện khuôn mặt trong ảnh và cắt theo tỷ lệ mong muốn (2x3, 3x4, 4x6).
- **Ghép ảnh in ấn:** Sắp xếp ảnh vào bố cục phù hợp để in trên khổ giấy lớn.
- **Xem trước ảnh:** Hiển thị ảnh đã xử lý ngay trong giao diện.
- **Hỗ trợ nhiều định dạng ảnh:** JPG, PNG, JPEG, BMP, TIF, TIFF.

---

## Yêu cầu hệ thống
- **Hệ điều hành:** Windows (đã kiểm tra trên Windows 10), có thể hoạt động trên Linux/Mac với điều chỉnh nhỏ.
- **Python:** 3.8 hoặc cao hơn.
- **Thư viện cần thiết:**
  - `PyQt5`
  - `opencv-python`
  - `pillow`
  - `appdirs`
  - `requests`

---
