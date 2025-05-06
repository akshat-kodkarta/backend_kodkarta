from django.db import models
from apps.users.models.models import User, Organization
from apps.products.models.models import ProductCatalog
from apps.assets.models.models import SoftwareComponent
from apps.integrations.models.models import GitRepository, CloudResource
from apps.policies.models.models import SecurityPolicy, ComplianceResult

class Insight(models.Model):
    """
    AI-generated insights about software components and products.
    Provides security, performance, and architectural recommendations.
    """
    TYPE_CHOICES = [
        ("security", "Security"),
        ("performance", "Performance"),
        ("architecture", "Architecture"),
        ("anomaly", "Anomaly"),
        ("recommendation", "Recommendation"),
        ("compliance", "Compliance"),
        ("dependency", "Dependency"),
        ("risk", "Risk"),
        ("ai_governance", "AI Governance")
    ]
    
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical")
    ]
    
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
        ("false_positive", "False Positive")
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    product = models.ForeignKey(ProductCatalog, on_delete=models.CASCADE, null=True, blank=True, 
                             related_name="insights")
    component = models.ForeignKey(SoftwareComponent, on_delete=models.CASCADE, null=True, blank=True, 
                               related_name="insights")
    repository = models.ForeignKey(GitRepository, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name="insights")
    cloud_resource = models.ForeignKey(CloudResource, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name="insights")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="insights")
    data = models.JSONField(help_text="Detailed insight data, including evidence")
    recommendation = models.TextField(help_text="Specific action recommended to address the insight")
    confidence_score = models.FloatField(default=0.0, help_text="AI confidence in this insight (0-1)")
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name="resolved_insights")
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.type}, {self.severity})"
    
    class Meta:
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'type']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['component'])
        ]

class AnomalyDetection(models.Model):
    """
    Detected anomalies in software components and cloud resources.
    Identifies unusual patterns, behaviors, and potential security risks.
    """
    TYPE_CHOICES = [
        ("access_pattern", "Unusual Access Pattern"),
        ("dependency_risk", "Dependency Risk"),
        ("security_issue", "Security Issue"),
        ("performance", "Performance Anomaly"),
        ("deployment", "Deployment Anomaly"),
        ("configuration", "Configuration Anomaly"),
        ("ai_behavior", "AI Behavior Anomaly")
    ]
    
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical")
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    anomaly_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    component = models.ForeignKey(SoftwareComponent, on_delete=models.CASCADE, null=True, blank=True, 
                               related_name="anomalies")
    product = models.ForeignKey(ProductCatalog, on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name="anomalies")
    cloud_resource = models.ForeignKey(CloudResource, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name="anomalies")
    repository = models.ForeignKey(GitRepository, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name="anomalies")
    detected_at = models.DateTimeField()
    anomaly_data = models.JSONField(help_text="Detailed anomaly information")
    confidence_score = models.FloatField(help_text="Confidence level (0-1)")
    baseline_data = models.JSONField(default=dict, blank=True, 
                                  help_text="Baseline comparison data")
    is_false_positive = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name="reviewed_anomalies")
    remediation_steps = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} in {self.component.name if self.component else 'unknown'} ({self.anomaly_type})"
    
    class Meta:
        ordering = ['-severity', '-detected_at']
        indexes = [
            models.Index(fields=['component', 'anomaly_type']),
            models.Index(fields=['product', 'severity']),
            models.Index(fields=['detected_at'])
        ]

class AIResponse(models.Model):
    """
    AI-generated responses to user queries about software assets.
    Tracks conversations and context for RAG-based assistance.
    """
    QUERY_TYPE_CHOICES = [
        ("general", "General Question"),
        ("security", "Security Question"),
        ("compliance", "Compliance Question"),
        ("architecture", "Architecture Question"),
        ("recommendation", "Recommendation Request"),
        ("troubleshooting", "Troubleshooting")
    ]
    
    query = models.TextField()
    query_type = models.CharField(max_length=50, choices=QUERY_TYPE_CHOICES, default="general")
    response = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_queries")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="ai_responses")
    product = models.ForeignKey(ProductCatalog, on_delete=models.SET_NULL, null=True, blank=True)
    component = models.ForeignKey(SoftwareComponent, on_delete=models.SET_NULL, null=True, blank=True)
    context_data = models.JSONField(help_text="Context and source information used for the response")
    sources = models.JSONField(default=list, blank=True, 
                            help_text="Source documents/components referenced")
    conversation_id = models.CharField(max_length=100, blank=True, 
                                    help_text="ID to group related queries")
    feedback_score = models.IntegerField(null=True, blank=True, help_text="User feedback (1-5)")
    tokens_used = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to: {self.query[:50]}..."
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['organization']),
            models.Index(fields=['conversation_id'])
        ]

class KnowledgeGraph(models.Model):
    """
    Knowledge graph representing software assets and relationships.
    Provides a semantic understanding of the software ecosystem.
    """
    GRAPH_TYPE_CHOICES = [
        ("product", "Product Graph"),
        ("component", "Component Graph"),
        ("security", "Security Graph"),
        ("dependency", "Dependency Graph"),
        ("architecture", "Architecture Graph"),
        ("full", "Full System Graph")
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    graph_type = models.CharField(max_length=50, choices=GRAPH_TYPE_CHOICES)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductCatalog, on_delete=models.SET_NULL, null=True, blank=True)
    graph_data = models.JSONField(help_text="Knowledge graph structure and relationships")
    metadata = models.JSONField(default=dict, blank=True)
    node_count = models.IntegerField(default=0)
    edge_count = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    last_updated = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_knowledge_graphs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.graph_type})"
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['organization', 'graph_type']),
            models.Index(fields=['product'])
        ] 