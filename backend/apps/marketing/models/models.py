from django.db import models
from apps.users.models.models import User, Organization

class MarketingCampaign(models.Model):
    """
    Marketing campaigns for both B2B and B2C users.
    Tracks campaign details, target segments, and performance metrics.
    """
    CAMPAIGN_TYPE_CHOICES = [
        ("acquisition", "New User Acquisition"),
        ("retention", "User Retention"),
        ("reactivation", "User Reactivation"),
        ("upsell", "Upsell/Upgrade"),
        ("awareness", "Brand Awareness"),
        ("education", "Product Education"),
        ("event", "Event Promotion"),
    ]
    
    TARGET_SEGMENT_CHOICES = [
        ("all", "All Users"),
        ("business", "Business Users"),
        ("consumer", "Consumer Users"),
        ("enterprise", "Enterprise Organizations"),
        ("smb", "Small/Medium Businesses"),
        ("free_tier", "Free Tier Users"),
        ("premium", "Premium Users"),
        ("inactive", "Inactive Users"),
    ]
    
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES)
    target_segment = models.CharField(max_length=20, choices=TARGET_SEGMENT_CHOICES)
    custom_segment_rules = models.JSONField(default=dict, blank=True, 
                                         help_text="Custom segmentation rules for targeting")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    channels = models.JSONField(default=list, 
                             help_text="List of marketing channels used in this campaign")
    content = models.JSONField(default=dict, 
                            help_text="Campaign content and creative assets")
    performance_metrics = models.JSONField(default=dict, blank=True,
                                        help_text="Campaign performance metrics")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_campaigns")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.campaign_type})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign_type']),
            models.Index(fields=['status']),
            models.Index(fields=['target_segment']),
        ]


class LeadCapture(models.Model):
    """
    Lead capture for B2B and B2C marketing.
    Tracks leads, their sources, and conversion status.
    """
    SOURCE_CHOICES = [
        ("website", "Website"),
        ("campaign", "Marketing Campaign"),
        ("social", "Social Media"),
        ("event", "Event"),
        ("referral", "Referral"),
        ("organic", "Organic Search"),
        ("paid", "Paid Advertising"),
        ("partner", "Partner"),
    ]
    
    LEAD_TYPE_CHOICES = [
        ("business", "Business Lead"),
        ("consumer", "Consumer Lead"),
    ]
    
    STATUS_CHOICES = [
        ("new", "New Lead"),
        ("qualified", "Qualified Lead"),
        ("nurturing", "In Nurturing"),
        ("converted", "Converted"),
        ("rejected", "Rejected"),
        ("dormant", "Dormant"),
    ]
    
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    lead_type = models.CharField(max_length=20, choices=LEAD_TYPE_CHOICES)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name="leads")
    landing_page = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    interest_score = models.IntegerField(default=0, help_text="Lead qualification score")
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    opted_in = models.BooleanField(default=True, help_text="Whether lead opted in to marketing communications")
    converted_to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name="converted_from_lead")
    converted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name or self.email} ({self.lead_type})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['lead_type']),
            models.Index(fields=['status']),
            models.Index(fields=['source']),
        ]


class ContentAsset(models.Model):
    """
    Marketing content assets for both B2B and B2C audiences.
    Manages blog posts, whitepapers, case studies, videos, etc.
    """
    CONTENT_TYPE_CHOICES = [
        ("blog", "Blog Post"),
        ("whitepaper", "Whitepaper"),
        ("case_study", "Case Study"),
        ("ebook", "E-Book"),
        ("video", "Video"),
        ("webinar", "Webinar"),
        ("infographic", "Infographic"),
        ("newsletter", "Newsletter"),
        ("social", "Social Media Post"),
    ]
    
    TARGET_AUDIENCE_CHOICES = [
        ("all", "All Audiences"),
        ("business", "Business Users"),
        ("consumer", "Consumer Users"),
        ("enterprise", "Enterprise"),
        ("smb", "Small/Medium Businesses"),
        ("technical", "Technical Users"),
        ("executive", "Executive Level"),
    ]
    
    FUNNEL_STAGE_CHOICES = [
        ("awareness", "Awareness"),
        ("consideration", "Consideration"),
        ("decision", "Decision"),
        ("retention", "Retention"),
        ("advocacy", "Advocacy"),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES)
    funnel_stage = models.CharField(max_length=20, choices=FUNNEL_STAGE_CHOICES)
    content_url = models.URLField(blank=True)
    content_file = models.CharField(max_length=512, blank=True, help_text="Path to content file in storage")
    thumbnail = models.CharField(max_length=512, blank=True, help_text="Path to thumbnail image")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                            related_name="authored_content")
    publish_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    is_gated = models.BooleanField(default=False, help_text="Whether content requires lead capture")
    tags = models.JSONField(default=list, blank=True)
    seo_keywords = models.TextField(blank=True)
    campaigns = models.ManyToManyField(MarketingCampaign, blank=True, related_name="content_assets")
    engagement_metrics = models.JSONField(default=dict, blank=True,
                                       help_text="Content engagement metrics")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.content_type})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type']),
            models.Index(fields=['target_audience']),
            models.Index(fields=['is_published']),
        ] 