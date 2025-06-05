# Ethernet Packet Generator

## Mục đích
Chương trình hỗ trợ tạo và gửi gói tin Ethernet (theo chuẩn Autosar) phục vụ kiểm thử hệ thống, với giao diện trực quan, dễ sử dụng, lấy dữ liệu cấu hình từ file DBC và source Autosar.

## Tính năng chính
- Chọn message từ file DBC, nhập giá trị signal, tự động tính toán payload.
- Sinh gói tin Ethernet hoàn chỉnh (Ethernet/IPv4/UDP/Autosar PDU).
- Hiển thị chi tiết từng trường của gói tin dưới dạng widget trực quan (giống Vector Canoe).
- Gửi gói tin ra test bench qua UDP.
- Hỗ trợ chọn thư mục source Autosar và variant để tự động lấy thông tin MAC, IP, message_id.

## Cách sử dụng sau khi build thành file .exe

1. **Chạy chương trình**
   - Tìm file `ETH_Generater.exe` trong thư mục đã build (thường là `dist` hoặc thư mục bạn chỉ định khi build).
   - Nhấp đúp vào `ETH_Generater.exe` để khởi động chương trình.

2. **Các bước thao tác**
   - Khi chương trình mở lên, làm theo các bước sau:
     - Chọn/thay đổi thư mục source Autosar và variant khi được yêu cầu.
     - Chọn message cần tạo từ combobox.
     - Nhập giá trị các signal hoặc chọn preset (Min/Max/Mid...).
     - Nhấn "Tạo ETH Packet" để sinh gói tin và xem chi tiết.
     - Nhấn "Gửi ETH Packet" để gửi gói tin ra test bench.

3. **Lưu ý**
   - Đảm bảo file `DBC/DBC.csv` và các file cấu hình cần thiết nằm đúng vị trí so với file `.exe`.
   - Nếu chương trình báo thiếu file hoặc không tìm thấy thư mục, kiểm tra lại cấu trúc thư mục và quyền truy cập.
   - Không cần cài đặt Python hoặc các thư viện phụ thuộc khi chạy file `.exe`.

## Lưu ý
- Đường dẫn mặc định khi chọn source là `Y:/Source` (có thể thay đổi trong code).
- Chương trình không thay đổi file source, chỉ đọc thông tin cấu hình.
- Nếu có lỗi về thiếu file hoặc cấu trúc thư mục, kiểm tra lại đường dẫn và quyền truy cập.

## Liên hệ
Mọi thắc mắc hoặc góp ý, vui lòng liên hệ tác giả chương trình: loc.nguyen@forvia.com.
