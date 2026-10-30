import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\core\views.py', 'r', encoding='utf-8') as f:
    views = f.read()

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\core\serializers.py', 'r', encoding='utf-8') as f:
    ser = f.read()

pos_v = views.find('class ProfileAPIView')
print("=== ProfileAPIView in views.py ===")
print(views[pos_v:pos_v+2000])

pos_s = ser.find('class ProfileUpdateSerializer')
print("=== ProfileUpdateSerializer in serializers.py ===")
print(ser[pos_s:pos_s+2000])

pos_p = ser.find('class ProfileSerializer')
print("=== ProfileSerializer in serializers.py ===")
print(ser[pos_p:pos_p+1500])
