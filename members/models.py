from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
import uuid
from django.conf import settings

class Member(AbstractUser):
    # Alias (renamed username)
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Alias"
    )

    email = models.EmailField(
        unique=True,
        verbose_name="Email Address"
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Full name as an alternative to first and last name"
    )

    email_verified = models.BooleanField(
        default=False,
        help_text="Designates whether the user's email has been verified"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def clean(self):
        super().clean()

        # Enforce case-insensitive uniqueness for alias
        if self.username:
            qs = Member.objects.filter(username__iexact=self.username)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"username": "This alias is already in use."})

    def get_full_name(self):
        if self.full_name:
            return self.full_name
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.full_name or self.username or self.email

    def __str__(self):
        return self.email



class EmailVerificationToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_token"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email verification for {self.user.email}"
