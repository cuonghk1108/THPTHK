from django.contrib import admin

# Register your models here.
from .models import ScoreAdjustment


@admin.register(ScoreAdjustment)
class ScoreAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'school_class', 'competition_period', 'amount', 'status', 'created_by', 'approved_by', 'created_at')
    list_filter = ('status', 'competition_period__academic_year', 'competition_period__period_type')
    search_fields = ('school_class__name', 'reason', 'created_by__username', 'approved_by__username')
    readonly_fields = ('idempotency_key', 'competition_period', 'school_class', 'amount', 'reason', 'status', 'created_by', 'approved_by', 'created_at', 'approved_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
