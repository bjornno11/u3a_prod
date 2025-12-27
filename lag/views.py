# /srv/u3a/lag/views.py

from django.shortcuts import render
from django.http import HttpResponse
from .models import Organisasjon 
# lag/views.py
from django.shortcuts import render, get_object_or_404
from .models import Aktivitet

# VIKTIG: Ingen import av settings er nødvendig her


def home_page(request):
    """Viser hjemmesiden ved å laste inn index.html malen."""
    return render(request, 'lag/index.html') 

def lokallag_liste(request):
    # Henter statusparameter fra URL-en. Bruker .lower() for robusthet.
    filter_status = request.GET.get('status', 'aktive').lower()

    # Starter med å hente alle objekter
    organisasjoner = Organisasjon.objects.all()

    if filter_status == 'alle':
        # Viser ALLE organisasjoner
        pass # Ingen filtrering nødvendig
    else:
        # Standard: Viser KUN 'Aktive' organisasjoner
        organisasjoner = organisasjoner.filter(status='Aktiv')

    # SORTERER alle resultater for å unngå uforutsigbar atferd
    organisasjoner = organisasjoner.order_by('fylke', 'kommune', 'organisasjon')

    # Teller aktive (uavhengig av filteret)
    antall_aktive = Organisasjon.objects.filter(status='Aktiv').count()

    context = {
        'organisasjoner': organisasjoner,
        'antall_aktive': antall_aktive,
        'filter_status': filter_status, # Sender valgt status til malen
    }
    return render(request, 'lag/lokallag_liste.html', context)


def lokallag_kart(request):
    """
    Henter aktive organisasjoner med koordinater for visning på kart.
    Filtrerer bort NULL og (0,0).
    """
    kartdata = (
        Organisasjon.objects
        .filter(status='Aktiv')
        .exclude(breddegrad__isnull=True)
        .exclude(lengdegrad__isnull=True)
        .exclude(breddegrad=0)
        .exclude(lengdegrad=0)
        .order_by('fylke', 'kommune', 'organisasjon')
    )

    context = {
        'kartdata': kartdata,
        'antall_markorer': kartdata.count(),
    }
    return render(request, 'lag/lokallag_kart.html', context)


def regnskap_side(request):
    """
    View for regnskapssiden.
    """
    context = {
        'page_title': 'Regnskap'
    }
    return render(request, 'lag/regnskap.html', context)

def aktivitet_detalj(request, slug):
    aktivitet = get_object_or_404(Aktivitet, slug=slug, publisert=True)
    return render(request, "lag/aktivitet_detalj.html", {"aktivitet": aktivitet})
