# -*- coding: utf-8 -*-
with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\test_teacher_classes_and_feedback.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("self.client.post('/api/conduct/student-feedback/'", "self.client.post('/api/conduct/feedbacks/'")

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\test_teacher_classes_and_feedback.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed post url!')
