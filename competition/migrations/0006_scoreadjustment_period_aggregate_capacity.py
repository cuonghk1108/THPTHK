import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def preserve_existing_bonuses(apps, schema_editor):
    Score = apps.get_model('competition', 'ClassCompetitionScore')
    Score.objects.all().update(legacy_bonus_points=models.F('bonus_points'))


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0005_classcompetitionscore_idx_score_period_rank_and_more'),
        ('conduct', '0016_redstarassignment_redstarreport'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='competitionperiod',
            name='internal_month_number',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Tháng thi đua nội bộ'),
        ),
        migrations.AddConstraint(
            model_name='competitionperiod',
            constraint=models.UniqueConstraint(condition=models.Q(('internal_month_number__isnull', False), ('period_type', 'MONTH')), fields=('academic_year', 'internal_month_number'), name='uniq_internal_comp_month'),
        ),
        migrations.AddField(
            model_name='classcompetitionscore',
            name='legacy_bonus_points',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=9, verbose_name='Điểm cộng đã lưu trước khi chuẩn hóa'),
        ),
        migrations.RunPython(preserve_existing_bonuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='classcompetitionscore',
            name='base_points',
            field=models.DecimalField(decimal_places=2, default=100.0, max_digits=9, verbose_name='Điểm khởi điểm'),
        ),
        migrations.AlterField(
            model_name='classcompetitionscore',
            name='bonus_points',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=9, verbose_name='Điểm cộng phong trào Đoàn'),
        ),
        migrations.AlterField(
            model_name='classcompetitionscore',
            name='penalty_points',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=9, verbose_name='Điểm trừ vi phạm (đã xác minh)'),
        ),
        migrations.AlterField(
            model_name='classcompetitionscore',
            name='total_score',
            field=models.DecimalField(decimal_places=2, default=100.0, max_digits=9, verbose_name='Tổng điểm thi đua'),
        ),
        migrations.CreateModel(
            name='ScoreAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idempotency_key', models.UUIDField(blank=True, default=None, null=True, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Điểm điều chỉnh (+/-)')),
                ('reason', models.TextField(verbose_name='Lý do điều chỉnh')),
                ('status', models.CharField(choices=[('PENDING', 'Chờ phê duyệt'), ('APPROVED', 'Đã phê duyệt'), ('REJECTED', 'Từ chối')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_score_adjustments', to=settings.AUTH_USER_MODEL, verbose_name='Người phê duyệt')),
                ('competition_period', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='adjustments', to='competition.competitionperiod', verbose_name='Tuần thi đua')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_score_adjustments', to=settings.AUTH_USER_MODEL, verbose_name='Người ghi nhận')),
                ('school_class', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='score_adjustments', to='conduct.schoolclass', verbose_name='Lớp')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['competition_period', 'school_class', 'status'], name='idx_adjustment_scope_status')],
                'constraints': [models.CheckConstraint(condition=models.Q(('amount', 0), _negated=True), name='score_adjustment_nonzero')],
            },
        ),
    ]
