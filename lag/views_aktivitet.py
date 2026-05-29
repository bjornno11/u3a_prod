# lag/views_aktivitet.py
from django.shortcuts import render
from lag.models import Aktivitet
from lag.context_processors import lokallag_from_host


def aktivitet_liste(request):
    lokallag = lokallag_from_host(request).get("lokallag")

    qs = Aktivitet.objects.filter(publisert=True).select_related("organisasjon").order_by("-dato", "-opprettet")

    if lokallag:
        qs = qs.filter(organisasjon=lokallag)

    return render(request, "lag/aktivitet_liste.html", {"aktiviteter": qs[:50]})
