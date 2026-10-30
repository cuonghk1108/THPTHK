import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's inspect the target block in review()
target_start = "                # Đồng bộ hồ sơ Teacher / Student nếu chưa có"
idx = content.find(target_start)
assert idx != -1, "Target start not found in core/views.py"

end_marker = "                Notification.objects.create(\n                    recipient=target_user,"
idx_end = content.find(end_marker, idx)
assert idx_end != -1, "End marker not found in core/views.py"

print("Target block found between", idx, "and", idx_end)
print("Preview of target block:\n", content[idx:idx+400])
