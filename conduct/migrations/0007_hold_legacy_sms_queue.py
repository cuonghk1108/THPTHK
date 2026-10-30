from django.db import migrations


def hold_legacy_queue(apps, schema_editor):
    SmsNotification = apps.get_model('conduct', 'SmsNotification')
    SmsNotification.objects.filter(status__in=['PENDING', 'SENDING']).update(
        status='FAILED',
        needs_admin_attention=True,
        last_error='Thông báo cũ được giữ lại khi nâng cấp; hãy kiểm tra trước khi thử gửi lại.',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('conduct', '0006_smsproviderstatusevent'),
    ]

    operations = [
        migrations.RunPython(hold_legacy_queue, migrations.RunPython.noop),
    ]
