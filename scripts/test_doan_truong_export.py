import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from core.models import User
from competition.models import CompetitionPeriod
from reports.services import export_competition_excel, export_competition_pdf
import openpyxl
import io

doan_user = User.objects.filter(role=User.ROLE_DOAN_TRUONG).first()
print(f"Testing export with DOAN_TRUONG: {doan_user}")

p_week = CompetitionPeriod.objects.get(id=1)
excel_bytes = export_competition_excel(p_week.id, doan_user)
wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
ws = wb.active
rows = list(ws.iter_rows(values_only=True))

# Count data rows
class_names = [r[1] for r in rows if r and len(r) > 1 and r[1] and ('10A' in str(r[1]) or '11A' in str(r[1]) or '12A' in str(r[1]))]
print(f"Excel export for DOAN_TRUONG succeeded! Classes in export: {len(class_names)}")
print(f"First 5 classes: {class_names[:5]}")
print(f"Last 5 classes: {class_names[-5:]}")

pdf_bytes = export_competition_pdf(p_week.id, doan_user)
print(f"PDF export for DOAN_TRUONG succeeded! PDF size: {len(pdf_bytes)} bytes")

print("DOAN_TRUONG EXPORT TEST PASSED!")
