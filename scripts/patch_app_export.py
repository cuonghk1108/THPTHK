import sys

p = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

target = "const pid = periodId || selectedPeriodId || (typeof currentPeriod !== 'undefined' && currentPeriod?.id);"
replacement = "const selectEl = document.getElementById('comp-filter-period');\n  const pid = periodId || (selectEl && selectEl.value ? selectEl.value : null) || selectedPeriodId || (typeof currentPeriod !== 'undefined' && currentPeriod?.id);"

occurrences = content.count(target)
print(f"Target found {occurrences} times.")
if occurrences > 0:
    content = content.replace(target, replacement)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced successfully!")
