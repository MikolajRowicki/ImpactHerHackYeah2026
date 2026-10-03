from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower

from .. import clock
from ..constants import VOIVODESHIPS


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password, display_name, **extra):
        user = self.model(email=email.strip().lower(), display_name=display_name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """A person. The e-mail address is the login; the role belongs to a membership."""

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=60)
    # Inactive until the activation link is used (sign-up) or at once (legacy register).
    is_active = models.BooleanField(default=True)
    voivodeship = models.CharField(max_length=30, blank=True, default="")
    email_reminders = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=clock.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        constraints = [
            # Addresses are unique whatever the letter case, also for rows written around the app.
            models.UniqueConstraint(Lower("email"), name="user_email_unique_ci"),
            models.CheckConstraint(
                condition=models.Q(voivodeship="") | models.Q(voivodeship__in=VOIVODESHIPS),
                name="user_voivodeship_known",
            ),
        ]

    def __str__(self):
        return f"user {self.pk}"

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)
