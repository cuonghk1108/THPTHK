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

## 4. TÀI KHOẢN VÀ ĐỔI MẬT KHẨU

Không công khai tài khoản hoặc mật khẩu mẫu trong tài liệu hay giao diện đăng nhập. Admin tạo tài khoản mới trong mục quản lý người dùng; hệ thống sinh mật khẩu tạm thời và chỉ trả về một lần. Người dùng phải đổi mật khẩu ngay lần đăng nhập đầu tiên trước khi truy cập các chức năng khác.

Không sử dụng tài khoản demo mặc định trong môi trường production. Mật khẩu bootstrap do lệnh seed production-safe tạo ra chỉ xuất hiện trong đầu ra của lần chạy đó; hãy chuyển cho quản trị viên qua kênh bảo mật và đổi ngay khi đăng nhập.

---

## 4. HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY DỰ ÁN

### 4.1. Chạy trên máy tính (Cục bộ)
Tạo file cấu hình riêng từ mẫu (lệnh không ghi đè file đã có), rồi điền mật khẩu ứng dụng Gmail và thông tin SpeedSMS vào file đó. Django tự đọc `.env.local` hoặc `.env`; không đưa mật khẩu ứng dụng hoặc token thật lên Git:
```powershell
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
```

### Cấu hình Gmail gửi email

Hệ thống gửi email khôi phục mật khẩu và cảnh báo vi phạm qua Gmail SMTP (cổng 587/STARTTLS). Bật Xác minh 2 bước cho tài khoản Google, tạo **Mật khẩu ứng dụng** trong mục Bảo mật, rồi điền `GMAIL_SENDER_EMAIL` và `GMAIL_APP_PASSWORD` trong `.env.local` (hoặc `.env` khi chạy Docker). Không dùng mật khẩu đăng nhập Gmail và không commit mật khẩu ứng dụng.

Các biến cần thiết:

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_TIMEOUT=10
GMAIL_SENDER_EMAIL=<địa chỉ Gmail gửi>
GMAIL_APP_PASSWORD=<Mật khẩu ứng dụng Gmail>
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
SCHOOL_UNION_NOTIFICATION_EMAIL=<địa chỉ Gmail Đoàn trường>
FRONTEND_BASE_URL=https://<tên-miền>
```

`GMAIL_SENDER_EMAIL` và `GMAIL_APP_PASSWORD` được dùng làm cấu hình nguồn; `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` là các tên tương thích với cấu hình Django hiện tại và chỉ cần đặt nếu muốn ghi đè chúng. `DEFAULT_FROM_EMAIL` mặc định dùng địa chỉ Gmail gửi. Email cảnh báo được đưa vào transactional outbox và worker gửi lại khi SMTP tạm lỗi; `SCHOOL_UNION_NOTIFICATION_EMAIL` là địa chỉ **nhận** cảnh báo (cũng có thể cấu hình qua trang quản trị). Trên môi trường triển khai như Vercel, khai báo secrets SMTP trong Environment Variables của dự án và chạy worker email bền vững cùng cơ sở dữ liệu dùng chung; không chạy worker trên filesystem SQLite tạm của serverless. Không gửi mật khẩu ứng dụng qua chat hoặc lưu trong Git.

Nếu tài khoản Google Workspace không cho phép App Password, hãy nhờ quản trị viên tổ chức cung cấp SMTP relay hoặc nhà cung cấp email được phê duyệt; không tìm cách vượt qua chính sách bảo mật.

Sau khi cấu hình, Admin đăng nhập và gọi `POST /api/conduct/email/test/` (có thể truyền `{"recipient_email":"..."}` để chọn hộp thư thử). Endpoint kiểm tra cấu hình rồi gửi thư thật; tối đa 5 lần trong 10 phút cho mỗi Admin. Lịch sử phân biệt `SMTP đã tiếp nhận` với việc thư thực sự vào Inbox, trạng thái này không thể xác nhận việc giao thư cuối cùng.

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

# 6. Ở cửa sổ terminal thứ nhất, chạy worker SMS
python manage.py process_sms_queue --loop
# Ở cửa sổ terminal thứ hai, chạy worker email
python manage.py process_email_queue --loop
```
Truy cập trình duyệt tại địa chỉ: `http://127.0.0.1:8000`

### 4.2. Chạy với Docker & Docker Compose
Docker Compose tự đọc file `.env`; nếu bạn đang cấu hình trong `.env.local`, hãy tạo `.env` một lần (không ghi đè file có sẵn):
```powershell
if (-not (Test-Path .env)) {
  if (Test-Path .env.local) { Copy-Item .env.local .env }
  else { Copy-Item .env.example .env }
}
```

```bash
# Khởi chạy máy chủ web, PostgreSQL và worker SMS/email nền
docker-compose up --build -d
```

### 4.3. Cấu hình SpeedSMS khi ghi nhận vi phạm

Tin vi phạm được ghi trước vào cơ sở dữ liệu; hàng đợi nền mới gửi SMS từ backend. Lỗi SpeedSMS không làm mất báo cáo. Khi gửi SMS tự động đang tắt, lịch sử ghi `SKIPPED`. Access Token chỉ được đọc từ biến môi trường trên máy chủ, không nhập vào giao diện quản trị và không được trả về trình duyệt.

Tạo Access Token tại [SpeedSMS Connect](https://connect.speedsms.vn), sau đó cấu hình các biến dưới đây cho cả tiến trình web và worker. Không commit token thật vào Git:

```text
SPEEDSMS_API_BASE_URL=https://api.speedsms.vn/index.php
SPEEDSMS_ACCESS_TOKEN=<Access Token thật>
SPEEDSMS_SMS_TYPE=<loại đã được tài khoản cấp quyền>
SPEEDSMS_SENDER=<sender đã đăng ký, nếu loại tin yêu cầu>
SPEEDSMS_RECIPIENT_PHONE=<số điện thoại Đoàn trường>
SPEEDSMS_WEBHOOK_SECRET=<chuỗi ngẫu nhiên dài, chỉ dùng trong URL webhook>
SPEEDSMS_ENABLED=false
SMS_REQUEST_TIMEOUT=10
```

Đăng nhập SpeedSMS để xác nhận loại tin và sender được phép dùng. Các loại được tài liệu API liệt kê gồm 2, 3, 4, 5 và 6; cấu hình hiện yêu cầu sender với loại 2, 3 và 5. Không tự chọn loại hoặc tên sender thay cho quản trị viên. Trang **Cấu hình SMS** cho phép Admin lưu số nhận, loại tin, sender, giới hạn gửi và số lần thử lại. Giá trị ở trang quản trị được ưu tiên; nếu để trống thì hệ thống dùng giá trị tương ứng trong môi trường máy chủ. Token có thể đổi bằng cách cập nhật biến môi trường và khởi động lại web/worker.

Quy trình bật an toàn: cấu hình token, loại tin, sender và số nhận; kiểm tra **Kết nối / số dư** trong trang quản trị; đặt `SPEEDSMS_ENABLED=true` trên máy chủ và chạy **Gửi tin thử** tới số nhận đã cấu hình; sau khi tin thử thành công, bật **Tự động gửi** trong trang quản trị. Lệnh gửi thử tạo một SMS thật và có thể tính phí. Worker nền phải đang chạy bằng `python manage.py process_sms_queue --loop`.

Backend gọi API qua HTTPS với HTTP Basic Authentication (`username` là Access Token, `password` là `x`). Gửi tin qua `POST /sms/send` bằng JSON (`to` là mảng số nhận, `content`, loại `sms_type` dạng số và `sender`). Phản hồi `status=success`, `code=00` lưu `data.tranId`, số tin và chi phí. Nút **Kiểm tra** dùng `GET /sms/status/{tranId}`; trạng thái API `1` chỉ được coi là đã gửi tới mạng, không phải xác nhận đã tới điện thoại. Chỉ Delivery Status Report hợp lệ mới đặt trạng thái `DELIVERED`. Nếu kết nối đứt trước khi backend nhận được `tranId`, giao dịch không tự gửi lại; Admin cần đối chiếu tài khoản SpeedSMS trước khi thử thủ công.

SpeedSMS chưa công bố chữ ký xác thực cho Delivery Status Report trong tài liệu API. Tạo một chuỗi ngẫu nhiên dài cho `SPEEDSMS_WEBHOOK_SECRET`, rồi khai báo trong SpeedSMS mục **Setting → Webhook** URL HTTPS chính xác dạng `https://<ten-mien>/api/webhooks/speedsms/delivery-report/<SPEEDSMS_WEBHOOK_SECRET>/`. Đây là URL mang bí mật chia sẻ, không phải chữ ký mật mã của SpeedSMS; endpoint từ chối URL sai, chỉ xử lý `type=report`, đối chiếu mã giao dịch và số nhận, khử lặp sự kiện, và chỉ cập nhật trạng thái SMS. Không dùng payload không xác thực làm bằng chứng giao hàng.

`ACCEPTED` nghĩa là SpeedSMS nhận yêu cầu gửi; chỉ `DELIVERED` mới xuất hiện khi webhook xác thực báo đã tới điện thoại. SpeedSMS dùng `status=0` cho chuyển thành công, `1–63` cho lỗi tạm thời và `>=64` cho lỗi cuối. Lỗi cấu hình, số dư không đủ, tham số và số điện thoại không hợp lệ không được tự thử vô hạn. Lỗi kết nối tạm thời được thử lại theo chính sách tăng dần; nếu phản hồi bị mất và chưa biết SpeedSMS đã nhận tin hay chưa, hệ thống không gửi lại tự động để tránh tính phí trùng và đánh dấu cần Admin kiểm tra.

Trang quản trị hiển thị lịch sử, số nhận đã che, mã giao dịch, số SMS, chi phí, trạng thái và lỗi đã làm sạch. Xem [tài liệu SMS API SpeedSMS](https://speedsms.vn/sms-api/) và [hướng dẫn dịch vụ SMS API](https://speedsms.vn/sms-api-service/).

### 4.4. Lệnh dữ liệu mẫu
- **Development/Preview (`DEBUG=True`)**: `python manage.py seed_hk_data` nạp bộ dữ liệu phục vụ phát triển.
- **Production (`DEBUG=False`)**: chỉ dùng `python manage.py seed_hk_data --production-safe` trên cơ sở dữ liệu trống. Lệnh từ chối chạy nếu đã có dữ liệu; bộ dữ liệu được ẩn danh, không có hồ sơ tư vấn hay nhật ký thao tác, các tài khoản mẫu bị vô hiệu hóa và chỉ tài khoản bootstrap admin được kích hoạt.
- `python manage.py seed_hk_data --clean` chỉ hoạt động khi `DEBUG=True`; lệnh bị chặn khi `DEBUG=False`.
- Production demo trên Vercel dùng riêng `sample_data/demo.sqlite3`; biến `DATABASE_URL` không được dùng trong chế độ này. Bộ dữ liệu gồm tài khoản demo và dữ liệu minh họa đã ẩn danh, không gồm hồ sơ tư vấn hay nhật ký thao tác.
- Trên Vercel, ứng dụng chỉ cho đăng nhập và xem dữ liệu mẫu. Mọi thao tác thay đổi dữ liệu bị chặn vì ổ đĩa của function không lưu bền vững hoặc chia sẻ giữa các instance.
- Tạo SQLite mẫu trên một file đích mới, trống bằng PowerShell:
  ```powershell
  $env:DB_NAME = 'sample_data/demo.sqlite3'
  python manage.py migrate
  python manage.py build_demo_dataset
  ```

Không đưa mật khẩu tạm thời hoặc dữ liệu cá nhân vào log, ticket hay kho mã nguồn.

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
