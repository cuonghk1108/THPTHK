import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from conduct.email import recover_interrupted_violation_emails, send_violation_email
from conduct.models import ViolationEmailNotification


class Command(BaseCommand):
    help = 'Process pending violation email notifications from the database outbox.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true', help='Run continuously as a background worker.')
        parser.add_argument('--poll-interval', type=float, default=2.0, help='Seconds to wait between queue scans.')
        parser.add_argument('--batch-size', type=int, default=50, help='Maximum notifications processed per scan.')

    def handle(self, *args, **options):
        while True:
            recovered = recover_interrupted_violation_emails()
            if recovered:
                self.stdout.write(self.style.WARNING(
                    f'{recovered} email sends were interrupted and require administrator review.'
                ))

            now = timezone.now()
            notification_ids = list(
                ViolationEmailNotification.objects.filter(
                    status=ViolationEmailNotification.STATUS_PENDING,
                    next_attempt_at__lte=now,
                ).order_by('next_attempt_at', 'created_at').values_list('id', flat=True)[:options['batch_size']]
            )
            for notification_id in notification_ids:
                if send_violation_email(notification_id):
                    self.stdout.write(f'Email notification {notification_id}: SMTP accepted.')

            if not options['loop']:
                break
            if not notification_ids:
                time.sleep(max(0.25, options['poll_interval']))
