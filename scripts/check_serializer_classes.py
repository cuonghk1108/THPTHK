import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/serializers.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Check lines around UserSerializer
assert 'class UserSerializer(' in text
assert 'class ApprovalActionSerializer(' in text
print("Both classes found in core/serializers.py")
