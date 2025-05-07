from django.urls import path, include
from apps.cloud_app.views import organisation_list, organisation_detail

urlpatterns = [
    
    path("list/", organisation_list, name="organisation_list"),
    path("<uuid:organisationId>", organisation_detail, name="organisation-detail"),
]
