from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from functools import cached_property
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password

from apps.users.managers import UserManager
from apps.users.models.models import Organization, User

class ProductCatalog(models.Model):
    """
    Product catalog entry representing a monitored software product.
    Used to organize and categorize software assets for visibility and governance.
    """
    TYPE_CHOICES = [
        ("app", "Application"),
        ("web", "Web Service"),
        ("api", "API Service"),
        ("infrastructure", "Infrastructure"),
        ("data", "Data Service"),
        ("ai", "AI Model/Service")
    ]
    
    STATUS_CHOICES = [
        ("active", "Active"),
        ("deprecated", "Deprecated"),
        ("in_development", "In Development"),
        ("maintenance", "Maintenance")
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="app")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="products")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="children",
                             help_text="Parent product (for hierarchical organization)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_products")
    tags = models.JSONField(default=list, blank=True, 
                          help_text="List of tags for categorization and filtering")
    risk_level = models.CharField(max_length=20, default="medium", 
                                help_text="Risk level of the product")
    metadata = models.JSONField(default=dict, blank=True,
                              help_text="Additional metadata about the product")
    is_critical = models.BooleanField(default=False,
                                    help_text="Indicates if this is a business-critical product")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.type})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'type']),
            models.Index(fields=['name'])
        ]

