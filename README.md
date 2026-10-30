# 🎓 HK STUDENT HUB – HỆ THỐNG QUẢN LÝ VÀ KẾT NỐI HỌC SINH THPT HƯƠNG KHÊ

> **Đơn vị chủ quản**: TRƯỜNG THPT HƯƠNG KHÊ – TỈNH HÀ TĨNH  
> **Thông điệp cốt lõi**: *“Kỷ cương số – Thi đua minh bạch – Đồng hành giáo dục toàn diện”*  
> **Trang chủ / Production URL**: [https://edumentor.io.vn](https://edumentor.io.vn)  
> **Mã nguồn GitHub**: [https://github.com/cuonghk1108/THPTHK](https://github.com/cuonghk1108/THPTHK)

---

## 📌 1. GIỚI THIỆU TỔNG QUAN

**HK Student Hub** là nền tảng quản lý trường học số toàn diện được nghiên cứu và phát triển chuyên biệt cho **Trường THPT Hương Khê** (Hà Tĩnh). Hệ thống số hóa 100% quy trình thi đua nề nếp học sinh, tự động hóa tính điểm xếp hạng Chi đoàn, theo dõi và nhận xét học sinh theo từng lớp học, cảnh báo sớm nguy cơ vi phạm cho Giáo viên chủ nhiệm (GVCN), đồng thời tích hợp phân hệ tư vấn tâm lý học đường **“Góc sẻ chia”** an toàn và tuyệt đối bảo mật.

---

## ⭐ 2. CÁC PHÂN HỆ VÀ TÍNH NĂNG NỔI BẬT

### 2.1. Quản lý Lớp học & Sổ tay Nhận xét Học sinh (Teacher Classes)
* **Phân công giảng dạy linh hoạt**: Hệ thống hỗ trợ phân công Giáo viên chủ nhiệm (GVCN) và Giáo viên bộ môn (GVBM) theo từng lớp và môn học.
* **Danh sách lớp học toàn trường**: Bộ lọc đa cấp thông minh theo Khối (10, 11, 12) và danh sách đầy đủ tất cả các lớp của toàn trường (10A1 - 10A22, 11A1 - 11A21, 12A1 - 12A22) sắp xếp tự nhiên theo bảng chữ cái.
* **Nhận xét đích danh học sinh**: Giáo viên bộ môn khi vào lớp có thể chọn đích danh học sinh để gửi nhận xét, đánh giá tinh thần học tập, kết quả bài kiểm tra hoặc nhắc nhở ý thức.
* **Hồ sơ học sinh cá nhân hóa**: Xem thông tin lý lịch, tình trạng học tập, quá trình nề nếp và lịch sử nhận xét từ các giáo viên.

### 2.2. Phân quyền & Quy trình Khiếu nại của Lớp trưởng (Class Monitor Workflow)
* **Bổ nhiệm Lớp trưởng chặt chẽ**: Chỉ **Quản trị viên (Admin)**, **Đoàn trường**, và **GVCN của chính lớp đó** mới có thẩm quyền phân công hoặc hủy vai trò Lớp trưởng.
* **Huy hiệu ⭐ Lớp trưởng**: Hiển thị trang trọng trên thẻ thông tin lớp học và dòng danh sách học sinh trên cả giao diện Desktop và Mobile.
* **Đại diện khiếu nại vi phạm tập thể**:
  * Lớp trưởng được cấp quyền truy cập mục **Nền nếp** (`conduct`) để giám sát toàn bộ các bản ghi vi phạm của lớp mình.
  * Lớp trưởng có thẩm quyền thay mặt lớp gửi **yêu cầu giải trình / khiếu nại** (`appeal`) đối với bất kỳ lỗi sai nào bị ghi nhận nhầm lẫn hoặc chưa khách quan về Đoàn trường để xác minh lại.

### 2.3. Quản lý Nề nếp & Ghi nhận Vi phạm Kỷ luật (Conduct Management)
* **Ghi nhận vi phạm siêu tốc**: Tối ưu trên thiết bị di động cho Đội Sao đỏ, Đoàn trường và Giáo viên; chọn nhanh khối, lớp, học sinh, mã quy định và đính kèm ảnh minh chứng.
* **Quy trình thẩm định 5 bước chuẩn hóa**:
  1. `PENDING` (*Chờ xác minh*) – Vi phạm mới tạo, chưa trừ điểm thi đua.
  2. `VERIFIED` (*Đã xác minh*) – Đoàn trường duyệt bằng chứng, áp dụng trừ điểm.
  3. `APPEALING` (*Đang khiếu nại*) – Học sinh, Lớp trưởng hoặc GVCN gửi giải trình.
  4. `ADJUSTED` (*Đã điều chỉnh/Hoàn tác*) – Đoàn trường duyệt khiếu nại, phục hồi điểm.
  5. `DISMISSED` (*Bác bỏ/Không đủ căn cứ*) – Hủy bản ghi vi phạm không chính xác.
* **Quy tắc tính điểm minh bạch**: Chỉ những bản ghi vi phạm ở trạng thái `VERIFIED` mới tác động trừ điểm thi đua của Chi đoàn.

### 2.4. Thi đua Chi đoàn Tự động (Competition & Scoring)
* **Biểu điểm công bằng & khách quan**: Điểm tuần khởi điểm 100 điểm, tự động trừ theo lỗi vi phạm đã duyệt và cộng điểm phong trào Đoàn (văn nghệ, thể thao, hoa điểm mười...).
* **Bảng xếp hạng trực quan**: Bục vinh danh Podium Top 3, danh sách xếp hạng tuần/tháng/học kỳ tự động cập nhật thời gian thực.
* **Chốt sổ kỳ thi đua**: Tính năng khóa kỳ thi đua giúp cố định kết quả khen thưởng, ngăn ngừa sai lệch số liệu sau khi công bố.
* **Xuất báo cáo văn bản**: Xuất bảng điểm và xếp hạng ra file Excel (`.xlsx`) và PDF (`.pdf`) theo đúng chuẩn văn bản biểu mẫu giáo dục.

### 2.5. Góc sẻ chia – Tư vấn Tâm lý Học đường (Counseling & Support)
* **Bảo mật & Cách ly dữ liệu cấp cao**: Phân hệ hoạt động độc lập, cách ly dữ liệu khỏi các bảng xếp hạng thi đua; chỉ chuyên viên tư vấn tâm lý được cấp quyền mới có thể truy cập.
* **Gửi tâm sự ẩn danh / định danh**: Học sinh có thể gửi khúc mắc tâm lý, áp lực học tập hoặc bạo lực học đường kèm bí danh.
* **Mã tra cứu bí mật**: Mỗi lượt tâm sự sinh một mã định danh ngẫu nhiên (VD: `GSC-2026-X8F9`) để học sinh tự tra cứu phản hồi từ thầy cô mà không lo lộ danh tính.
* **Cảnh báo an toàn khẩn cấp**: Tích hợp đường dây nóng Tổng đài Quốc gia Bảo vệ Trẻ em **111** và chỉ dẫn hỗ trợ tại chỗ khi học sinh gặp nguy cơ.

### 2.6. Xác thực, Đăng ký & Hoàn thiện Hồ sơ (Authentication & Onboarding)
* **Đăng nhập Google OAuth 2.0 (SSO)**: Đăng nhập 1 chạm nhanh chóng qua tài khoản Google.
* **Hoàn thiện hồ sơ (`/complete-profile`)**: Dành cho học sinh mới, hỗ trợ chọn Khối, Lớp, Mã học sinh và gửi thông tin về Đoàn trường.
* **Quy trình duyệt tài khoản tự động**: Tự động nhận diện và bỏ qua bước hoàn thiện hồ sơ nếu tài khoản đã được kích hoạt và phê duyệt.

### 2.7. Thông báo Đa kênh (Email SMTP & SMS)
* **Email tự động**: Gửi email cảnh báo vi phạm tới hòm thư của GVCN và Đoàn trường qua Gmail SMTP với hàng đợi nền transactional outbox bền vững.
* **Tích hợp SpeedSMS API**: Tự động gửi SMS cảnh báo đến số điện thoại phụ huynh hoặc GVCN khi phát sinh vi phạm nghiêm trọng.

---

## 🏗️ 3. KIẾN TRÚC CÔNG NGHỆ (TECH STACK)

| Thành phần | Công nghệ sử dụng |
| :--- | :--- |
| **Backend Framework** | Python 3.12, Django 5.x / 6.x, Django REST Framework (DRF) |
| **Frontend Architecture**| Responsive SPA, HTML5, Vanilla ES6+ JavaScript, Tailwind CSS |
| **UI Components & Icons**| Lucide Icons, Chart.js, Modal Dialogs & Toasts Design System |
| **Cơ sở dữ liệu** | SQLite (môi trường Dev/Test), PostgreSQL (môi trường Production) |
| **Cache & Session** | In-memory cache / Redis cache utils |
| **Báo cáo & Tệp tin** | OpenPyXL (Excel Generator), ReportLab (PDF Engine) |
| **Bảo mật & Tunnel** | Cloudflare Edge Tunnel (`cloudflared`), HTTPS SSL/TLS |
| **Kiểm thử tự động** | Django Test Framework, APIRequestFactory, Custom Test Suites |

---

## 🛡️ 4. MA TRẬN PHÂN QUYỀN NGƯỜI DÙNG (RBAC MATRIX)

| Chức năng / Phân hệ | Quản trị viên (Admin) | Ban Giám hiệu (BGH) | Đoàn trường | GVCN | GVBM | Lớp trưởng | Học sinh | Chuyên viên Tâm lý |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Quản trị người dùng & Phê duyệt** | ✅ Toàn quyền | 👁️ Xem | ✅ Duyệt HS | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Phân công Lớp trưởng** | ✅ Có quyền | ✅ Có quyền | ✅ Có quyền | ✅ Lớp mình | ❌ | ❌ | ❌ | ❌ |
| **Phân công GVCN & GVBM** | ✅ Có quyền | ✅ Có quyền | ✅ Có quyền | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Nhận xét học sinh** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Xem hồ sơ học sinh lớp** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ (Chỉ mình) | ❌ |
| **Xác minh vi phạm & Trừ điểm** | ✅ | 👁️ Xem | ✅ Toàn quyền | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Khiếu nại / Giải trình vi phạm** | ✅ | ❌ | ❌ | ✅ Lớp mình | ❌ | ✅ Lớp mình | ✅ Lỗi mình | ❌ |
| **Chốt kỳ thi đua Chi đoàn** | ✅ | ✅ Phê duyệt | ✅ Chốt sổ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Xuất báo cáo Excel / PDF** | ✅ | ✅ | ✅ | ✅ Lớp mình | ❌ | ❌ | ❌ | ❌ |
| **Tư vấn tâm lý "Góc sẻ chia"** | ❌ (Cách ly) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Gửi ẩn danh | ✅ Toàn quyền |

---

## 🚀 5. HƯỚNG DẪN CÀI ĐẶT VÀ KHỞI CHẠY CỤC BỘ

### 5.1. Yêu cầu môi trường
* **Python**: Phiên bản `3.11` hoặc `3.12` (khuyến nghị `3.12`).
* **Git**: Phiên bản 2.x trở lên.

### 5.2. Các bước cài đặt
```bash
# 1. Clone mã nguồn từ GitHub
git clone https://github.com/cuonghk1108/THPTHK.git
cd THPTHK

# 2. Khởi tạo môi trường ảo Python
python -m venv .venv

# 3. Kích hoạt môi trường ảo
# Trên Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Trên Linux/macOS:
source .venv/bin/activate

# 4. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# 5. Cấu hình biến môi trường
# Tạo file .env từ file mẫu
copy .env.example .env
```

### 5.3. Khởi tạo Cơ sở dữ liệu & Chạy máy chủ
```bash
# Chạy migration database
python manage.py migrate

# Khởi tạo danh sách lớp học và tài khoản mẫu (nếu dùng dữ liệu mẫu)
python manage.py seed_hk_data

# Thu thập tệp tĩnh
python manage.py collectstatic --noinput

# Khởi chạy server phát triển
python manage.py runserver 127.0.0.1:8000
```
Truy cập ứng dụng tại: **`http://127.0.0.1:8000`**

---

## 🧪 6. KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST SUITES)

Dự án tích hợp sẵn các bộ kiểm thử tự động toàn diện kiểm tra tính đúng đắn và bảo mật:

```bash
# 1. Kiểm thử quy trình phân quyền và khiếu nại của Lớp trưởng
python scripts/test_lop_truong_workflow.py

# 2. Kiểm thử bảo vệ phạm vi dữ liệu và phân quyền của Học sinh
python scripts/test_student_role_scope.py

# 3. Kiểm thử phân công giáo viên và sổ tay nhận xét học sinh
python manage.py test conduct.test_teacher_classes_and_feedback

# 4. Kiểm thử biểu điểm thi đua và xuất báo cáo tự nhiên
python scripts/test_competition_export_order.py

# 5. Kiểm thử toàn bộ hệ thống
python manage.py test
```

---

## 🌐 7. TRIỂN KHAI PRODUCTION QUA CLOUDFLARE EDGE TUNNEL

Hệ thống được thiết kế sẵn sàng kết nối qua **Cloudflare Tunnel** để phát hành ra Internet với tên miền chính thức mà không cần mở port modem hoặc thuê IP tĩnh:

1. Chạy file batch khởi động một chạm:
   ```cmd
   start_cloudflare_tunnel.bat
   ```
2. Cấu hình DNS Cloudflare trỏ CNAME về UUID của Tunnel.
3. Ứng dụng tự động hoạt động bảo mật với chứng chỉ SSL/TLS miễn phí từ Cloudflare Edge.

---

## 🔒 8. BẢO MẬT & BẢN QUYỀN

* **Bảo mật Secret Keys**: Toàn bộ khóa bảo mật (SECRET_KEY, Google OAuth Client Secret, Mật khẩu ứng dụng Gmail SMTP, SpeedSMS Token) được quản lý qua biến môi trường (`.env`), không commit lên GitHub.
* **Chống giả mạo & Tấn công**: Tích hợp sẵn CSRF Protection, XSS Filter, SQL Parameterization của Django ORM và Rate Limiting đối với các API xác thực.
* **Bản quyền**: Bản quyền thuộc về **Trường THPT Hương Khê – Hà Tĩnh**. Nghiêm cấm sao chép hoặc phân phối lại cho mục đích thương mại khi chưa có sự đồng ý của đơn vị chủ quản.

---
*Ghi chú: Mọi thắc mắc hoặc yêu cầu hỗ trợ kỹ thuật, vui lòng liên hệ Ban Quản trị Hệ thống CNTT – Trường THPT Hương Khê.*
