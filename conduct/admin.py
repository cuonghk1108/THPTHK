from django.contrib import admin

from .models import ViolationEmailNotification


@admin.register(ViolationEmailNotification)
class ViolationEmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'violation', 'recipient_user', 'recipient_email', 'status', 'attempt_count', 'next_attempt_at', 'sent_at')
    list_filter = ('status', 'is_test')
    search_fields = ('recipient_email', 'subject', 'violation__record_code')
    readonly_fields = tuple(field.name for field in ViolationEmailNotification._meta.fields)

    def has_module_permission(self, request):
        return request.user.is_admin

    def has_view_permission(self, request, obj=None):
        return request.user.is_admin

    def has_change_permission(self, request, obj=None):
        return False

