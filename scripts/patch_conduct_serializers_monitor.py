import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

path = r'conduct/serializers.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. SchoolClassSerializer
sc_pattern = r'class SchoolClassSerializer\(serializers\.ModelSerializer\):.*?(?=class StudentSerializer)'
new_sc = """class SchoolClassSerializer(serializers.ModelSerializer):
    homeroom_teacher_name = serializers.CharField(source='homeroom_teacher.full_name', read_only=True, default='')
    monitor_name = serializers.CharField(source='monitor.full_name', read_only=True, default='')

    class Meta:
        model = SchoolClass
        fields = ['id', 'name', 'grade', 'academic_year', 'homeroom_teacher', 'homeroom_teacher_name',
                  'student_count', 'room_number', 'union_branch_name', 'monitor', 'monitor_name']


"""
assert re.search(sc_pattern, text, flags=re.DOTALL), "sc_pattern not found"
text = re.sub(sc_pattern, new_sc, text, flags=re.DOTALL)
print("Updated SchoolClassSerializer.")

# 2. StudentSerializer
stu_pattern = r'class StudentSerializer\(serializers\.ModelSerializer\):.*?(?=class ConductRuleCategorySerializer)'
new_stu = """class StudentSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'student_code', 'full_name', 'date_of_birth', 'gender', 'school_class',
                  'class_name', 'is_union_member', 'is_red_star', 'is_class_monitor', 'status']


"""
assert re.search(stu_pattern, text, flags=re.DOTALL), "stu_pattern not found"
text = re.sub(stu_pattern, new_stu, text, flags=re.DOTALL)
print("Updated StudentSerializer.")

# 3. ViolationRecordSerializer
if "class_id = serializers.IntegerField(source='school_class_id'" not in text:
    old_v = "class_name = serializers.CharField(source='school_class.name', read_only=True)"
    new_v = "class_name = serializers.CharField(source='school_class.name', read_only=True)\n    class_id = serializers.IntegerField(source='school_class_id', read_only=True)"
    text = text.replace(old_v, new_v, 1)

    old_vf = "'id', 'record_code', 'school_class', 'class_name',"
    new_vf = "'id', 'record_code', 'school_class', 'class_name', 'class_id',"
    text = text.replace(old_vf, new_vf, 1)
    print("Updated ViolationRecordSerializer.")

# 4. TeacherAssignedClassSerializer
ta_pattern = r'class TeacherAssignedClassSerializer\(serializers\.Serializer\):.*'
new_ta = """class TeacherAssignedClassSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    grade = serializers.IntegerField()
    academic_year_name = serializers.CharField()
    student_count = serializers.IntegerField()
    assignment_role = serializers.CharField()
    assignment_role_display = serializers.CharField()
    subjects = serializers.ListField(child=serializers.CharField())
    homeroom_teacher_name = serializers.CharField()
    homeroom_teacher_id = serializers.IntegerField(allow_null=True, required=False)
    monitor_id = serializers.IntegerField(allow_null=True, required=False)
    monitor_name = serializers.CharField(allow_null=True, required=False)
    can_assign_monitor = serializers.BooleanField(default=False, required=False)
"""
assert re.search(ta_pattern, text, flags=re.DOTALL), "ta_pattern not found"
text = re.sub(ta_pattern, new_ta, text, flags=re.DOTALL)
print("Updated TeacherAssignedClassSerializer.")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("conduct/serializers.py successfully updated.")
