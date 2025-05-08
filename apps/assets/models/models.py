from django.db import models
from apps.integrations.models.models import DataSource, GitRepository
from apps.products.models.models import ProductCatalog

class SoftwareComponent(models.Model):
    """
    Software components discovered through integrations.
    Represents code modules, libraries, services, or other software assets.
    """
    TYPE_CHOICES = [
        ("code", "Source Code"),
        ("library", "Library/Package"),
        ("service", "Microservice"),
        ("api", "API Component"),
        ("database", "Database"),
        ("function", "Serverless Function"),
        ("infra", "Infrastructure Code"),
        ("container", "Container"),
        ("ai_model", "AI Model"),
        ("config", "Configuration")
    ]
    
    DISCOVERY_METHOD_CHOICES = [
        ("automated", "Automated Scanning"),
        ("manual", "Manual Entry"),
        ("imported", "Imported")
    ]
    
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    resource_id = models.CharField(max_length=255, null=True, blank=True)
    path = models.CharField(max_length=1024, help_text="Path to the component within its source")
    repository = models.ForeignKey(GitRepository, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name="components")
    metadata = models.JSONField(default=dict)
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="discovered_components")
    discovery_method = models.CharField(max_length=50, choices=DISCOVERY_METHOD_CHOICES, default="automated")
    language = models.CharField(max_length=50, blank=True, null=True)
    version = models.CharField(max_length=100, blank=True, null=True)
    last_updated_in_source = models.DateTimeField(null=True, blank=True)
    security_score = models.FloatField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.type})"
    
    class Meta:
        db_table = 'software_component'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['data_source', 'type']),
            models.Index(fields=['repository', 'path'])
        ]
        verbose_name = 'Software Component'
        verbose_name_plural = 'Software Components'

class ProductComponent(models.Model):
    """
    Mapping between products and components.
    Establishes relationships between business products and discovered software components.
    """
    RELATIONSHIP_TYPE_CHOICES = [
        ("primary", "Primary Component"),
        ("dependency", "Dependency"),
        ("included", "Included Component"),
        ("generated", "Generated Component"),
        ("deployed", "Deployed Resource"),
        ("consumed", "Consumed Service")
    ]
    
    product = models.ForeignKey(ProductCatalog, on_delete=models.CASCADE, related_name="components")
    component = models.ForeignKey(SoftwareComponent, on_delete=models.CASCADE, related_name="products")
    relationship_type = models.CharField(max_length=50, choices=RELATIONSHIP_TYPE_CHOICES, default="included")
    importance = models.CharField(max_length=20, default="medium", 
                               help_text="Importance of this component to the product")
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.component.name} ({self.relationship_type})"
    
    class Meta:
        db_table = 'product_component'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'relationship_type']),
            models.Index(fields=['component'])
        ]
        verbose_name = 'Product Component'
        verbose_name_plural = 'Product Components'

class Dependency(models.Model):
    """
    Dependencies between software components.
    Tracks relationships and dependencies between discovered software assets.
    """
    DEPENDENCY_TYPE_CHOICES = [
        ("imports", "Code Import"),
        ("requires", "Requires/Depends On"),
        ("calls", "API Call"),
        ("consumes", "Consumes Service"),
        ("uses", "Uses Resource"),
        ("generates", "Generates"),
        ("deploys", "Deploys"),
        ("connects", "Connects To")
    ]
    
    CRITICALITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical")
    ]
    
    source_component = models.ForeignKey(SoftwareComponent, related_name="outgoing_dependencies", on_delete=models.CASCADE)
    target_component = models.ForeignKey(SoftwareComponent, related_name="incoming_dependencies", on_delete=models.CASCADE)
    dependency_type = models.CharField(max_length=50, choices=DEPENDENCY_TYPE_CHOICES)
    criticality = models.CharField(max_length=20, choices=CRITICALITY_CHOICES, default="medium")
    is_direct = models.BooleanField(default=True, help_text="Whether this is a direct dependency")
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True, 
                              help_text="Additional metadata about the dependency")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.source_component.name} → {self.target_component.name} ({self.dependency_type})"
    
    class Meta:
        db_table = 'assets_dependency'
        verbose_name_plural = "Dependencies"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_component']),
            models.Index(fields=['target_component']),
            models.Index(fields=['dependency_type'])
        ]
        verbose_name = 'Dependency' 