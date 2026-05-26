from django.db import models
from django.conf import settings
from django.utils import timezone


class LoginAttempt(models.Model):
    """
    Tracks failed login attempts per identifier (email/phone) 
    to enforce temporary lockout after 3 failed attempts.
    """
    identifier = models.CharField(
        max_length=255, 
        db_index=True,
        help_text="Normalized email or phone number (lowercase)"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the login attempt"
    )
    failed_attempts = models.PositiveIntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    locked_until = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name_plural = "Login Attempts"
        ordering = ['-last_attempt']
        indexes = [
            models.Index(fields=['identifier', 'locked_until']),
            models.Index(fields=['last_attempt']),
        ]

    def __str__(self):
        status = "🔒 LOCKED" if self.is_locked else "✅ Active"
        return f"{self.identifier} | {self.failed_attempts} fails | {status}"

    @property
    def is_locked(self):
        """Check if account is currently locked."""
        if not self.locked_until:
            return False
        return self.locked_until > timezone.now()

    @property
    def lock_remaining_minutes(self):
        """Return remaining lock time in minutes, or 0 if not locked."""
        if not self.is_locked:
            return 0
        delta = self.locked_until - timezone.now()
        return max(0, int(delta.total_seconds() // 60))

    @classmethod
    def record_failure(cls, identifier: str, ip_address: str = None):
        """
        Record a failed login attempt and apply lockout if threshold reached.
        Lockout: 3 failed attempts = 15 minute lock.
        """
        normalized_id = identifier.lower().strip()
        
        attempt, created = cls.objects.get_or_create(
            identifier=normalized_id,
            defaults={'ip_address': ip_address}
        )
        
        attempt.failed_attempts += 1
        attempt.last_attempt = timezone.now()
        
        # Apply lockout after 3 failed attempts
        if attempt.failed_attempts >= 3:
            attempt.locked_until = timezone.now() + timezone.timedelta(minutes=15)
        
        attempt.save()
        return attempt

    @classmethod
    def check_lockout(cls, identifier: str):
        """
        Check if identifier is locked.
        Returns: (is_locked: bool, message: str or None)
        """
        normalized_id = identifier.lower().strip()
        
        try:
            attempt = cls.objects.get(identifier=normalized_id)
            
            # Check if currently locked
            if attempt.is_locked:
                remaining = attempt.lock_remaining_minutes
                return True, f"Too many failed attempts. Account locked. Try again in {remaining} minute{'s' if remaining != 1 else ''}."
            
            # Auto-reset if lock expired
            if attempt.locked_until and not attempt.is_locked:
                attempt.failed_attempts = 0
                attempt.locked_until = None
                attempt.save()
                
            return False, None
            
        except cls.DoesNotExist:
            return False, None

    @classmethod
    def reset_attempts(cls, identifier: str):
        """Clear failed attempts after successful login."""
        normalized_id = identifier.lower().strip()
        cls.objects.filter(identifier=normalized_id).delete()

    @classmethod
    def cleanup_expired(cls):
        """
        Optional: Call periodically to clean old records.
        Example: Add to a management command or Celery task.
        """
        # Delete records older than 7 days that aren't locked
        cls.objects.filter(
            last_attempt__lt=timezone.now() - timezone.timedelta(days=7),
            locked_until__isnull=True
        ).delete()