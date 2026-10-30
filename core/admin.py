from django.contrib import admin
from .models import User, AcademicYear, Semester, SystemSetting, AuditLog, ApprovalLog, Notification

admin.site.register(User)
admin.site.register(AcademicYear)
admin.site.register(Semester)
admin.site.register(SystemSetting)
admin.site.register(AuditLog)
admin.site.register(ApprovalLog)
admin.site.register(Notification)

