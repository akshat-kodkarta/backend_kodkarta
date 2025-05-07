from django.db import models
from apps.users.models.models import User, Organization
from apps.products.models.models import ProductCatalog
from apps.assets.models.models import SoftwareComponent
from apps.integrations.models.models import GitRepository, CloudResource
from apps.policies.models.models import SecurityPolicy

class Graph(models.Model):
    """
    Graph visualization for software assets and dependencies.
    Provides visual representation of product components and relationships.
    """
    GRAPH_TYPE_CHOICES = [
        ("product", "Product Graph"),
        ("dependency", "Dependency Graph"),
        ("security", "Security Visualization"),
        ("infrastructure", "Infrastructure Map"),
        ("compliance", "Compliance Status"),
        ("ai_governance", "AI Governance Map")
    ]
    
    VISIBILITY_CHOICES = [
        ("private", "Private (Owner Only)"),
        ("organization", "Organization"),
        ("public", "Public")
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    graph_type = models.CharField(max_length=50, choices=GRAPH_TYPE_CHOICES, default="product")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="graphs")
    product = models.ForeignKey(ProductCatalog, on_delete=models.CASCADE, null=True, blank=True, 
                             related_name="graphs")
    repositories = models.ManyToManyField(GitRepository, blank=True, related_name="visualizations")
    graph_data = models.JSONField(help_text="Graph structure and visualization data")
    layout_algorithm = models.CharField(max_length=100, default="force-directed")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_visualizations")
    last_generated = models.DateTimeField(auto_now=True, help_text="When the graph was last generated")
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default="organization")
    is_snapshot = models.BooleanField(default=False, help_text="Whether this is a point-in-time snapshot")
    snapshot_timestamp = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.graph_type})"
    
    class Meta:
        db_table = 'graph'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['organization', 'graph_type']),
            models.Index(fields=['product']),
            models.Index(fields=['created_by'])
        ]
        verbose_name = 'Graph'
        verbose_name_plural = 'Graphs'

class GraphNode(models.Model):
    """
    Node within a visualization graph.
    Represents a software component, service, or resource in a graph.
    """
    NODE_TYPE_CHOICES = [
        ("component", "Software Component"),
        ("service", "Service"),
        ("database", "Database"),
        ("storage", "Storage"),
        ("compute", "Compute Resource"),
        ("function", "Serverless Function"),
        ("ai_model", "AI Model"),
        ("external", "External Service"),
        ("custom", "Custom")
    ]
    
    NODE_STATUS_CHOICES = [
        ("normal", "Normal"),
        ("warning", "Warning"),
        ("critical", "Critical"),
        ("inactive", "Inactive")
    ]
    
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="nodes")
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    node_type = models.CharField(max_length=50, choices=NODE_TYPE_CHOICES)
    component = models.ForeignKey(SoftwareComponent, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="graph_nodes")
    cloud_resource = models.ForeignKey(CloudResource, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=NODE_STATUS_CHOICES, default="normal")
    properties = models.JSONField(default=dict)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    size = models.FloatField(default=1.0)
    icon = models.CharField(max_length=100, blank=True)
    custom_style = models.JSONField(default=dict, blank=True)
    is_expandable = models.BooleanField(default=False)
    is_expanded = models.BooleanField(default=False)
    has_issues = models.BooleanField(default=False, help_text="Whether this node has security/compliance issues")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.node_type})"
    
    class Meta:
        db_table = 'graph_node'
        ordering = ['graph', 'name']
        indexes = [
            models.Index(fields=['graph', 'node_type']),
            models.Index(fields=['component']),
            models.Index(fields=['status'])
        ]
        verbose_name = 'Graph Node'
        verbose_name_plural = 'Graph Nodes'

class GraphEdge(models.Model):
    """
    Edge connecting nodes in a visualization graph.
    Represents relationships between software components, services, and resources.
    """
    EDGE_TYPE_CHOICES = [
        ("depends", "Depends On"),
        ("calls", "Calls"),
        ("contains", "Contains"),
        ("deploys", "Deploys"),
        ("accesses", "Accesses"),
        ("generates", "Generates"),
        ("secures", "Secures"),
        ("monitors", "Monitors"),
        ("custom", "Custom")
    ]
    
    SECURITY_STATUS_CHOICES = [
        ("secure", "Secure"),
        ("warning", "Warning"),
        ("vulnerable", "Vulnerable"),
        ("unknown", "Unknown")
    ]
    
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE, related_name="edges")
    source = models.ForeignKey(GraphNode, on_delete=models.CASCADE, related_name="outgoing_edges")
    target = models.ForeignKey(GraphNode, on_delete=models.CASCADE, related_name="incoming_edges")
    edge_type = models.CharField(max_length=50, choices=EDGE_TYPE_CHOICES)
    label = models.CharField(max_length=100, blank=True)
    weight = models.FloatField(default=1.0)
    security_status = models.CharField(max_length=20, choices=SECURITY_STATUS_CHOICES, default="unknown")
    properties = models.JSONField(default=dict, blank=True)
    custom_style = models.JSONField(default=dict, blank=True)
    is_bidirectional = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.source.name} → {self.target.name} ({self.edge_type})"
    
    class Meta:
        db_table = 'graph_edge'
        ordering = ['graph', 'source']
        indexes = [
            models.Index(fields=['graph', 'edge_type']),
            models.Index(fields=['source', 'target']),
            models.Index(fields=['security_status'])
        ]
        verbose_name = 'Graph Edge'
        verbose_name_plural = 'Graph Edges'

class Dashboard(models.Model):
    """
    Custom dashboards for security visualization.
    Provides customizable views of security and compliance data.
    """
    DASHBOARD_TYPE_CHOICES = [
        ("security", "Security Dashboard"),
        ("compliance", "Compliance Dashboard"),
        ("performance", "Performance Dashboard"),
        ("operations", "Operations Dashboard"),
        ("ai_governance", "AI Governance Dashboard"),
        ("custom", "Custom Dashboard")
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dashboard_type = models.CharField(max_length=50, choices=DASHBOARD_TYPE_CHOICES, default="security")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dashboards")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="dashboards")
    products = models.ManyToManyField(ProductCatalog, blank=True, related_name="dashboards")
    layout = models.JSONField(help_text="Dashboard layout configuration")
    widgets = models.JSONField(default=list, help_text="Widgets configuration and settings")
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name="shared_dashboards")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.dashboard_type})"
    
    class Meta:
        db_table = 'visualization_dashboard'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'dashboard_type']),
            models.Index(fields=['owner']),
            models.Index(fields=['is_default'])
        ]
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'

class SecurityVisualization(models.Model):
    """
    Specialized security visualization for software assets.
    Provides security-focused views of software components and risks.
    """
    VISUALIZATION_TYPE_CHOICES = [
        ("risk_map", "Risk Heatmap"),
        ("compliance", "Compliance Status"),
        ("attack_paths", "Attack Paths"),
        ("vulnerability", "Vulnerability Map"),
        ("security_posture", "Security Posture"),
        ("ai_risk", "AI Risk Visualization")
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visualization_type = models.CharField(max_length=50, choices=VISUALIZATION_TYPE_CHOICES)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    products = models.ManyToManyField(ProductCatalog, blank=True, related_name="security_visualizations")
    source_graph = models.ForeignKey(Graph, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="security_visualizations")
    policies = models.ManyToManyField(SecurityPolicy, blank=True, related_name="visualizations")
    visualization_data = models.JSONField(help_text="Specialized security visualization data")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_security_visualizations")
    is_public = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.visualization_type})"
    
    class Meta:
        db_table = 'security_visualization'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'visualization_type']),
            models.Index(fields=['created_by'])
        ]
        verbose_name = 'Security Visualization'
        verbose_name_plural = 'Security Visualizations' 