from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from lag.models import Organisasjon
from .models import Konto, Bilag, Bilagslinje, Avdeling, Prosjekt, Styrekode, Regnskapsaar, Bilagsserie
from .services import opprett_standard_regnskap
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
from django.utils import timezone


@login_required
def dashboard(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    antall_kontoer = Konto.objects.filter(organisasjon=organisasjon).count()
    antall_bilag = Bilag.objects.filter(organisasjon=organisasjon).count()
    antall_avdelinger = Avdeling.objects.filter(organisasjon=organisasjon).count()
    antall_prosjekter = Prosjekt.objects.filter(organisasjon=organisasjon).count()
    antall_styrekoder = Styrekode.objects.filter(
        organisasjon=organisasjon
    ).count()

    return render(
        request,
        "regnskap/dashboard.html",
        {
            "organisasjon": organisasjon,
            "antall_kontoer": antall_kontoer,
            "antall_bilag": antall_bilag,
            "antall_avdelinger": antall_avdelinger,
            "antall_prosjekter": antall_prosjekter,
            "antall_styrekoder": antall_styrekoder,
        }
    )

@login_required
def faste_data(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    har_kontoer = Konto.objects.filter(
        organisasjon=organisasjon
    ).exists()

    return render(
        request,
        "regnskap/faste_data.html",
        {
            "organisasjon": organisasjon,
            "har_kontoer": har_kontoer,
        }
    )

@login_required
def kontoplan(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon
    ).order_by("kontonummer")

    return render(
        request,
        "regnskap/kontoplan.html",
        {
            "organisasjon": organisasjon,
            "kontoer": kontoer,
        }
    )

@login_required
def avdelinger(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    avdelinger = Avdeling.objects.filter(
        organisasjon=organisasjon
    )

    return render(
        request,
        "regnskap/avdelinger.html",
        {
            "organisasjon": organisasjon,
            "avdelinger": avdelinger,
        }
    )


@login_required
def styrekoder(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    styrekoder = Styrekode.objects.filter(
        organisasjon=organisasjon
    ).order_by("kode")

    return render(
        request,
        "regnskap/styrekoder.html",
        {
            "organisasjon": organisasjon,
            "styrekoder": styrekoder,
        }
    )

def opprett_standard_startdata(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Fant ikke organisasjon for innlogget bruker.")
        return redirect("regnskap:faste_data")

    if Konto.objects.filter(organisasjon=organisasjon).exists():
        messages.warning(request, "Regnskapet har allerede kontoer.")
        return redirect("regnskap:faste_data")

    opprett_standard_regnskap(organisasjon)

    messages.success(request, "Standard startdata er opprettet.")
    return redirect("regnskap:faste_data")

@login_required
def styrekode_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Fant ikke organisasjon for innlogget bruker.")
        return redirect("regnskap:faste_data")

    if request.method == "POST":
        kode = request.POST.get("kode", "").strip()
        fortekst = request.POST.get("fortekst", "").strip()
        sumtekst = request.POST.get("sumtekst", "").strip()
        aktiv = request.POST.get("aktiv") == "on"

        if kode and fortekst:
            Styrekode.objects.create(
                organisasjon=organisasjon,
                kode=kode,
                fortekst=fortekst,
                sumtekst=sumtekst,
                aktiv=aktiv,
            )
            return redirect("regnskap:styrekoder")

    return render(
        request,
        "regnskap/styrekode_skjema.html",
        {
            "organisasjon": organisasjon,
        }
    )

@login_required
def styrekode_endre(request, styrekode_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    styrekode = get_object_or_404(
        Styrekode,
        id=styrekode_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":

        styrekode.kode = request.POST.get(
            "kode", ""
        ).strip()

        styrekode.fortekst = request.POST.get(
            "fortekst", ""
        ).strip()

        styrekode.sumtekst = request.POST.get(
            "sumtekst", ""
        ).strip()

        styrekode.aktiv = (
            request.POST.get("aktiv") == "on"
        )

        styrekode.save()

        return redirect("regnskap:styrekoder")

    return render(
        request,
        "regnskap/styrekode_skjema.html",
        {
            "organisasjon": organisasjon,
            "styrekode": styrekode,
        }
    )

@login_required
def styrekode_slett(request, styrekode_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    styrekode = get_object_or_404(
        Styrekode,
        id=styrekode_id,
        organisasjon=organisasjon,
    )

    # Sperre: ikke slett hvis konto bruker denne styrekoden direkte
    konto_i_bruk = Konto.objects.filter(
        organisasjon=organisasjon,
        styrekode=styrekode.kode,
    ).exists()

    if konto_i_bruk:
        messages.error(
            request,
            "Styrekoden kan ikke slettes fordi den er brukt på en konto."
        )
        return redirect("regnskap:styrekoder")

    if request.method == "POST":
        styrekode.delete()
        return redirect("regnskap:styrekoder")

    return render(
        request,
        "regnskap/styrekode_slett.html",
        {
            "organisasjon": organisasjon,
            "styrekode": styrekode,
        }
    )

@login_required
def avdeling_ny(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if request.method == "POST":
        avdelingsnummer = request.POST.get("avdelingsnummer", "").strip()
        navn = request.POST.get("navn", "").strip()
        aktiv = request.POST.get("aktiv") == "on"

        if avdelingsnummer and navn:
            Avdeling.objects.create(
                organisasjon=organisasjon,
                avdelingsnummer=avdelingsnummer,
                navn=navn,
                aktiv=aktiv,
            )

            return redirect("regnskap:avdelinger")

    return render(
        request,
        "regnskap/avdeling_skjema.html",
        {
            "organisasjon": organisasjon,
        }
    )

@login_required
def avdeling_endre(request, avdeling_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    avdeling = get_object_or_404(
        Avdeling,
        id=avdeling_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":

        avdeling.avdelingsnummer = request.POST.get(
            "avdelingsnummer", ""
        ).strip()

        avdeling.navn = request.POST.get(
            "navn", ""
        ).strip()

        avdeling.aktiv = (
            request.POST.get("aktiv") == "on"
        )

        avdeling.save()

        return redirect("regnskap:avdelinger")

    return render(
        request,
        "regnskap/avdeling_skjema.html",
        {
            "organisasjon": organisasjon,
            "avdeling": avdeling,
        }
    )

@login_required
def avdeling_slett(request, avdeling_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    avdeling = get_object_or_404(
        Avdeling,
        id=avdeling_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        avdeling.delete()
        return redirect("regnskap:avdelinger")

    return render(
        request,
        "regnskap/avdeling_slett.html",
        {
            "organisasjon": organisasjon,
            "avdeling": avdeling,
        }
    )

@login_required
def prosjekter(request):
    organisasjon = Organisasjon.objects.filter(redaktorer=request.user).first()

    prosjekter = Prosjekt.objects.filter(
        organisasjon=organisasjon
    )

    return render(request, "regnskap/prosjekter.html", {
        "organisasjon": organisasjon,
        "prosjekter": prosjekter,
    })


@login_required
def prosjekt_ny(request):
    organisasjon = Organisasjon.objects.filter(redaktorer=request.user).first()

    if request.method == "POST":
        prosjektnummer = request.POST.get("prosjektnummer", "").strip()
        navn = request.POST.get("navn", "").strip()
        beskrivelse = request.POST.get("beskrivelse", "").strip()
        aktiv = request.POST.get("aktiv") == "on"

        if prosjektnummer and navn:
            Prosjekt.objects.create(
                organisasjon=organisasjon,
                prosjektnummer=prosjektnummer,
                navn=navn,
                beskrivelse=beskrivelse,
                aktiv=aktiv,
            )
            return redirect("regnskap:prosjekter")

    return render(request, "regnskap/prosjekt_skjema.html", {
        "organisasjon": organisasjon,
    })


@login_required
def prosjekt_endre(request, prosjekt_id):
    organisasjon = Organisasjon.objects.filter(redaktorer=request.user).first()

    prosjekt = get_object_or_404(
        Prosjekt,
        id=prosjekt_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        prosjekt.prosjektnummer = request.POST.get("prosjektnummer", "").strip()
        prosjekt.navn = request.POST.get("navn", "").strip()
        prosjekt.beskrivelse = request.POST.get("beskrivelse", "").strip()
        prosjekt.aktiv = request.POST.get("aktiv") == "on"
        prosjekt.save()

        return redirect("regnskap:prosjekter")

    return render(request, "regnskap/prosjekt_skjema.html", {
        "organisasjon": organisasjon,
        "prosjekt": prosjekt,
    })


@login_required
def prosjekt_slett(request, prosjekt_id):
    organisasjon = Organisasjon.objects.filter(redaktorer=request.user).first()

    prosjekt = get_object_or_404(
        Prosjekt,
        id=prosjekt_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        prosjekt.delete()
        return redirect("regnskap:prosjekter")

    return render(request, "regnskap/prosjekt_slett.html", {
        "organisasjon": organisasjon,
        "prosjekt": prosjekt,
    })

@login_required
def bilagsserier(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    regnskapsaar_liste = Regnskapsaar.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
        avsluttet=False,
    ).order_by("aar")

    valgt_aar_id = request.GET.get("aar")

    if valgt_aar_id:
        regnskapsaar = regnskapsaar_liste.filter(
            id=valgt_aar_id
        ).first()
    else:
        regnskapsaar = regnskapsaar_liste.first()

    bilagsserier = Bilagsserie.objects.none()

    if regnskapsaar:
        bilagsserier = Bilagsserie.objects.filter(
            organisasjon=organisasjon,
            regnskapsaar=regnskapsaar,
        )

    return render(
        request,
        "regnskap/bilagsserier.html",
        {
            "organisasjon": organisasjon,
            "regnskapsaar": regnskapsaar,
            "regnskapsaar_liste": regnskapsaar_liste,
            "bilagsserier": bilagsserier,
        }
    )


@login_required
def regnskapsaar(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    aar = Regnskapsaar.objects.filter(
        organisasjon=organisasjon
    )

    return render(
        request,
        "regnskap/regnskapsaar.html",
        {
            "organisasjon": organisasjon,
            "regnskapsaar_liste": aar,
        }
    )

@login_required
def regnskapsaar_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if request.method == "POST":
        aar = request.POST.get("aar", "").strip()
        fra_dato = request.POST.get("fra_dato", "").strip()
        til_dato = request.POST.get("til_dato", "").strip()
        aktiv = request.POST.get("aktiv") == "on"
        avsluttet = request.POST.get("avsluttet") == "on"

        if aar and fra_dato and til_dato:
            Regnskapsaar.objects.create(
                organisasjon=organisasjon,
                aar=aar,
                fra_dato=fra_dato,
                til_dato=til_dato,
                aktiv=aktiv,
                avsluttet=avsluttet,
            )
            return redirect("regnskap:regnskapsaar")

    return render(
        request,
        "regnskap/regnskapsaar_skjema.html",
        {
            "organisasjon": organisasjon,
        }
    )

@login_required
def regnskapsaar_endre(request, regnskapsaar_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    regnskapsaar = get_object_or_404(
        Regnskapsaar,
        id=regnskapsaar_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        regnskapsaar.aar = request.POST.get("aar", "").strip()
        regnskapsaar.navn = request.POST.get("navn", "").strip()
        regnskapsaar.fra_dato = request.POST.get("fra_dato", "").strip()
        regnskapsaar.til_dato = request.POST.get("til_dato", "").strip()
        regnskapsaar.aktiv = request.POST.get("aktiv") == "on"
        regnskapsaar.avsluttet = request.POST.get("avsluttet") == "on"

        regnskapsaar.save()

        return redirect("regnskap:regnskapsaar")

    return render(
        request,
        "regnskap/regnskapsaar_skjema.html",
        {
            "organisasjon": organisasjon,
            "regnskapsaar": regnskapsaar,
        }
    )

@login_required
def bilagsserie_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    aar_id = request.GET.get("aar")

    if aar_id:
        regnskapsaar = get_object_or_404(
            Regnskapsaar,
            id=aar_id,
            organisasjon=organisasjon,
        )
    else:
        regnskapsaar = Regnskapsaar.objects.filter(
            organisasjon=organisasjon,
            aktiv=True,
            avsluttet=False,
        ).order_by("aar").first()

    if not regnskapsaar:
        return redirect("regnskap:bilagsserier")

    if request.method == "POST":
        print("POST:", request.POST)
        regnskapsaar_id = request.POST.get("regnskapsaar_id")

        regnskapsaar = get_object_or_404(
            Regnskapsaar,
            id=regnskapsaar_id,
            organisasjon=organisasjon,
        )
        kode = request.POST.get("kode", "").strip()
        navn = request.POST.get("navn", "").strip()
        neste_nummer = request.POST.get("neste_nummer", "1").strip()
        standard_konto = request.POST.get("standard_konto", "").strip() or None
        standard_fortegn = request.POST.get("standard_fortegn", "").strip()
        aktiv = request.POST.get("aktiv") == "on"

        if kode and navn:
            Bilagsserie.objects.create(
                organisasjon=organisasjon,
                regnskapsaar=regnskapsaar,
                kode=kode,
                navn=navn,
                neste_nummer=neste_nummer,
                standard_konto=standard_konto,
                standard_fortegn=standard_fortegn,
                aktiv=aktiv,
            )
            return redirect("regnskap:bilagsserier")

    return render(request, "regnskap/bilagsserie_skjema.html", {
        "organisasjon": organisasjon,
        "regnskapsaar": regnskapsaar,
    })

@login_required
def bilagsserie_endre(request, bilagsserie_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    bilagsserie = get_object_or_404(
        Bilagsserie,
        id=bilagsserie_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        bilagsserie.kode = request.POST.get("kode", "").strip()
        bilagsserie.navn = request.POST.get("navn", "").strip()
        bilagsserie.neste_nummer = request.POST.get("neste_nummer", "1").strip()
        bilagsserie.standard_konto = request.POST.get("standard_konto", "").strip() or None
        bilagsserie.standard_fortegn = request.POST.get("standard_fortegn", "").strip()
        bilagsserie.aktiv = request.POST.get("aktiv") == "on"

        bilagsserie.save()

        return redirect(
            f"{reverse('regnskap:bilagsserier')}?aar={bilagsserie.regnskapsaar.id}"
        )

    return render(request, "regnskap/bilagsserie_skjema.html", {
        "organisasjon": organisasjon,
        "regnskapsaar": bilagsserie.regnskapsaar,
        "bilagsserie": bilagsserie,
    })

@login_required
def bilagsserie_slett(request, bilagsserie_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    bilagsserie = get_object_or_404(
        Bilagsserie,
        id=bilagsserie_id,
        organisasjon=organisasjon,
    )

    regnskapsaar_id = bilagsserie.regnskapsaar.id

    if request.method == "POST":
        bilagsserie.delete()
        return redirect(
            f"{reverse('regnskap:bilagsserier')}?aar={regnskapsaar_id}"
        )

    return render(request, "regnskap/bilagsserie_slett.html", {
        "organisasjon": organisasjon,
        "regnskapsaar": bilagsserie.regnskapsaar,
        "bilagsserie": bilagsserie,
    })

@login_required
def bilag_liste(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    regnskapsaar_liste = Regnskapsaar.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
        avsluttet=False,
    ).order_by("aar")

    valgt_aar_id = request.GET.get("aar")

    if valgt_aar_id:
        regnskapsaar = regnskapsaar_liste.filter(
            id=valgt_aar_id
        ).first()
    else:
        regnskapsaar = regnskapsaar_liste.first()

    bilag = Bilag.objects.none()

    if regnskapsaar:
        bilag = Bilag.objects.filter(
            organisasjon=organisasjon,
            regnskapsaar=regnskapsaar,
        ).order_by("bilagsserie__kode", "bilagsnummer")

    return render(
        request,
        "regnskap/bilag_liste.html",
        {
            "organisasjon": organisasjon,
            "regnskapsaar": regnskapsaar,
            "regnskapsaar_liste": regnskapsaar_liste,
            "bilag": bilag,
        }
    )

@login_required
def bilag_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    regnskapsaar_liste = Regnskapsaar.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
        avsluttet=False,
    ).order_by("aar")

    valgt_aar_id = request.GET.get("aar") or request.POST.get("regnskapsaar_id")

    if valgt_aar_id:
        regnskapsaar = regnskapsaar_liste.filter(id=valgt_aar_id).first()
    else:
        regnskapsaar = regnskapsaar_liste.first()

    if not regnskapsaar:
        return redirect("regnskap:bilag_liste")

    bilagsserier = Bilagsserie.objects.filter(
        organisasjon=organisasjon,
        regnskapsaar=regnskapsaar,
        aktiv=True,
    ).order_by("kode")

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon
    ).order_by("kontonummer")

    if request.method == "POST":
        bilagsserie_id = request.POST.get("bilagsserie")
        bilagsdato = request.POST.get("bilagsdato")
        foringsdato = request.POST.get("foringsdato")
        bilagstekst = request.POST.get("bilagstekst", "").strip()

        bilagsserie = get_object_or_404(
            Bilagsserie,
            id=bilagsserie_id,
            organisasjon=organisasjon,
            regnskapsaar=regnskapsaar,
        )

        with transaction.atomic():
            bilagsnummer = bilagsserie.neste_nummer
            bilagsserie.neste_nummer += 1
            bilagsserie.save()

            bilag = Bilag.objects.create(
                organisasjon=organisasjon,
                regnskapsaar=regnskapsaar,
                bilagsserie=bilagsserie,
                bilagsnummer=bilagsnummer,
                bilagsdato=bilagsdato,
                foringsdato=foringsdato,
                bilagstekst=bilagstekst,
                registrert_av=request.user,
            )

            for linjenr in [1, 2]:
                konto = request.POST.get(f"konto_{linjenr}")
                tekst = request.POST.get(f"tekst_{linjenr}", "").strip()
                belop = request.POST.get(f"belop_{linjenr}", "").strip()

                if konto and belop:
                    Bilagslinje.objects.create(
                        bilag=bilag,
                        linjenummer=linjenr,
                        kontonummer=konto,
                        linjetekst=tekst,
                        belop=Decimal(belop),
                    )

        return redirect(
            f"{reverse('regnskap:bilag_liste')}?aar={regnskapsaar.id}"
        )

    dagens_dato = timezone.localdate()

    return render(request, "regnskap/bilag_skjema.html", {
        "organisasjon": organisasjon,
        "regnskapsaar": regnskapsaar,
        "bilagsserier": bilagsserier,
        "kontoer": kontoer,
        "dagens_dato": dagens_dato,
        "dagens_dato_iso": dagens_dato.isoformat(),
    })

