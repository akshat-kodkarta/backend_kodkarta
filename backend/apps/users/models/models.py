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
    Organization model for multi-tenant functionality.
    """
    ORG_TYPE_CHOICES = [
        ("enterprise", "Enterprise"),
        ("smb", "Small/Medium Business"),
        ("startup", "Startup"),
        ("partner", "Partner Organization"),
        ("education", "Educational Institution"),
        ("government", "Government"),
        ("nonprofit", "Non-profit")
    ]
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    org_type = models.CharField(max_length=20, choices=ORG_TYPE_CHOICES, default="enterprise")
    
    # B2B specific fields
    industry = models.CharField(max_length=100, blank=True)
    size_range = models.CharField(max_length=50, blank=True, help_text="Organization size range (e.g., '1-10', '11-50', etc.)")
    billing_email = models.EmailField(blank=True)
    account_manager = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_organizations")
    
    # Subscription and billing
    subscription_plan = models.CharField(max_length=50, default="free")
    subscription_status = models.CharField(max_length=20, default="active")
    max_users = models.IntegerField(default=5)
    
    # Contact information
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    primary_contact = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_contact_for")
    
    # Settings and preferences
    settings = models.JSONField(default=dict, blank=True)
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

    # Basic user information
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Account type and segment
    USER_TYPE_CHOICES = [
        ("business", "Business User"),
        ("consumer", "Consumer User"),
        ("partner", "Partner"),
        ("admin", "Administrator")
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default="consumer")
    
    # B2B specific fields
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    
    # B2C specific fields
    preferences = models.JSONField(default=dict, blank=True, help_text="User preferences for personalization")
    subscription_tier = models.CharField(max_length=50, blank=True, default="free")
    
    # Common fields
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    auth_providers = models.JSONField(default=list, blank=True, help_text="List of auth providers used by this user")
    
    # Analytics and engagement
    last_login = models.DateTimeField(null=True, blank=True)
    login_count = models.IntegerField(default=0)
    onboarding_completed = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return self.name.strip() if self.name else self.email

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def is_business_user(self):
        """Check if this is a business user"""
        return self.user_type == "business" and self.organization is not None

    def is_consumer_user(self):
        """Check if this is a consumer user"""
        return self.user_type == "consumer"

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

    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['organization', 'user_type']),
        ]

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

class Team(models.Model):
    """
    Teams within organizations for B2B functionality.
    Enables group-based access control and collaboration.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="teams")
    members = models.ManyToManyField(User, related_name="teams")
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="led_teams")
    is_default = models.BooleanField(default=False, help_text="Whether new members are automatically added")
    permissions = models.JSONField(default=dict, blank=True, help_text="Team-specific permissions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    class Meta:
        ordering = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization']),
        ]


class SubscriptionPlan(models.Model):
    """
    Subscription plans for B2B and B2C users.
    Defines pricing, features, and limits for different user segments.
    """
    PLAN_TYPE_CHOICES = [
        ("business", "Business Plan"),
        ("consumer", "Consumer Plan"),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annual", "Annual"),
        ("custom", "Custom"),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True, help_text="Whether the plan is publicly visible")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default="monthly")
    features = models.JSONField(help_text="Features included in this plan")
    limits = models.JSONField(help_text="Usage limits for this plan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.plan_type})"
    
    class Meta:
        ordering = ['plan_type', 'price']
        indexes = [
            models.Index(fields=['plan_type', 'is_active']),
        ]


class UserSubscription(models.Model):
    """
    User or organization subscription records.
    Tracks subscription status, billing, and plan details.
    """
    STATUS_CHOICES = [
        ("active", "Active"),
        ("trialing", "Trial Period"),
        ("past_due", "Past Due"),
        ("canceled", "Canceled"),
        ("unpaid", "Unpaid"),
        ("paused", "Paused"),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="subscriptions")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscribers")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    billing_cycle_anchor = models.DateTimeField(help_text="Next billing date")
    payment_provider = models.CharField(max_length=50, blank=True)
    payment_provider_id = models.CharField(max_length=255, blank=True, help_text="ID in payment provider system")
    is_auto_renew = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        subscriber = self.organization.name if self.organization else self.user.email
        return f"{subscriber} - {self.plan.name}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['organization']),
            models.Index(fields=['status']),
        ]


class UserFeedback(models.Model):
    """
    User feedback for product improvement.
    Collects feedback from both B2B and B2C users.
    """
    FEEDBACK_TYPE_CHOICES = [
        ("bug", "Bug Report"),
        ("feature", "Feature Request"),
        ("usability", "Usability Issue"),
        ("general", "General Feedback"),
        ("nps", "NPS Rating"),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="feedback")
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    content = models.TextField()
    rating = models.IntegerField(null=True, blank=True, help_text="Rating on a scale (e.g., 1-10)")
    page_url = models.CharField(max_length=255, blank=True, help_text="URL where feedback was given")
    user_agent = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="resolved_feedback")
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_feedback_type_display()} from {self.user.email if self.user else 'Anonymous'}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "User feedback"
