from django.db import models
from apps.users.models.models import Organization, User
from apps.integrations.models.models import DataSource
from apps.assets.models.models import SoftwareComponent
from apps.products.models.models import ProductCatalog

class SecurityPolicy(models.Model):
    """
    Security policy definitions for compliance and governance.
    Defines rules and compliance standards for software assets.
    """
    POLICY_TYPE_CHOICES = [
        ("security", "Security Policy"),
        ("compliance", "Compliance Standard"),
        ("governance", "Governance Policy"),
        ("custom", "Custom Policy"),
        ("ai_governance", "AI Governance")
    ]
    
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical")
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    standard_reference = models.CharField(max_length=100, blank=True, 
                                      help_text="Reference to external standard (ISO, NIST, etc.)")
    policy_content = models.JSONField(help_text="Policy definition and rules")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="security_policies")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                related_name="created_policies")
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False, help_text="System-defined policies vs user-created")
    tags = models.JSONField(default=list, blank=True)
    products = models.ManyToManyField(ProductCatalog, blank=True, related_name="applicable_policies")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.policy_type})"
    
    class Meta:
        db_table = 'security_policy'
        verbose_name_plural = "Security policies"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'policy_type']),
            models.Index(fields=['is_active'])
        ]
        verbose_name = 'Security Policy'

class PolicyRule(models.Model):
    """
    Individual policy rules within a security policy.
    Defines specific checks and conditions for compliance.
    """
    RULE_TYPE_CHOICES = [
        ("condition", "Condition Check"),
        ("pattern", "Pattern Match"),
        ("threshold", "Threshold Check"),
        ("existence", "Existence Check"),
        ("scan", "Security Scan"),
        ("ai", "AI/ML Check")
    ]
    
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"), 
        ("critical", "Critical")
    ]
    
    policy = models.ForeignKey(SecurityPolicy, on_delete=models.CASCADE, related_name="rules")
    name = models.CharField(max_length=255)
    description = models.TextField()
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    target_component_type = models.CharField(max_length=100, 
                                          help_text="Type of component this rule applies to")
    target_resource_pattern = models.CharField(max_length=255, blank=True, 
                                           help_text="Pattern to match resources")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    condition = models.JSONField(help_text="Rule conditions and checks")
    remediation = models.TextField(blank=True, help_text="Instructions for remediation")
    is_active = models.BooleanField(default=True)
    is_blocking = models.BooleanField(default=False, 
                                   help_text="If true, blocks deployments when violated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.policy.name} - {self.name}"
    
    class Meta:
        db_table = 'policy_rule'
        ordering = ['policy', '-severity']
        indexes = [
            models.Index(fields=['policy', 'rule_type']),
            models.Index(fields=['target_component_type'])
        ]
        verbose_name = 'Policy Rule'
        verbose_name_plural = 'Policy Rules'

class ScanJob(models.Model):
    """
    Security and compliance scan jobs.
    Tracks scanning operations across data sources.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled")
    ]
    
    SCAN_TYPE_CHOICES = [
        ("security", "Security Scan"),
        ("compliance", "Compliance Scan"),
        ("discovery", "Discovery Scan"),
        ("dependency", "Dependency Scan"), 
        ("ai_audit", "AI Audit")
    ]
    
    name = models.CharField(max_length=255)
    scan_type = models.CharField(max_length=50, choices=SCAN_TYPE_CHOICES)
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="scan_jobs")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    policies = models.ManyToManyField(SecurityPolicy, blank=True, related_name="scan_jobs")
    configuration = models.JSONField(default=dict, help_text="Scan job configuration")
    result = models.JSONField(default=dict)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name="initiated_scans")
    scheduled = models.BooleanField(default=False, help_text="Is this a scheduled scan")
    items_scanned = models.IntegerField(default=0)
    issues_found = models.IntegerField(default=0)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.scan_type}, {self.status})"
    
    class Meta:
        db_table = 'scan_job'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['data_source', 'status']),
            models.Index(fields=['scan_type'])
        ]
        verbose_name = 'Scan Job'
        verbose_name_plural = 'Scan Jobs'

class ComplianceResult(models.Model):
    """
    Results of compliance checks against policies.
    Tracks the compliance status of software components.
    """
    STATUS_CHOICES = [
        ("compliant", "Compliant"),
        ("non_compliant", "Non-Compliant"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("not_applicable", "Not Applicable")
    ]
    
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical")
    ]
    
    component = models.ForeignKey(SoftwareComponent, on_delete=models.CASCADE, 
                               related_name="compliance_results")
    product = models.ForeignKey(ProductCatalog, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name="compliance_results")
    policy = models.ForeignKey(SecurityPolicy, on_delete=models.CASCADE, 
                            related_name="compliance_results")
    rule = models.ForeignKey(PolicyRule, on_delete=models.SET_NULL, null=True, 
                          related_name="compliance_results")
    scan_job = models.ForeignKey(ScanJob, on_delete=models.CASCADE, related_name="compliance_results")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    details = models.JSONField(help_text="Detailed compliance check results")
    evidence = models.TextField(blank=True, help_text="Evidence supporting the result")
    remediation_steps = models.TextField(blank=True)
    is_fixed = models.BooleanField(default=False)
    fixed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fixed_at = models.DateTimeField(null=True, blank=True)
    checked_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.component.name} - {self.policy.name}: {self.status}"
    
    class Meta:
        db_table = 'compliance_result'
        ordering = ['-severity', '-checked_at']
        indexes = [
            models.Index(fields=['component', 'status']),
            models.Index(fields=['policy']),
            models.Index(fields=['scan_job'])
        ]
        verbose_name = 'Compliance Result'
        verbose_name_plural = 'Compliance Results' 