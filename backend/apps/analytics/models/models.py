from django.db import models
from apps.users.models.models import User, Organization
from apps.products.models.models import ProductCatalog

class UserActivity(models.Model):
    """
    User activity tracking for both B2B and B2C users.
    Records user actions and engagement for analytics.
    """
    ACTIVITY_TYPE_CHOICES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("page_view", "Page View"),
        ("feature_use", "Feature Use"),
        ("search", "Search"),
        ("download", "Download"),
        ("upload", "Upload"),
        ("setting_change", "Setting Change"),
        ("account_update", "Account Update"),
        ("purchase", "Purchase"),
        ("feedback", "Feedback"),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name="member_activities")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    page_url = models.CharField(max_length=512, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} at {self.occurred_at}"
    
    class Meta:
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['organization']),
            models.Index(fields=['occurred_at']),
        ]
        verbose_name_plural = "User activities"


class UserMetrics(models.Model):
    """
    Aggregated user metrics for both B2B and B2C users.
    Stores pre-calculated user engagement and activity metrics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="metrics")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    last_active_at = models.DateTimeField()
    active_days_last_week = models.IntegerField(default=0)
    active_days_last_month = models.IntegerField(default=0)
    total_logins = models.IntegerField(default=0)
    average_session_duration = models.IntegerField(default=0, help_text="In seconds")
    feature_usage_counts = models.JSONField(default=dict, help_text="Count of feature usage by type")
    engagement_score = models.FloatField(default=0.0, help_text="Calculated engagement score 0-100")
    value_score = models.FloatField(default=0.0, help_text="Calculated user value score 0-100")
    churn_risk = models.FloatField(default=0.0, help_text="Estimated churn risk 0-100%")
    avg_daily_activity = models.IntegerField(default=0)
    retention_metrics = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Metrics for {self.user.email}"
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = "User metrics"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['organization']),
        ]


class OrganizationMetrics(models.Model):
    """
    Aggregated organization metrics for B2B users.
    Tracks organization-level engagement and usage patterns.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="metrics")
    total_users = models.IntegerField(default=0)
    active_users_last_week = models.IntegerField(default=0)
    active_users_last_month = models.IntegerField(default=0)
    average_user_engagement = models.FloatField(default=0.0)
    total_activities = models.IntegerField(default=0)
    feature_usage_distribution = models.JSONField(default=dict)
    growth_metrics = models.JSONField(default=dict, blank=True)
    health_score = models.FloatField(default=0.0, help_text="Organization health score 0-100")
    expansion_opportunity = models.FloatField(default=0.0, help_text="Expansion opportunity score 0-100")
    churn_risk = models.FloatField(default=0.0, help_text="Estimated churn risk 0-100%")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Metrics for {self.organization.name}"
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = "Organization metrics"
        indexes = [
            models.Index(fields=['organization']),
        ]


class ProductUsageMetrics(models.Model):
    """
    Product usage metrics for both B2B and B2C users.
    Tracks usage patterns and engagement with specific products.
    """
    PERIOD_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
    ]
    
    product = models.ForeignKey(ProductCatalog, on_delete=models.CASCADE, related_name="usage_metrics")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name="product_usage")
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    active_users = models.IntegerField(default=0)
    total_activities = models.IntegerField(default=0)
    usage_minutes = models.IntegerField(default=0)
    feature_usage = models.JSONField(default=dict, help_text="Feature usage breakdown")
    usage_growth = models.FloatField(default=0.0, help_text="Growth rate compared to previous period")
    user_satisfaction = models.FloatField(null=True, blank=True, help_text="Avg satisfaction score if available")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} usage ({self.period}: {self.period_start} to {self.period_end})"
    
    class Meta:
        ordering = ['-period_end']
        verbose_name_plural = "Product usage metrics"
        indexes = [
            models.Index(fields=['product', 'period']),
            models.Index(fields=['organization']),
            models.Index(fields=['period_start', 'period_end']),
        ]


class BusinessInsight(models.Model):
    """
    Business insights generated from analytics data.
    Provides actionable insights for both B2B and B2C strategies.
    """
    INSIGHT_TYPE_CHOICES = [
        ("usage", "Usage Pattern"),
        ("engagement", "User Engagement"),
        ("retention", "Retention Issue"),
        ("growth", "Growth Opportunity"),
        ("conversion", "Conversion Funnel"),
        ("segment", "User Segmentation"),
        ("feature", "Feature Utilization"),
        ("satisfaction", "User Satisfaction"),
    ]
    
    AUDIENCE_CHOICES = [
        ("all", "All Teams"),
        ("product", "Product Team"),
        ("marketing", "Marketing Team"),
        ("sales", "Sales Team"),
        ("customer_success", "Customer Success Team"),
        ("executive", "Executive Team"),
    ]
    
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    
    title = models.CharField(max_length=255)
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPE_CHOICES)
    description = models.TextField()
    data_points = models.JSONField(help_text="Supporting data and metrics")
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="all")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name="insights")
    is_system_generated = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name="created_insights")
    recommendations = models.TextField(blank=True)
    is_actioned = models.BooleanField(default=False)
    actioned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name="actioned_insights")
    actioned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.insight_type})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['insight_type']),
            models.Index(fields=['organization']),
            models.Index(fields=['priority']),
        ] 