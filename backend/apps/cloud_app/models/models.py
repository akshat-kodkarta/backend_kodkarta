import uuid
from django.db import models

class Organisation(models.Model):
    id = models.AutoField(primary_key=True)  
    organisation_id = models.UUIDField(default=uuid.uuid4, unique=True)  
    organisation_name = models.CharField(max_length=255)
    owner_id = models.UUIDField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      

    class Meta:
        db_table = 'Organisations'
        verbose_name = 'Cloud Organisation'
        verbose_name_plural = 'Cloud Organisations'

    def __str__(self):
        return self.organisation_name