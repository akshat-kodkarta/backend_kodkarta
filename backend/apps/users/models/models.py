from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from functools import cached_property
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password

from apps.users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    AUTH_PROVIDER_CHOICES = [
        ("google", "Google"),
        ("github", "Github"),
        ("email", "Email"),
    ]

    email = models.EmailField(unique=True)
    auth_provider = models.CharField(max_length=50, choices=AUTH_PROVIDER_CHOICES, default="email")
    auth_id = models.CharField(max_length=255, blank=True, null=True, help_text="External provider's user ID")
    password = models.CharField(max_length=255)

    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)

    is_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user account should be treated as active.'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into this admin site.'
    )
    is_superuser = models.BooleanField(default=False)

    meta = {"indexes": ["email", "auth_id"]}
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        # Optional: specify a custom table name if needed
        db_table = 'user'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @cached_property
    def is_authenticated(self):
        return True

    @cached_property
    def is_anonymous(self):
        return False

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def __repr__(self):
        return f"User(auth_id={self.auth_id!r}, email={self.email!r}, first_name={self.first_name!r}, last_name={self.last_name!r})"

