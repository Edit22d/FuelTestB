from django.core.management.base import BaseCommand
from authentication.models import LoginAttempt

class Command(BaseCommand):
    help = 'Clean up expired login attempt records'

    def handle(self, *args, **options):
        deleted, _ = LoginAttempt.cleanup_expired()
        self.stdout.write(
            self.style.SUCCESS(f'✅ Cleaned up {deleted} expired login attempt records')
        )