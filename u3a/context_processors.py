from django.conf import settings

def site_contact(request):
    return {
        "CONTACT_EMAIL": getattr(settings, "CONTACT_EMAIL", "")
    }
