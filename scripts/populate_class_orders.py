# -*- coding: utf-8 -*-
import sys
import os
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.chdir(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from conduct.models import SchoolClass
from competition.models import CompetitionPeriod
from competition.services import recalculate_period_scores

classes = SchoolClass.objects.all()
updated_count = 0
for c in classes:
    m = re.match(r'^(\d+)[A-Za-zĐđ]+(\d+)$', c.name.strip())
    if m:
        c.class_order = int(m.group(2))
    else:
        m2 = re.search(r'(\d+)$', c.name.strip())
        if m2:
            c.class_order = int(m2.group(1))
        else:
            c.class_order = 1
    c.save(update_fields=['class_order'])
    updated_count += 1

print(f"Updated class_order for {updated_count} classes in database.")

# Check the new DB default ordering
qs = SchoolClass.objects.filter(is_active=True)
print("\n--- NEW SYSTEM-WIDE DEFAULT ORDERING FROM DB ---")
for grade in [10, 11, 12]:
    names = list(qs.filter(grade=grade).values_list('name', flat=True))
    print(f"Khối {grade} ({len(names)} lớp):")
    print(", ".join(names))

# Recalculate scores for all periods so tie-breaker order reflects natural sort
periods = CompetitionPeriod.objects.all()
print(f"\nRecalculating scores for {periods.count()} periods...")
for p in periods:
    try:
        recalculate_period_scores(p, force=True)
    except Exception as e:
        print(f"Error recalculating period {p.id}: {e}")

print("All periods recalculated successfully!")
