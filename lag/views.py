# /srv/u3a/lag/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Organisasjon, LagMedlem, Aktivitet, LagMedlemVerv 
from .forms import LagMedlemRegistreringForm
from .models import Organisasjon
from django.http import JsonResponse
from .models import Organisasjon, Postnummer
from django.contrib.admin.views.decorators import staff_member_required
from .models import Nyhet
from django.utils import timezone
from lag.context_processors import lokallag_from_host

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

def styre_side(request):
    organisasjon = hent_organisasjon_fra_host(request)

    if organisasjon is None:
        return render(request, "lag/styre_side.html", {
            "organisasjon": None,
            "verv": [],
            "feil": "Fant ikke lokallag for dette domenet.",
        })

    verv = (
        LagMedlemVerv.objects
        .filter(
            organisasjon=organisasjon,
            aktiv=True,
        )
        .select_related("medlem", "rolle", "utvalg")
        .order_by("rolle__navn", "medlem__etternavn", "medlem__fornavn")
    )

    return render(request, "lag/styre_side.html", {
        "organisasjon": organisasjon,
        "verv": verv,
    })



def registrer_medlem(request):
    organisasjon = hent_organisasjon_fra_host(request)

    if organisasjon is None:
        return render(request, "lag/registrer_medlem.html", {
            "form": LagMedlemRegistreringForm(),
            "organisasjon": None,
            "feil": "Fant ikke lokallag for dette domenet.",
        })

    if request.method == "POST":
        form = LagMedlemRegistreringForm(request.POST)
        if form.is_valid():
            medlem = form.save(commit=False)
            medlem.organisasjon = organisasjon
            medlem.save()
            return redirect("registrer_medlem_takk")
    else:
        form = LagMedlemRegistreringForm()

    return render(request, "lag/registrer_medlem.html", {
        "form": form,
        "organisasjon": organisasjon,
    })
def registrer_medlem_takk(request):
    organisasjon = hent_organisasjon_fra_host(request)

    return render(request, "lag/registrer_medlem_takk.html", {
        "organisasjon": organisasjon,
    })
def hent_organisasjon_fra_host(request):
    host = request.get_host().split(":")[0]
    subdomene = host.split(".")[0]
    return Organisasjon.objects.filter(subdomene=subdomene).first()

def postnummer_lookup(request):
    postnummer = request.GET.get("postnummer", "").strip()

    try:
        post = Postnummer.objects.get(postnummer=postnummer)
        return JsonResponse({
            "found": True,
            "poststed": post.poststed,
            "kommune": post.kommune,
            "fylke": post.fylke,
        })
    except Postnummer.DoesNotExist:
        return JsonResponse({"found": False})

@staff_member_required
def godkjenn_medlemmer(request):
    organisasjon = hent_organisasjon_fra_host(request)

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon,
        status=LagMedlem.STATUS_REGISTRERT,
    ).order_by("opprettet")

    return render(request, "lag/godkjenn_medlemmer.html", {
        "organisasjon": organisasjon,
        "medlemmer": medlemmer,
    })


@staff_member_required
def godkjenn_medlem(request, medlem_id):
    organisasjon = hent_organisasjon_fra_host(request)

    medlem = get_object_or_404(
        LagMedlem,
        id=medlem_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        medlem.status = LagMedlem.STATUS_GODKJENT
        medlem.aktiv = True
        medlem.save()
        return redirect("godkjenn_medlemmer")

    return redirect("godkjenn_medlemmer")

def nyhet_detalj(request, nyhet_id):
    nyhet = get_object_or_404(
        Nyhet,
        id=nyhet_id,
        publisert=True,
    )

    return render(
        request,
        "lag/nyhet_detalj.html",
        {
            "nyhet": nyhet,
            "organisasjon": nyhet.organisasjon,
        }
    )
def program(request):
    lokallag = lokallag_from_host(request).get("lokallag")

    aktiviteter = Aktivitet.objects.filter(
        publisert=True
    ).select_related("organisasjon")

    if lokallag:
        aktiviteter = aktiviteter.filter(
            organisasjon=lokallag
        )

    aktiviteter = aktiviteter.order_by(
        "dato",
        "starttid",
        "tittel"
    )

    return render(
        request,
        "lag/program.html",
        {
            "lokallag": lokallag,
            "aktiviteter": aktiviteter,
        }
    )

