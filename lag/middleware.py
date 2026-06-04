from lag.models import Organisasjon
from django.shortcuts import render


class SubdomeneAdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""

        if (
            (path.startswith("/admin/") or path.startswith("/lokaladmin/"))
            and request.user.is_authenticated
        ):
            if request.user.is_superuser:
                return self.get_response(request)

            host = (request.get_host() or "").split(":")[0].lower()

            if host in ("u3a.no", "www.u3a.no"):
                return self.get_response(request)

            subdomene = host.replace(".u3a.no", "")

            if not Organisasjon.objects.filter(
                subdomene=subdomene,
                redaktorer=request.user
            ).exists():
                return render(
                    request,
                    "admin/lag/ingen_tilgang.html",
                    status=403
                )

        return self.get_response(request)

from django.utils import timezone
from .models import Sidevisning


class SidevisningMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        sti = request.path or "/"

        ignorer = (
            "/admin/",
            "/static/",
            "/media/",
            "/favicon.ico",
            "/robots.txt",
            "/postnummer-lookup/",
        )

        if not sti.startswith(ignorer):
            host = request.get_host().split(":")[0].lower()
            dato = timezone.localdate()

            obj, created = Sidevisning.objects.get_or_create(
                dato=dato,
                host=host,
                sti=sti,
                defaults={"antall": 0},
            )

            obj.antall += 1
            obj.save(update_fields=["antall", "sist_besokt"])

        return response

