# HK STUDENT HUB – HỆ THỐNG QUẢN LÝ VÀ KẾT NỐI HỌC SINH THPT HƯƠNG KHÊ

> **Đơn vị chủ quản**: TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH  
> **Thông điệp cốt lõi**: *“Kỷ cương số – Thi đua minh bạch – Đồng hành cùng học sinh”*

---

## 1. GIỚI THIỆU TỔNG QUAN

**HK Student Hub** là hệ thống phần mềm nghiệp vụ giáo dục toàn diện được thiết kế chuyên biệt cho Trường THPT Hương Khê (Hà Tĩnh). Hệ thống số hóa toàn bộ quy trình quản lý nền nếp học sinh, tự động hóa tính điểm và xếp hạng thi đua Chi đoàn, cảnh báo sớm nguy cơ vi phạm cho Giáo viên chủ nhiệm (GVCN), đồng thời tích hợp phân hệ độc lập **“Góc sẻ chia”** – kênh kết nối tư vấn tâm lý học đường an toàn, bảo mật.

### Các Phân hệ Cốt lõi:
1. **Quản lý Nền nếp & Ghi nhận Vi phạm Nhanh**: Tối ưu cho điện thoại của Đội Sao đỏ và Giáo viên; quy trình thẩm định 5 trạng thái (*Chờ xác minh*, *Đã xác minh*, *Không đủ căn cứ*, *Đã điều chỉnh*, *Đang khiếu nại*); chỉ vi phạm đã xác minh mới trừ điểm.
2. **Thi đua Chi đoàn Tự động**: Biểu điểm linh hoạt (Khởi điểm 100đ + Điểm cộng phong trào Đoàn − Điểm trừ vi phạm); tự động cập nhật xếp hạng theo tuần/tháng/kỳ; chốt sổ kết quả; xuất báo cáo Excel/PDF.
3. **Cảnh báo Sớm & Phối hợp GVCN**: Tự động phát hiện học sinh đi học muộn &ge; 3 lần/tuần hoặc lỗi lặp lại; chuyển thông báo riêng đến GVCN; ghi nhận nhật ký can thiệp sư phạm.
4. **Góc sẻ chia – Tư vấn Tâm lý Học đường**: Phân hệ độc lập, cách ly dữ liệu nghiêm ngặt; cho phép học sinh gửi tâm sự ẩn danh hoặc có định danh; cấp mã tra cứu bí mật; chuyên viên tâm lý ghi chú chuyên môn; hướng dẫn an toàn khẩn cấp (Tổng đài 111).
5. **Dashboard Phân quyền RBAC**: Giao diện và dữ liệu thay đổi linh hoạt theo vai trò đăng nhập.
6. **Báo cáo & Kiểm toán Hệ thống**: Xuất file Excel/PDF tiêu chuẩn có tiêu đề trường; lưu trữ nhật ký thao tác (Audit Logs).

---

## 2. KIẾN TRÚC VÀ CÔNG NGHỆ

- **Backend**: Python 3.12, Django 6.1, Django REST Framework.
- **Frontend**: Responsive Single-Page Application (SPA) tích hợp giao diện hiện đại, Tailwind CSS, Chart.js, Lucide Icons (100% tiếng Việt).
- **Cơ sở dữ liệu**: SQLite cho môi trường thử nghiệm cục bộ; sẵn sàng chuyển đổi PostgreSQL cho môi trường sản xuất.
- **Báo cáo**: OpenPyXL (Excel), ReportLab (PDF chuẩn văn bản giáo dục).
- **Đóng gói & Triển khai**: Docker & Docker Compose (Production Ready).

---

## 3. CƠ CHẾ XÁC THỰC VÀ BẢO MẬT PHÂN QUYỀN (RBAC)

Hệ thống thiết lập hàng rào bảo mật nghiêm ngặt theo đúng nguyên tắc:
1. **Bắt buộc đăng nhập (Login Gate)**: Người dùng bắt buộc phải xác thực thông qua màn hình đăng nhập với `username` và `password`. Mọi truy cập chưa đăng nhập đều bị khóa lại màn hình đăng nhập.
2. **Không tự ý chọn vai trò**: Đã loại bỏ hoàn toàn menu chọn vai trò tự do trên giao diện. Người dùng đăng nhập tài khoản nào sẽ nhận đúng chức vụ và giới hạn quyền hạn của tài khoản đó.
3. **Chỉ Quản trị viên (Admin) mới có quyền duyệt chức vụ & quyền hạn**:
   - Chỉ tài khoản có vai trò `ADMIN` mới nhìn thấy và truy cập được phân hệ **“Duyệt chức vụ & Quyền”** (`/api/core/users/`).
   - Mọi nỗ lực từ các tài khoản khác (Đoàn trường, BGH, GVCN, Học sinh) nhằm thay đổi vai trò hoặc cấp quyền đều bị máy chủ chặn mã lỗi `403 Forbidden`.
   - Mỗi lần Admin duyệt đổi chức vụ hoặc cấp quyền chuyên biệt (xác minh vi phạm, xem tư vấn tâm lý) đều được lưu vào nhật ký `AuditLog`.

---

## 4. DANH SÁCH TÀI KHOẢN MẪU ĐỂ ĐĂNG NHẬP KIỂM THỬ

| STT | Vai trò được Admin duyệt | Tên đăng nhập | Mật khẩu xác thực | Người dùng đại diện | Quyền hạn được duyệt |
|:---:|---|---|---|---|---|
| **1** | **Quản trị viên** (Admin) | `admin` | `admin_password_2026` | Quản trị viên hệ thống | Toàn quyền cấu hình, phê duyệt chức vụ người dùng, xem audit logs. |
| **2** | **Ban Giám hiệu** (BGH) | `bgh.huongkhe` | `bgh_password_2026` | Thầy Phan Thanh Toàn | Theo dõi nền nếp toàn trường, chốt kỳ thi đua, xuất văn bản PDF. |
| **3** | **Đoàn trường** | `doantruong.hk` | `doan_password_2026` | Thầy Trần Văn Đoàn | Thẩm định và xác minh vi phạm Sao đỏ, cộng điểm phong trào, tính lại BXH. |
| **4** | **Đội Sao đỏ** (Trực tuần) | `saodo.tuan1` | `saodo_password_2026` | Em Hoàng Minh Thắng | Ghi nhận nhanh vi phạm trên điện thoại, theo dõi duyệt bản ghi của mình. |
| **5** | **GVCN** | `gvcn.10a1` | `gvcn_password_2026` | Cô Nguyễn Thị Mai | Theo dõi lớp 10A1, nhận cảnh báo sớm (đi muộn 3 lần), ghi can thiệp sư phạm. |
| **6** | **Học sinh** | `hocsinh.nam` | `hocsinh_password_2026` | Em Nguyễn Văn Nam | Tra cứu vi phạm cá nhân, gửi giải trình, gửi tâm sự vào Góc sẻ chia. |
| **7** | **Chuyên viên tâm lý** | `tamly.huongkhe` | `tamly_password_2026` | Cô Đặng Thùy Linh | Được Admin cấp quyền chuyên biệt truy cập hồ sơ bảo mật Góc sẻ chia. |

---

## 4. HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY DỰ ÁN

### 4.1. Chạy trên máy tính (Cục bộ)
```bash
# 1. Di chuyển vào thư mục dự án
cd "C:\Users\Xuan Cuong\.gemini\antigravity\scratch\hk-student-hub"

# 2. Cài đặt các gói phụ thuộc (nếu chưa có)
python -m pip install django djangorestframework django-cors-headers openpyxl reportlab pillow

# 3. Chạy migration cơ sở dữ liệu
python manage.py migrate

# 4. Nạp dữ liệu mẫu THPT Hương Khê
python manage.py seed_hk_data

# 5. Khởi chạy máy chủ phát triển
python manage.py runserver 127.0.0.1:8000
```
Truy cập trình duyệt tại địa chỉ: `http://127.0.0.1:8000`

### 4.2. Chạy với Docker & Docker Compose
```bash
# Khởi chạy toàn bộ hệ thống gồm máy chủ web Gunicorn và PostgreSQL
docker-compose up --build -d
```

### 4.3. Lệnh quản lý dữ liệu mẫu
- Khởi tạo dữ liệu mẫu: `python manage.py seed_hk_data`
- Xóa sạch dữ liệu mẫu an toàn: `python manage.py seed_hk_data --clean`

---

## 5. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG (ACCEPTANCE CRITERIA)

Dự án đã tích hợp bộ kiểm thử tích hợp tự động (`core/tests.py`) kiểm tra nghiêm ngặt 10 tiêu chí nghiệm thu:

```text
Ran 9 tests in 26.218s
OK (100% Passed)
```

1. **Sao đỏ tạo bản ghi vi phạm**: Sinh mã `VP-YYYYMMDD-XXXX` tự động, lưu trữ đúng lớp và học sinh.
2. **Bản ghi chưa xác minh không trừ điểm**: Điểm thi đua của Chi đoàn giữ nguyên 100đ khi vi phạm đang ở trạng thái `PENDING`.
3. **Đoàn trường xác minh điểm**: Khi chuyển trạng thái sang `VERIFIED`, điểm thi đua tự động cập nhật chính xác (ví dụ trừ 2.0đ còn 98.0đ).
4. **GVCN chỉ xem lớp được phân công**: GVCN 10A1 chỉ thấy dữ liệu lớp 10A1, không thấy lớp khác.
5. **Học sinh chỉ xem thông tin bản thân**: Học sinh không truy cập được hồ sơ học sinh khác.
6. **Cách ly dữ liệu tư vấn tâm lý**: Tài khoản Đoàn trường, Sao đỏ, GVCN hoặc học sinh khác khi truy cập API tư vấn tâm lý đều bị chặn `403 Forbidden`. Chỉ tài khoản có quyền chuyên biệt `has_counseling_access` mới được phép.
7. **Không rò rỉ dữ liệu tư vấn**: Hồ sơ tâm sự tuyệt đối không xuất hiện trong bảng xếp hạng thi đua hay báo cáo xuất ra.
8. **Chốt sổ kỳ thi đua**: Sau khi khóa kỳ thi đua, các vi phạm phát sinh sau không tự ý làm sai lệch kết quả đã chốt.
9. **Báo cáo Excel & PDF**: Sinh tệp nhị phân hợp lệ, đầy đủ tiêu đề Trường THPT Hương Khê và chữ ký phê duyệt.

---

## 6. TÀI LIỆU HƯỚNG DẪN SỬ DỤNG THEO VAI TRÒ

### A. Dành cho Ban Giám hiệu
- **Theo dõi toàn trường**: Đăng nhập xem bảng thống kê số lượt vi phạm trong ngày, số bản ghi chờ Đoàn trường xử lý, số học sinh thuộc diện cảnh báo sớm.
- **Phê duyệt bảng xếp hạng**: Truy cập tab *Thi đua Chi đoàn*, theo dõi điểm cộng/trừ và bấm *Chốt kết quả* sau khi kỳ thi đua kết thúc.
- **Xuất báo cáo**: Nhấn *Xuất Excel* hoặc *Xuất PDF* để in ấn văn bản trình ký ban hành.

### B. Dành cho Đoàn trường
- **Tiếp nhận & Xác minh vi phạm**: Truy cập tab *Quản lý nền nếp*, lọc các bản ghi có trạng thái *Chờ xác minh*. Nhấn *Xác minh* để chấp thuận (trừ điểm), bác bỏ (không đủ căn cứ, 0đ) hoặc điều chỉnh mức điểm.
- **Xử lý khiếu nại**: Xem các bản ghi có trạng thái *Đang khiếu nại/giải trình* từ học sinh hoặc GVCN để xem xét lại sự việc khách quan.
- **Cộng điểm phong trào**: Truy cập tab *Thi đua Chi đoàn*, chọn nút *+ Cộng điểm* cho các Chi đoàn có thành tích văn nghệ, thể thao, bảo vệ môi trường.
- **Tính toán lại điểm**: Nhấn *Tính lại điểm tự động* để hệ thống quét toàn bộ vi phạm đã xác minh và xếp hạng lại.

### C. Dành cho Đội Sao đỏ (Trực tuần)
- **Ghi nhận vi phạm nhanh**: Nhấn nút vàng *Ghi nhận vi phạm* (tối ưu cho màn hình điện thoại).
  - Bước 1: Chọn lớp.
  - Bước 2: Chọn học sinh (hoặc chọn Tập thể lớp).
  - Bước 3: Chọn lỗi từ danh mục nội quy (hệ thống hiển thị điểm trừ dự kiến).
  - Bước 4: Nhập vị trí và thời gian.
  - Bước 5: Đính kèm ảnh chụp minh chứng (nếu có và được phép).
  - Bước 6: Nhấn *Gửi bản ghi để xác minh*.
- **Theo dõi bản ghi**: Xem danh sách các bản ghi do mình tạo và trạng thái phê duyệt của Đoàn trường.

### D. Dành cho Giáo viên chủ nhiệm (GVCN)
- **Theo dõi lớp chủ nhiệm**: Dashboard hiển thị riêng thông tin lớp được phân công (ví dụ Lớp 10A1).
- **Tiếp nhận cảnh báo sớm**: Khi học sinh trong lớp đi học muộn &ge; 3 lần hoặc vi phạm lặp lại, hệ thống gửi cảnh báo vào tab *Cảnh báo & GVCN*.
- **Ghi nhận can thiệp sư phạm**: Nhấn *Ghi nhận can thiệp & Hỗ trợ* để ghi lại biện pháp (gặp trao đổi riêng, liên hệ phụ huynh, giao bạn trong tổ hỗ trợ...) và kết quả chuyển biến.
- **Gửi khiếu nại/giải trình**: Nếu có sự việc chưa chính xác đối với học sinh lớp mình, GVCN có thể nhấn *Khiếu nại* để đề nghị Đoàn trường xác minh lại.

### E. Dành cho Học sinh
- **Tra cứu nền nếp cá nhân**: Xem lịch sử các lần vi phạm của bản thân, điểm trừ và trạng thái.
- **Gửi giải trình**: Nếu có lý do chính đáng (ví dụ áo ướt do mưa lũ, hỏng xe có xác nhận), nhấn *Khiếu nại* và nhập lý do giải trình gửi Đoàn trường.
- **Sử dụng “Góc sẻ chia”**:
  - Chọn tab *Góc sẻ chia*, chọn chủ đề (áp lực học tập, bạn bè, gia đình, hòa nhập...).
  - Nhập tâm sự và chọn hình thức phản hồi mong muốn.
  - Có thể bật chế độ **Ẩn danh** và nhập bí danh.
  - Nhận **Mã tra cứu bí mật** (VD: `GSC-2026-X8F9`) để theo dõi phản hồi và lịch hẹn tư vấn mà không sợ lộ danh tính.

### F. Dành cho Chuyên viên Tư vấn Tâm lý
- **Tiếp nhận hồ sơ**: Truy cập tab *Góc sẻ chia* với quyền chuyên môn để đọc nội dung tâm sự từ học sinh.
- **Cảnh báo khẩn cấp**: Các hồ sơ chứa nội dung nguy cơ an toàn/tự hại sẽ được gắn cờ màu đỏ ưu tiên xử lý.
- **Cập nhật tiến trình**: Cập nhật trạng thái (*Đã tiếp nhận*, *Đang hỗ trợ*, *Đã hẹn trao đổi*, *Hoàn thành*).
- **Ghi chép chuyên môn**: Ghi lại lưu ý tư vấn và phương án đồng hành riêng tư.

---

## 7. CHÍNH SÁCH BẢO MẬT VÀ QUYỀN RIÊNG TƯ DỮ LIỆU

1. **Phân vùng dữ liệu tư vấn**: Bảng dữ liệu tư vấn tâm lý được bảo vệ nghiêm ngặt ở cấp độ Server-side REST API; không cho phép tài khoản thông thường truy vấn.
2. **Quy định về ảnh minh chứng**: Ảnh minh chứng vi phạm chỉ phục vụ công tác thẩm định nội bộ của Đoàn trường, không công khai lên bảng xếp hạng hoặc gửi cho học sinh khác.
3. **Nhật ký thao tác (Audit Logs)**: Ghi nhận mọi thao tác điều chỉnh điểm và xác minh vi phạm, bảo đảm tính minh bạch tuyệt đối; không ghi nội dung tâm sự hay mật khẩu vào nhật ký.
4. **Quy trình an toàn học đường**: Hệ thống cung cấp chỉ dẫn rõ ràng về Tổng đài Quốc gia 111 và các kênh hỗ trợ trực tiếp tại trường khi học sinh gặp tình huống khẩn cấp.

# THPTHK
