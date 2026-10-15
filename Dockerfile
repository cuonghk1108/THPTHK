FROM python:3.12-slim

# Thiết lập môi trường không ghi file bytecode và xuất log ngay lập tức
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt thư viện hệ thống cần thiết cho Pillow, ReportLab và PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt dependencies python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Sao chép mã nguồn dự án
COPY . /app/

# Thu gom tệp tĩnh
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Chạy với máy chủ Gunicorn chuẩn production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "hk_hub_project.wsgi:application"]
