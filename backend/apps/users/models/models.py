import binascii
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from functools import cached_property
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password
from functools import cached_property
from mongoengine import Document, fields
from django.contrib.auth.hashers import make_password, check_password
import binascii
import os
from datetime import timedelta, datetime
import logging
import pytz



logger = logging.getLogger(__name__)

UTC_PLUS_ONE = pytz.timezone('Europe/London')  # or 'Etc/GMT-1'
from apps.users.managers import UserManager


class Organization(models.Model):
    """
    Organization model for grouping users and resources
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Role(models.Model):
    """
    User roles with associated permissions
    """
    name = models.CharField(max_length=255)
    permissions = models.JSONField()
    
    def __str__(self):
        return self.name

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
    
    # Added fields from the duplicate User model
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

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

class Token(models.Model):
    """
    Authentication tokens for API access
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField()
    key = models.CharField(max_length=255, primary_key=True)
    expires = models.DateTimeField()
    refresh_token = models.CharField(max_length=255, unique=True)
    refresh_expires = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Token for {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.user:
            raise ValueError("User field cannot be None.")
        if not self.key:
            self.key = self.generate_key()
        if not self.refresh_token:
            self.refresh_token = self.generate_key()
        if not self.expires:
            self.expires = timezone.now() + timedelta(hours=1)
        if not self.refresh_expires:
            self.refresh_expires = timezone.now() + timedelta(days=30)
        # print(f"DEBUG: Saving token with expires: {self.expires}, refresh_expires: {self.refresh_expires}")
        return super(Token, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key

    def is_valid(self):
        now = timezone.now()
        if timezone.is_naive(self.expires):
            self.expires = timezone.make_aware(self.expires)
            self.save()
        # print(f"DEBUG: is_valid - now: {now}, expires: {self.expires}")
        return now < self.expires

    def is_refresh_valid(self):
        now = timezone.now()
        if timezone.is_naive(self.refresh_expires):
            self.refresh_expires = timezone.make_aware(self.refresh_expires)
            self.save()
        # print(f"DEBUG: is_refresh_valid - now: {now}, refresh_expires: {self.refresh_expires}")
        return now < self.refresh_expires

    def delete_existing_tokens(self):
        Token.objects(user=self.user).delete()

    def refresh(self):
        if not self.user:
            raise ValueError("User field cannot be None.")

        logger.info(f"Refreshing token for user: {self.user.auth_id}")

        user = self.user

        self.delete_existing_tokens()

        new_token = Token(user=user)
        new_token.key = self.generate_key()
        new_token.expires = timezone.now() + timedelta(hours=1)
        new_token.refresh_token = self.generate_key()
        new_token.refresh_expires = timezone.now() + timedelta(days=30)
        new_token.created = timezone.now()

        new_token.save()

        logger.info("Token successfully refreshed and saved")
        return new_token
    
    @classmethod
    def get_or_create(cls, user):
        token = cls.objects(user=user).first()
        # print(f"DEBUG: get_or_create - existing token: {token}")
        if token:
            print(f"DEBUG: existing token expires: {token.expires}, refresh_expires: {token.refresh_expires}")
        if token and token.is_valid():
            return token, False
        else:
            if token:
                token.delete()
            new_token = cls(user=user).save()
            # print(f"DEBUG: new token created with expires: {new_token.expires}, refresh_expires: {new_token.refresh_expires}")
            return new_token, True
