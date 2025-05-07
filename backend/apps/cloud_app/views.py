from django.shortcuts import render
from apps.cloud_app.models import Organisation
from django.http import JsonResponse

def organisation_list(requests):
    organisations = Organisation.objects.all()
    data = {
                "organisations": list(organisations.values())
           }
    return JsonResponse(data)


def organisation_detail(requests, organisationId):
    organisation = Organisation.objects.get(organisation_id=organisationId)
    data = {
            'name': organisation.organisation_name,
            'owner-id': organisation.owner_id,
            'createdAt': organisation.created_at,
          }
    return JsonResponse(data)