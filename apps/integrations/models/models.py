from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from functools import cached_property
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password
from apps.users.models.models import Organization, User

from apps.users.managers import UserManager

class DataSource(models.Model):
    """
    External data sources for integrations with cloud platforms and code repositories.
    Stores connection details and metadata for scanning resources.
    """
    SOURCE_TYPE_CHOICES = [
        ("github", "GitHub"),
        ("gitlab", "GitLab"),
        ("azure", "Azure"),
        ("aws", "AWS"),
        ("gcp", "Google Cloud"),
        ("kubernetes", "Kubernetes"),
        ("bitbucket", "Bitbucket")
    ]
    
    CONNECTION_STATUS_CHOICES = [
        ("active", "Active"),
        ("failed", "Failed"),
        ("pending", "Pending Authorization"),
        ("disconnected", "Disconnected")
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    credentials = models.TextField(help_text="Encrypted credentials for the data source")
    credentials_metadata = models.JSONField(default=dict, blank=True, 
                                          help_text="Non-sensitive metadata about the credentials")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="data_sources")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_data_sources")
    connection_status = models.CharField(max_length=20, choices=CONNECTION_STATUS_CHOICES, default="pending")
    last_scan_at = models.DateTimeField(null=True, blank=True)
    scan_frequency = models.IntegerField(default=24, help_text="Scan frequency in hours")
    integration_data = models.JSONField(default=dict, blank=True,
                                      help_text="Additional integration-specific data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.type})"
    
    class Meta:
        db_table = 'data_source'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'type']),
            models.Index(fields=['connection_status'])
        ]
        verbose_name = 'Data Source'
        verbose_name_plural = 'Data Sources'

class CloudResource(models.Model):
    """
    Cloud resources discovered through integration with cloud platforms.
    """
    RESOURCE_TYPE_CHOICES = [
        ("compute", "Compute Resource"),
        ("storage", "Storage Resource"),
        ("database", "Database Resource"),
        ("network", "Network Resource"),
        ("serverless", "Serverless Function"),
        ("container", "Container Service"),
        ("ai", "AI Service"),
        ("security", "Security Service"),
        ("other", "Other")
    ]
    
    resource_id = models.CharField(max_length=255, help_text="Cloud provider's resource ID")
    name = models.CharField(max_length=255)
    cloud_provider = models.CharField(max_length=50, help_text="Name of the cloud provider")
    type = models.CharField(max_length=50, choices=RESOURCE_TYPE_CHOICES)
    specific_type = models.CharField(max_length=100, help_text="Provider-specific resource type")
    location = models.CharField(max_length=255, help_text="Region/zone of the resource")
    status = models.CharField(max_length=50, default="active")
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="cloud_resources")
    configuration = models.JSONField(default=dict, help_text="Resource configuration data")
    tags = models.JSONField(default=dict, blank=True, help_text="Resource tags")
    security_score = models.FloatField(null=True, blank=True, help_text="Security assessment score")
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.specific_type})"
    
    class Meta:
        db_table = 'cloud_resource'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['data_source', 'type']),
            models.Index(fields=['resource_id'])
        ]
        verbose_name = 'Cloud Resource'
        verbose_name_plural = 'Cloud Resources'

class GitRepository(models.Model):
    """
    Git repositories discovered through integration with Git providers.
    """
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
        ("internal", "Internal")
    ]
    
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=512, help_text="Full repository name with owner/org")
    url = models.URLField()
    clone_url = models.URLField()
    description = models.TextField(blank=True)
    default_branch = models.CharField(max_length=100, default="main")
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default="private")
    provider = models.CharField(max_length=50, help_text="Git provider (GitHub, GitLab, etc.)")
    owner = models.CharField(max_length=255, help_text="Repository owner/organization name")
    last_scanned_at = models.DateTimeField(null=True, blank=True)
    last_commit_at = models.DateTimeField(null=True, blank=True)
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="git_repositories")
    security_insights = models.JSONField(default=dict, blank=True, help_text="Security assessment data")
    repository_metadata = models.JSONField(default=dict, blank=True)
    has_security_issues = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        db_table = 'git_repository'
        verbose_name_plural = "Git repositories"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['data_source', 'provider']),
            models.Index(fields=['full_name'])
        ]
        verbose_name = 'Git Repository'

