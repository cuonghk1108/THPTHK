import openpyxl
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook(r'C:\Users\Xuan Cuong\.gemini\antigravity\brain\5a5dcb7f-ba1d-4f8d-8a94-94f428cd0bbe\.user_uploaded\media_1792913340467_98df7079.xlsx')
ws = wb.active

rows = []
for r in ws.iter_rows(values_only=True):
    if any(r):
        rows.append(list(r))

print("Total non-empty rows:", len(rows))
for idx, r in enumerate(rows):
    print(f"{idx}: {r}")
