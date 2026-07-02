from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from lag.models import Organisasjon, LagMedlem
from .models import Konto, Bilag, Bilagslinje, Avdeling, Prosjekt, Styrekode, Regnskapsaar, SamlekontoType, Bilagsserie, Leverandor, Kunde
from .services import opprett_standard_regnskap
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
import json
import requests
from .medlem_synkronisering import (
    analyser_medlemssynkronisering,
    tildel_medlemsnummer,
    opprett_medlemskontoer,
)

def konto_kan_foeres_paa(konto):
    if konto.samlekonto:
        return False
    return True

def bilag_kan_endres(bilag):
    return bilag.h_status == Bilag.STATUS_REGISTRERT


def bilag_kan_slettes(bilag):
    return bilag.h_status == Bilag.STATUS_REGISTRERT


def bilag_kan_tilbakefores(bilag):
    return bilag.h_status >= Bilag.STATUS_REGISTRERT


def bygg_bilag_context(
    organisasjon,
    bilag,
    modus,
    kan_endre,
    regnskapsaar,
    bilagsserier,
    kontoer,
    kontonavn_json,
    avdelinger,
    prosjekter,
    valgt_serie_id=None,
    linje1=None,
    linje2=None,
    linje3=None,
    linje4=None,
    linje5=None,
    linje6=None,
    feil_linje=None,
):

    dagens_dato = timezone.localdate()

    linjer = []

    if bilag and linje1 is None:
        linjer = list(
            bilag.linjer.all().order_by("linjenummer")
        )

        linje1 = linjer[0] if len(linjer) > 0 else None
        linje2 = linjer[1] if len(linjer) > 1 else None
        linje3 = linjer[2] if len(linjer) > 2 else None
        linje4 = linjer[3] if len(linjer) > 3 else None
        linje5 = linjer[4] if len(linjer) > 4 else None
        linje6 = linjer[5] if len(linjer) > 5 else None

    return {
        "organisasjon": organisasjon,
        "bilag": bilag,
        "modus": modus,
        "kan_endre": kan_endre,
        "regnskapsaar": regnskapsaar,
        "bilagsserier": bilagsserier,
        "kontoer": kontoer,
        "dagens_dato": bilag.bilagsdato if bilag else dagens_dato,
        "dagens_dato_iso": bilag.bilagsdato.isoformat() if bilag else dagens_dato.isoformat(),
        "foringsdato_iso": bilag.foringsdato.isoformat() if bilag else dagens_dato.isoformat(),
        "kontonavn_json": kontonavn_json,
        "avdelinger": avdelinger,
        "prosjekter": prosjekter,
        "valgt_serie_id": valgt_serie_id,
        "linjer": linjer,
        "linje1": linje1,
        "linje2": linje2,
        "linje3": linje3,
        "linje4": linje4,
        "linje5": linje5,
        "linje6": linje6,
        "feil_linje": feil_linje,
    }

@login_required

def tilbakefor_bilag(request, bilag):
    if bilag.h_status == Bilag.STATUS_REGISTRERT:
        siste_linje = (
            bilag.linjer
            .order_by("-linjenummer")
            .first()
        )

        neste_linje = 1
        if siste_linje:
            neste_linje = siste_linje.linjenummer + 1

        with transaction.atomic():
            for linje in bilag.linjer.all().order_by("linjenummer"):
                Bilagslinje.objects.create(
                    bilag=bilag,
                    linjenummer=neste_linje,
                    kontonummer=linje.kontonummer,
                    avdeling=linje.avdeling,
                    prosjekt=linje.prosjekt,
                    momskode=linje.momskode,
                    linjetekst=f"Tilbakeføring av linje {linje.linjenummer}",
                    belop=-linje.belop,
                )
                neste_linje += 1

            bilag.h_status = Bilag.STATUS_SLETTET
            bilag.bilagstekst = f"Tilbakeført: {bilag.bilagstekst}"
            bilag.save()

        messages.success(
            request,
            f"Bilag {bilag} er tilbakeført."
        )

        return redirect("regnskap:bilag_detalj", bilag_id=bilag.id)

    messages.error(
        request,
        "Tilbakeføring av oppdatert bilag kommer i neste steg."
    )
    return redirect("regnskap:bilag_detalj", bilag_id=bilag.id)

def bilag_skjema(request, bilag_id=None, modus="ny"):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    bilag = None

    if bilag_id:
        bilag = get_object_or_404(
            Bilag,
            id=bilag_id,
            organisasjon=organisasjon,
        )

        if modus == "ny":
            modus = "endre"

        if modus != "tilbakeforing" and bilag.h_status != Bilag.STATUS_REGISTRERT:
            modus = "vis"


    regnskapsaar_liste = Regnskapsaar.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
        avsluttet=False,
    ).order_by("aar")

    valgt_aar_id = request.GET.get("aar") or request.POST.get("regnskapsaar_id")
    valgt_serie_id = request.GET.get("serie")

    if valgt_aar_id:
        regnskapsaar = regnskapsaar_liste.filter(id=valgt_aar_id).first()
    else:
        regnskapsaar = regnskapsaar_liste.first()
    if bilag:
        regnskapsaar = bilag.regnskapsaar

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

    avdelinger = Avdeling.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("avdelingsnummer")

    prosjekter = Prosjekt.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("prosjektnummer")

    kontonavn_json = json.dumps({
        str(k.kontonummer): {
            "navn": k.kontonavn,
            "samlekonto": k.samlekonto,
            "krever_avdeling": k.krever_avdeling,
            "krever_prosjekt": k.krever_prosjekt,
        }
        for k in kontoer
    })

    linjer = []
    linje1 = linje2 = linje3 = linje4 = linje5 = linje6 = None

    if bilag:
        linjer = list(
            bilag.linjer.all().order_by("linjenummer")
        )

        linje1 = linjer[0] if len(linjer) > 0 else None
        linje2 = linjer[1] if len(linjer) > 1 else None
        linje3 = linjer[2] if len(linjer) > 2 else None
        linje4 = linjer[3] if len(linjer) > 3 else None
        linje5 = linjer[4] if len(linjer) > 4 else None
        linje6 = linjer[5] if len(linjer) > 5 else None

    if request.method == "POST" and modus == "tilbakeforing":
        return tilbakefor_bilag(request, bilag)

    if request.method == "POST" and modus == "endre" and bilag.h_status == Bilag.STATUS_REGISTRERT:
        nye_linjer = []

        konto_liste = request.POST.getlist("konto[]")
        tekst_liste = request.POST.getlist("tekst[]")
        belop_liste = request.POST.getlist("belop[]")
        avdeling_liste = request.POST.getlist("avdeling[]")
        prosjekt_liste = request.POST.getlist("prosjekt[]")

        antall_linjer = max(
            len(konto_liste),
            len(tekst_liste),
            len(belop_liste),
            len(avdeling_liste),
            len(prosjekt_liste),
        )

        for i in range(antall_linjer):
            linjenr = i + 1

            konto = konto_liste[i].strip() if i < len(konto_liste) else ""
            tekst = tekst_liste[i].strip() if i < len(tekst_liste) else ""
            belop = belop_liste[i].strip() if i < len(belop_liste) else ""
            avdeling_id = avdeling_liste[i] if i < len(avdeling_liste) and avdeling_liste[i] else None
            prosjekt_id = prosjekt_liste[i] if i < len(prosjekt_liste) and prosjekt_liste[i] else None

            if konto and belop:
                konto_obj = Konto.objects.filter(
                    organisasjon=organisasjon,
                    kontonummer=konto,
                ).first()

                if not konto_obj:
                    messages.error(
                        request,
                        f"Konto {konto} på linje {linjenr} finnes ikke i kontoplanen."
                    )

                    return render(
                        request,
                        "regnskap/bilag_skjema.html",
                        bygg_bilag_context(
                            organisasjon=organisasjon,
                            bilag=bilag,
                            modus=modus,
                            kan_endre=True,
                            regnskapsaar=regnskapsaar,
                            bilagsserier=bilagsserier,
                            kontoer=kontoer,
                            kontonavn_json=kontonavn_json,
                            avdelinger=avdelinger,
                            prosjekter=prosjekter,
                            valgt_serie_id=valgt_serie_id,
                        )
                    )

                if not konto_kan_foeres_paa(konto_obj):
                    messages.error(
                        request,
                        f"Konto {konto_obj.kontonummer} {konto_obj.kontonavn} er samlekonto og kan ikke føres på."
                    )

                    return render(
                        request,
                        "regnskap/bilag_skjema.html",
                        bygg_bilag_context(
                            organisasjon=organisasjon,
                            bilag=bilag,
                            modus=modus,
                            kan_endre=True,
                            regnskapsaar=bilag.regnskapsaar,
                            bilagsserier=bilagsserier,
                            kontoer=kontoer,
                            kontonavn_json=kontonavn_json,
                            avdelinger=avdelinger,
                            prosjekter=prosjekter,
                            valgt_serie_id=valgt_serie_id,
                            feil_linje=str(linjenr),
                        )
                    )


                nye_linjer.append(
                    (
                        linjenr,
                        konto,
                        tekst,
                        belop,
                        avdeling_id,
                        prosjekt_id,
                    )
                )

        bilag.bilagsdato = request.POST.get("bilagsdato")
        bilag.foringsdato = request.POST.get("foringsdato")
        bilag.bilagstekst = request.POST.get("bilagstekst", "").strip()
        bilag.save()

        bilag.linjer.all().delete()

        for linjenr, konto, tekst, belop, avdeling_id, prosjekt_id in nye_linjer:
            Bilagslinje.objects.create(
                bilag=bilag,
                linjenummer=linjenr,
                kontonummer=konto,
                avdeling_id=avdeling_id,
                prosjekt_id=prosjekt_id,
                linjetekst=tekst,
                belop=Decimal(belop.replace(",", ".")),
            )

        return redirect("regnskap:bilag_detalj", bilag_id=bilag.id)

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

            konto_liste = request.POST.getlist("konto[]")
            tekst_liste = request.POST.getlist("tekst[]")
            belop_liste = request.POST.getlist("belop[]")
            avdeling_liste = request.POST.getlist("avdeling[]")
            prosjekt_liste = request.POST.getlist("prosjekt[]")

            antall_linjer = max(
                len(konto_liste),
                len(tekst_liste),
                len(belop_liste),
                len(avdeling_liste),
                len(prosjekt_liste),
            )

            lagrede_linjer = 0

            for i in range(antall_linjer):
                linjenr = i + 1

                konto = konto_liste[i].strip() if i < len(konto_liste) else ""
                tekst = tekst_liste[i].strip() if i < len(tekst_liste) else ""
                belop = belop_liste[i].strip() if i < len(belop_liste) else ""
                avdeling_id = avdeling_liste[i] if i < len(avdeling_liste) and avdeling_liste[i] else None
                prosjekt_id = prosjekt_liste[i] if i < len(prosjekt_liste) and prosjekt_liste[i] else None

                if konto and belop:
                    konto_obj = Konto.objects.filter(
                        organisasjon=organisasjon,
                        kontonummer=konto,
                    ).first()

                    if not konto_obj:
                        raise ValueError(f"Konto {konto} finnes ikke i kontoplanen.")

                    if not konto_kan_foeres_paa(konto_obj):
                        messages.error(
                            request,
                            f"Konto {konto_obj.kontonummer} {konto_obj.kontonavn} er samlekonto og kan ikke føres på."
                        )
                        return render(request, "regnskap/bilag_skjema.html", {
                            "organisasjon": organisasjon,
                            "bilag": bilag,
                            "modus": modus,
                            "kan_endre": True,
                            "regnskapsaar": regnskapsaar,
                            "bilagsserier": bilagsserier,
                            "kontoer": kontoer,
                            "dagens_dato": bilag.bilagsdato if bilag else dagens_dato,
                            "dagens_dato_iso": bilag.bilagsdato.isoformat() if bilag else dagens_dato.isoformat(),
                            "foringsdato_iso": bilag.foringsdato.isoformat() if bilag else dagens_dato.isoformat(),
                            "kontonavn_json": kontonavn_json,
                            "avdelinger": avdelinger,
                            "prosjekter": prosjekter,
                            "valgt_serie_id": valgt_serie_id,
                            "linjer": linjer,
                            "linje1": linje1,
                            "linje2": linje2,
                            "linje3": linje3,
                            "linje4": linje4,
                            "linje5": linje5,
                            "linje6": linje6,
                        })

                    Bilagslinje.objects.create(
                        bilag=bilag,
                        linjenummer=linjenr,
                        kontonummer=konto,
                        avdeling_id=avdeling_id,
                        prosjekt_id=prosjekt_id,
                        linjetekst=tekst,
                        belop=Decimal(belop.replace(",", ".")),
                    )
                    lagrede_linjer += 1

            if lagrede_linjer == 0:
                raise ValueError(
                    "Bilaget har ingen bilagslinjer og kan ikke lagres."
                )
        messages.success(
            request,
            f"Bilag {bilagsserie.kode}{bilagsnummer} er lagret."
        )

        return redirect(
            f"{reverse('regnskap:bilag_ny')}?aar={regnskapsaar.id}&serie={bilagsserie.id}"
        )


    return render(
        request,
        "regnskap/bilag_skjema.html",
        bygg_bilag_context(
            organisasjon=organisasjon,
            bilag=bilag,
            modus=modus,
            kan_endre=True,
            regnskapsaar=regnskapsaar,
            bilagsserier=bilagsserier,
            kontoer=kontoer,
            kontonavn_json=kontonavn_json,
            avdelinger=avdelinger,
            prosjekter=prosjekter,
            valgt_serie_id=valgt_serie_id,
        )
    )

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


    sum_debet = Decimal("0")
    sum_kredit = Decimal("0")
    omsetning = Decimal("0")
    kostnader = Decimal("0")

    linjer = Bilagslinje.objects.filter(
        bilag__organisasjon=organisasjon
    )

    for linje in linjer:
        if linje.belop > 0:
            sum_debet += linje.belop
        else:
            sum_kredit += linje.belop

        if 300 <= linje.kontonummer <= 399:
            omsetning += linje.belop

        if 400 <= linje.kontonummer <= 999:
            kostnader += linje.belop

    differanse = sum_debet + sum_kredit
    resultat = omsetning + kostnader

    return render (
        request,
        "regnskap/dashboard.html",
        {
            "organisasjon": organisasjon,
            "antall_kontoer": antall_kontoer,
            "antall_bilag": antall_bilag,
            "antall_avdelinger": antall_avdelinger,
            "antall_prosjekter": antall_prosjekter,
            "antall_styrekoder": antall_styrekoder,
            "sum_debet": sum_debet,
            "sum_kredit": sum_kredit,
            "differanse": differanse,
            "omsetning": omsetning,
            "kostnader": kostnader,
            "resultat": resultat,

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

    oppslag = request.GET.get("oppslag") == "1"

    fra = request.GET.get("fra", "0")
    til = request.GET.get("til", "10000")

    try:
        fra_int = int(fra)
    except ValueError:
        fra_int = 0

    try:
        til_int = int(til)
    except ValueError:
        til_int = 10000

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon,
        kontonummer__gte=fra_int,
        kontonummer__lte=til_int,
    ).order_by("kontonummer")

    return render(
        request,
        "regnskap/kontoplan.html",
        {
            "organisasjon": organisasjon,
            "kontoer": kontoer,
            "oppslag": oppslag,
            "fra": fra_int,
            "til": til_int,
        }
    )

@login_required
def konto_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if request.method == "POST":
        Konto.objects.create(
            organisasjon=organisasjon,
            kontonummer=request.POST.get("kontonummer"),
            kontonavn=request.POST.get("kontonavn"),
            styrekode=request.POST.get("styrekode"),
            samlekonto=request.POST.get("samlekonto") == "on",
            krever_avdeling=request.POST.get("krever_avdeling") == "on",
            krever_prosjekt=request.POST.get("krever_prosjekt") == "on",
            aktiv=request.POST.get("aktiv") == "on",
        )

        return redirect("regnskap:kontoplan")

    return render(
        request,
        "regnskap/konto_skjema.html",
        {
            "organisasjon": organisasjon,
        }
    )


@login_required
def konto_endre(request, konto_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    konto = get_object_or_404(
        Konto,
        id=konto_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        konto.kontonummer = request.POST.get("kontonummer", "").strip()
        konto.kontonavn = request.POST.get("kontonavn", "").strip()
        konto.styrekode = request.POST.get("styrekode", "").strip()
        konto.samlekonto = request.POST.get("samlekonto") == "on"
        konto.krever_avdeling = request.POST.get("krever_avdeling") == "on"
        konto.krever_prosjekt = request.POST.get("krever_prosjekt") == "on"
        konto.aktiv = request.POST.get("aktiv") == "on"
        konto.save()

        return redirect("regnskap:kontoplan")

    return render(request, "regnskap/konto_skjema.html", {
        "organisasjon": organisasjon,
        "konto": konto,
    })

@login_required
def konto_slett(request, konto_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    konto = get_object_or_404(
        Konto,
        id=konto_id,
        organisasjon=organisasjon,
    )

    brukt_i_bilag = Bilagslinje.objects.filter(
        bilag__organisasjon=organisasjon,
        kontonummer=konto.kontonummer,
    ).exists()

    if brukt_i_bilag:
        return render(request, "regnskap/konto_slett.html", {
            "organisasjon": organisasjon,
            "konto": konto,
            "feilmelding": "Kontoen er brukt i bilag og kan ikke slettes. Sett den inaktiv i stedet.",
        })

    if request.method == "POST":
        konto.delete()
        return redirect("regnskap:kontoplan")

    return render(request, "regnskap/konto_slett.html", {
        "organisasjon": organisasjon,
        "konto": konto,
    })

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
def samlekontotyper(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    samlekontotyper = SamlekontoType.objects.filter(
        hovedbokskonto__organisasjon=organisasjon
    ).select_related("hovedbokskonto").order_by(
        "hovedbokskonto__kontonummer"
    )

    return render(
        request,
        "regnskap/samlekontotyper.html",
        {
            "organisasjon": organisasjon,
            "samlekontotyper": samlekontotyper,
        }
    )


@login_required
def samlekontotype_ny(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("kontonummer")

    if request.method == "POST":
        hovedbokskonto_id = request.POST.get("hovedbokskonto")
        navn = request.POST.get("navn", "").strip()
        beskrivelse = request.POST.get("beskrivelse", "").strip()
        bruker_lopende_nummer = request.POST.get("bruker_lopende_nummer") == "on"
        aktiv = request.POST.get("aktiv") == "on"

        nummer_fra = int(request.POST.get("nummer_fra") or 1)
        nummer_til = int(request.POST.get("nummer_til") or 999999)
        neste_nummer = int(request.POST.get("neste_nummer") or nummer_fra)

        feilmelding = None
        hovedbokskonto = None

        if not hovedbokskonto_id:
            feilmelding = "Du må velge hovedbokskonto."

        elif not navn:
            feilmelding = "Du må registrere navn."

        else:
            hovedbokskonto = get_object_or_404(
                Konto,
                id=hovedbokskonto_id,
                organisasjon=organisasjon,
            )

            if SamlekontoType.objects.filter(
                hovedbokskonto=hovedbokskonto
            ).exists():
                feilmelding = "Denne hovedbokskontoen er allerede brukt som samlekontotype."

            elif nummer_fra > nummer_til:
                feilmelding = "Nummer fra kan ikke være høyere enn nummer til."

            elif neste_nummer < nummer_fra or neste_nummer > nummer_til:
                feilmelding = "Neste nummer må ligge innenfor nummerintervallet."

            elif SamlekontoType.objects.filter(
                hovedbokskonto__organisasjon=organisasjon,
                nummer_fra__lte=nummer_til,
                nummer_til__gte=nummer_fra,
            ).exists():
                feilmelding = "Nummerintervallet kolliderer med en annen samlekontotype."

        if feilmelding:
            return render(
                request,
                "regnskap/samlekontotype_skjema.html",
                {
                    "organisasjon": organisasjon,
                    "samlekontotype": None,
                    "kontoer": kontoer,
                    "feilmelding": feilmelding,
                    "skjema": {
                        "hovedbokskonto_id": int(hovedbokskonto_id) if hovedbokskonto_id else "",
                        "navn": navn,
                        "nummer_fra": nummer_fra,
                        "nummer_til": nummer_til,
                        "neste_nummer": neste_nummer,
                        "beskrivelse": beskrivelse,
                        "bruker_lopende_nummer": bruker_lopende_nummer,
                        "aktiv": aktiv,
                    },
                },
            )

        SamlekontoType.objects.create(
            hovedbokskonto=hovedbokskonto,
            navn=navn,
            nummer_fra=nummer_fra,
            nummer_til=nummer_til,
            neste_nummer=neste_nummer,
            bruker_lopende_nummer=bruker_lopende_nummer,
            beskrivelse=beskrivelse,
            aktiv=aktiv,
        )

        return redirect("regnskap:samlekontotyper")

    return render(
        request,
        "regnskap/samlekontotype_skjema.html",
        {
            "organisasjon": organisasjon,
            "samlekontotype": None,
            "kontoer": kontoer,
        }
    )


@login_required
def samlekontotype_endre(request, samlekontotype_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    samlekontotype = get_object_or_404(
        SamlekontoType,
        id=samlekontotype_id,
        hovedbokskonto__organisasjon=organisasjon
    )
    kontoer = Konto.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("kontonummer")

    if request.method == "POST":
        hovedbokskonto_id = request.POST.get("hovedbokskonto")

        hovedbokskonto = get_object_or_404(
            Konto,
            id=hovedbokskonto_id,
            organisasjon=organisasjon,
        )

        navn = request.POST.get("navn", "").strip()
        nummer_fra = int(request.POST.get("nummer_fra") or 1)
        nummer_til = int(request.POST.get("nummer_til") or 999999)
        neste_nummer = int(request.POST.get("neste_nummer") or nummer_fra)
        beskrivelse = request.POST.get("beskrivelse", "").strip()
        bruker_lopende_nummer = (
            request.POST.get("bruker_lopende_nummer") == "on"
        )
        aktiv = request.POST.get("aktiv") == "on"

        feilmelding = None

        if not navn:
            feilmelding = "Du må registrere navn."

        elif nummer_fra > nummer_til:
            feilmelding = "Nummer fra kan ikke være høyere enn nummer til."

        elif neste_nummer < nummer_fra or neste_nummer > nummer_til:
            feilmelding = "Neste nummer må ligge innenfor nummerintervallet."

        elif SamlekontoType.objects.filter(
            hovedbokskonto__organisasjon=organisasjon,
            nummer_fra__lte=nummer_til,
            nummer_til__gte=nummer_fra,
        ).exclude(
            id=samlekontotype.id
        ).exists():
            feilmelding = "Nummerintervallet kolliderer med en annen samlekontotype."

        if feilmelding:
            return render(
                request,
                "regnskap/samlekontotype_skjema.html",
                {
                    "organisasjon": organisasjon,
                    "samlekontotype": samlekontotype,
                    "kontoer": kontoer,
                    "feilmelding": feilmelding,
                    "skjema": {
                        "hovedbokskonto_id": hovedbokskonto.id,
                        "navn": navn,
                        "nummer_fra": nummer_fra,
                        "nummer_til": nummer_til,
                        "neste_nummer": neste_nummer,
                        "beskrivelse": beskrivelse,
                        "bruker_lopende_nummer": bruker_lopende_nummer,
                        "aktiv": aktiv,
                    },
                },
            )

        samlekontotype.hovedbokskonto = hovedbokskonto
        samlekontotype.navn = navn
        samlekontotype.nummer_fra = nummer_fra
        samlekontotype.nummer_til = nummer_til
        samlekontotype.neste_nummer = neste_nummer
        samlekontotype.beskrivelse = beskrivelse
        samlekontotype.bruker_lopende_nummer = bruker_lopende_nummer
        samlekontotype.aktiv = aktiv
        samlekontotype.save()
        return redirect("regnskap:samlekontotyper")


    return render(
        request,
        "regnskap/samlekontotype_skjema.html",
        {
            "organisasjon": organisasjon,
            "samlekontotype": samlekontotype,
            "kontoer": kontoer,
        }
    )

@login_required
def samlekontotype_slett(request, samlekontotype_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    samlekontotype = get_object_or_404(
        SamlekontoType,
        id=samlekontotype_id,
        hovedbokskonto__organisasjon=organisasjon,
    )

    if request.method == "POST":
        konto = samlekontotype.hovedbokskonto

        samlekontotype.delete()

        konto.samlekonto = False
        konto.save(update_fields=["samlekonto"])

    return redirect("regnskap:samlekontotyper")


@login_required
def leverandorer(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    leverandorer = Leverandor.objects.filter(
        organisasjon=organisasjon
    ).select_related(
        "konto"
    ).order_by(
        "konto__kontonummer"
    )

    return render(
        request,
        "regnskap/leverandorer.html",
        {
            "organisasjon": organisasjon,
            "leverandorer": leverandorer,
        }
    )

@login_required
def leverandor_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    samlekontotyper = SamlekontoType.objects.filter(
        hovedbokskonto__organisasjon=organisasjon,
        aktiv=True,
    ).order_by("navn")

    if request.method == "POST":
        samlekontotype_id = request.POST.get("samlekontotype")
        navn = request.POST.get("navn", "").strip()

        samlekontotype = get_object_or_404(
            SamlekontoType,
            id=samlekontotype_id,
            hovedbokskonto__organisasjon=organisasjon,
        )

        kontonummer = samlekontotype.neste_nummer

        with transaction.atomic():
            konto = Konto.objects.create(
                organisasjon=organisasjon,
                kontonummer=kontonummer,
                kontonavn=navn,
                styrekode=samlekontotype.hovedbokskonto.styrekode,
                samlekonto=False,
                aktiv=True,
            )

            Leverandor.objects.create(
                organisasjon=organisasjon,
                konto=konto,
                navn=navn,
                orgnummer=request.POST.get("orgnummer", "").strip(),
                adresse=request.POST.get("adresse", "").strip(),
                postnummer=request.POST.get("postnummer", "").strip(),
                poststed=request.POST.get("poststed", "").strip(),
                land=request.POST.get("land", "").strip() or "Norge",
                kontaktperson=request.POST.get("kontaktperson", "").strip(),
                epost=request.POST.get("epost", "").strip(),
                url=request.POST.get("url", "").strip(),
                telefon=request.POST.get("telefon", "").strip(),
                bankkonto=request.POST.get("bankkonto", "").strip(),
                iban=request.POST.get("iban", "").strip(),
                bic=request.POST.get("bic", "").strip(),
                aktiv=request.POST.get("aktiv") == "on",
                notat=request.POST.get("notat", "").strip(),
            )

            samlekontotype.neste_nummer += 1
            samlekontotype.save(update_fields=["neste_nummer"])

        return redirect("regnskap:leverandorer")

    return render(
        request,
        "regnskap/leverandor_skjema.html",

        {
            "organisasjon": organisasjon,
            "leverandor": None,
            "samlekontotyper": samlekontotyper,
            "skjema": {
                "navn": request.GET.get("navn", ""),
                "orgnummer": request.GET.get("orgnummer", ""),
                "adresse": request.GET.get("adresse", ""),
                "postnummer": request.GET.get("postnummer", ""),
                "poststed": request.GET.get("poststed", ""),
                "land": request.GET.get("land", "Norge"),
            },
        }
    )

@login_required
def leverandor_endre(request, leverandor_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    leverandor = get_object_or_404(
        Leverandor,
        id=leverandor_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        leverandor.navn = request.POST.get("navn", "").strip()
        leverandor.orgnummer = request.POST.get("orgnummer", "").strip()
        leverandor.adresse = request.POST.get("adresse", "").strip()
        leverandor.postnummer = request.POST.get("postnummer", "").strip()
        leverandor.poststed = request.POST.get("poststed", "").strip()
        leverandor.land = request.POST.get("land", "").strip() or "Norge"
        leverandor.kontaktperson = request.POST.get("kontaktperson", "").strip()
        leverandor.epost = request.POST.get("epost", "").strip()
        leverandor.url = request.POST.get("url", "").strip()
        leverandor.telefon = request.POST.get("telefon", "").strip()
        leverandor.bankkonto = request.POST.get("bankkonto", "").strip()
        leverandor.iban = request.POST.get("iban", "").strip()
        leverandor.bic = request.POST.get("bic", "").strip()
        leverandor.aktiv = request.POST.get("aktiv") == "on"
        leverandor.notat = request.POST.get("notat", "").strip()
        leverandor.save()

        leverandor.konto.kontonavn = leverandor.navn
        leverandor.konto.aktiv = leverandor.aktiv
        leverandor.konto.save(update_fields=["kontonavn", "aktiv"])

        return redirect("regnskap:leverandorer")

    return render(
        request,
        "regnskap/leverandor_skjema.html",
        {
            "organisasjon": organisasjon,
            "leverandor": leverandor,
            "samlekontotyper": None,
            "skjema": {
                "navn": leverandor.navn,
                "orgnummer": leverandor.orgnummer,
                "adresse": leverandor.adresse,
                "postnummer": leverandor.postnummer,
                "poststed": leverandor.poststed,
                "land": leverandor.land,
                "kontaktperson": leverandor.kontaktperson,
                "epost": leverandor.epost,
                "url": leverandor.url,
                "telefon": leverandor.telefon,
                "bankkonto": leverandor.bankkonto,
                "iban": leverandor.iban,
                "bic": leverandor.bic,
                "aktiv": leverandor.aktiv,
                "notat": leverandor.notat,
            },
        }
    )


@login_required
def leverandor_slett(request, leverandor_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    leverandor = get_object_or_404(
        Leverandor,
        id=leverandor_id,
        organisasjon=organisasjon,
    )

    if request.method == "POST":
        leverandor.aktiv = False
        leverandor.save(update_fields=["aktiv"])

        leverandor.konto.aktiv = False
        leverandor.konto.save(update_fields=["aktiv"])

        return redirect("regnskap:leverandorer")

    return render(
        request,
        "regnskap/leverandor_slett.html",
        {
            "organisasjon": organisasjon,
            "leverandor": leverandor,
        }
    )

@login_required
def kunder(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    kunder = Kunde.objects.filter(
        organisasjon=organisasjon
    ).select_related(
        "konto"
    ).order_by(
        "konto__kontonummer"
    )

    return render(
        request,
        "regnskap/kunder.html",
        {
            "organisasjon": organisasjon,
            "kunder": kunder,
        }
    )

@login_required
def kunde_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    samlekontotyper = SamlekontoType.objects.filter(
        hovedbokskonto__organisasjon=organisasjon,
        aktiv=True,
    ).order_by("navn")

    if request.method == "POST":
        samlekontotype_id = request.POST.get("samlekontotype")
        navn = request.POST.get("navn", "").strip()

        samlekontotype = get_object_or_404(
            SamlekontoType,
            id=samlekontotype_id,
            hovedbokskonto__organisasjon=organisasjon,
        )

        kontonummer = samlekontotype.neste_nummer

        with transaction.atomic():
            konto = Konto.objects.create(
                organisasjon=organisasjon,
                kontonummer=kontonummer,
                kontonavn=navn,
                styrekode=samlekontotype.hovedbokskonto.styrekode,
                samlekonto=False,
                aktiv=True,
            )

            Kunde.objects.create(
                organisasjon=organisasjon,
                konto=konto,
                navn=navn,
                orgnummer=request.POST.get("orgnummer", "").strip(),
                adresse=request.POST.get("adresse", "").strip(),
                postnummer=request.POST.get("postnummer", "").strip(),
                poststed=request.POST.get("poststed", "").strip(),
                land=request.POST.get("land", "").strip() or "Norge",
                kontaktperson=request.POST.get("kontaktperson", "").strip(),
                epost=request.POST.get("epost", "").strip(),
                url=request.POST.get("url", "").strip(),
                telefon=request.POST.get("telefon", "").strip(),
                aktiv=request.POST.get("aktiv") == "on",
                notat=request.POST.get("notat", "").strip(),
            )

            samlekontotype.neste_nummer += 1
            samlekontotype.save(update_fields=["neste_nummer"])

        return redirect("regnskap:kunder")

    return render(
        request,
        "regnskap/kunde_skjema.html",

        {
            "organisasjon": organisasjon,
            "kunde": None,
            "samlekontotyper": samlekontotyper,
            "skjema": {
                "navn": request.GET.get("navn", ""),
                "orgnummer": request.GET.get("orgnummer", ""),
                "adresse": request.GET.get("adresse", ""),
                "postnummer": request.GET.get("postnummer", ""),
                "poststed": request.GET.get("poststed", ""),
                "land": request.GET.get("land", "Norge"),
            },
        }
    )

@login_required
def kunde_endre(request, kunde_id):
    return redirect("regnskap:kunder")


@login_required
def kunde_slett(request, kunde_id):
    return redirect("regnskap:kunder")




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
        standard_tekst = request.POST.get(
            "standard_tekst",
            ""
        ).strip()

        if kode and navn:
            Bilagsserie.objects.create(
                organisasjon=organisasjon,
                regnskapsaar=regnskapsaar,
                kode=kode,
                navn=navn,
                standard_tekst=standard_tekst,
                neste_nummer=neste_nummer,
                standard_konto=standard_konto,
                standard_fortegn=standard_fortegn,
                aktiv=aktiv,
            )
            return redirect("regnskap:bilagsserier")

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("kontonummer")

    return render(request, "regnskap/bilagsserie_skjema.html", {
        "organisasjon": organisasjon,
        "regnskapsaar": regnskapsaar,
        "kontoer": kontoer,
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
        bilagsserie.standard_tekst = request.POST.get(
            "standard_tekst",
            ""
        ).strip()
        bilagsserie.aktiv = request.POST.get("aktiv") == "on"

        bilagsserie.save()

        return redirect(
            f"{reverse('regnskap:bilagsserier')}?aar={bilagsserie.regnskapsaar.id}"
        )

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("kontonummer")

    return render(request, "regnskap/bilagsserie_skjema.html", {
        "organisasjon": organisasjon,
        "regnskapsaar": bilagsserie.regnskapsaar,
        "bilagsserie": bilagsserie,
        "kontoer": kontoer,
    })

@login_required
def bilag_slett(request, bilag_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    bilag = get_object_or_404(
        Bilag,
        id=bilag_id,
        organisasjon=organisasjon,
    )

    if not bilag_kan_slettes(bilag):
        messages.error(request, "Dette bilaget kan ikke slettes. Det må eventuelt tilbakeføres.")
        return redirect("regnskap:bilag_detalj", bilag_id=bilag.id)

    bilag.h_status = Bilag.STATUS_SLETTET
    bilag.save()

    messages.success(request, f"Bilag {bilag.bilagsnummer} er slettet.")

    return redirect(
        reverse("regnskap:bilag_liste") +
        f"?aar={bilag.regnskapsaar.id}"
    )

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
    fra_dato = request.GET.get("fra_dato")
    til_dato = request.GET.get("til_dato")
    valgt_avdeling_id = request.GET.get("avdeling")
    valgt_prosjekt_id = request.GET.get("prosjekt")

    avdelinger = Avdeling.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("avdelingsnummer")

    prosjekter = Prosjekt.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("prosjektnummer")

    if regnskapsaar:
        alle_bilag = Bilag.objects.filter(
            organisasjon=organisasjon,
            regnskapsaar=regnskapsaar,
        )

        if not fra_dato and not til_dato:
            siste_50 = list(
                alle_bilag.order_by(
                    "-bilagsdato",
                    "-bilagsnummer",
                )[:50]
            )

            if siste_50:
                fra_dato = min(b.bilagsdato for b in siste_50).isoformat()
                til_dato = max(b.bilagsdato for b in siste_50).isoformat()

        bilag = alle_bilag

        if fra_dato:
            bilag = bilag.filter(bilagsdato__gte=fra_dato)

        if til_dato:
            bilag = bilag.filter(bilagsdato__lte=til_dato)
        if valgt_avdeling_id:
            bilag = bilag.filter(linjer__avdeling_id=valgt_avdeling_id)

        if valgt_prosjekt_id:
            bilag = bilag.filter(linjer__prosjekt_id=valgt_prosjekt_id)

        bilag = bilag.distinct()


        bilag = bilag.order_by("bilagsdato", "bilagsserie__kode", "bilagsnummer")

        sum_debet = Decimal("0")
        sum_kredit = Decimal("0")

        for b in bilag:
            for linje in b.linjer.all():
                if linje.belop > 0:
                    sum_debet += linje.belop
                else:
                    sum_kredit += linje.belop

        total_differanse = sum_debet + sum_kredit

    return render(
        request,
        "regnskap/bilag_liste.html",
        {
            "organisasjon": organisasjon,
            "regnskapsaar": regnskapsaar,
            "regnskapsaar_liste": regnskapsaar_liste,
            "bilag": bilag,
            "fra_dato": fra_dato,
            "til_dato": til_dato,
            "avdelinger": avdelinger,
            "prosjekter": prosjekter,
            "valgt_avdeling_id": valgt_avdeling_id,
            "valgt_prosjekt_id": valgt_prosjekt_id,
            "sum_debet": sum_debet,
            "sum_kredit": sum_kredit,
            "total_differanse": total_differanse,
        }
    )

@login_required
def bilag_detalj(request, bilag_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    bilag = get_object_or_404(
        Bilag,
        id=bilag_id,
        organisasjon=organisasjon,
    )

    linjer = bilag.linjer.all().order_by("linjenummer")

    konto_map = {
        k.kontonummer: k.kontonavn
        for k in Konto.objects.filter(
            organisasjon=organisasjon
        )
    }


    return render(request, "regnskap/bilag_detalj.html", {
        "organisasjon": organisasjon,
        "bilag": bilag,
        "linjer": linjer,
        "konto_map": konto_map,
        "bilag_kan_endres": bilag_kan_endres(bilag),
        "bilag_kan_slettes": bilag_kan_slettes(bilag),
        "bilag_kan_tilbakefores": bilag_kan_tilbakefores(bilag),
    })

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
    valgt_serie_id = request.GET.get("serie")

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

    kontonavn_json = json.dumps({
        str(k.kontonummer): {
            "navn": k.kontonavn,
            "samlekonto": k.samlekonto,
        }
        for k in kontoer
    })    
    avdelinger = Avdeling.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("avdelingsnummer")

    prosjekter = Prosjekt.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("prosjektnummer")

    kontonavn_json = json.dumps({
        str(k.kontonummer): {
            "navn": k.kontonavn,
            "samlekonto": k.samlekonto,
        }
        for k in kontoer
    })

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

            for linjenr in range(1, 7):
                konto = request.POST.get(f"konto_{linjenr}", "").strip()
                tekst = request.POST.get(f"tekst_{linjenr}", "").strip()
                belop = request.POST.get(f"belop_{linjenr}", "").strip()
                avdeling_id = request.POST.get(f"avdeling_{linjenr}") or None
                prosjekt_id = request.POST.get(f"prosjekt_{linjenr}") or None

                if konto and belop:

                    konto_obj = Konto.objects.filter(
                        organisasjon=organisasjon,
                        kontonummer=konto,
                    ).first()

                    if not konto_obj:
                        raise ValueError(f"Konto {konto} finnes ikke i kontoplanen.")

                    if not konto_kan_foeres_paa(konto_obj):
                        messages.error(
                            request,
                            f"Konto {konto_obj.kontonummer} {konto_obj.kontonavn} er samlekonto og kan ikke føres på."
                        )
                        return render(request, "regnskap/bilag_skjema.html", {
                            "organisasjon": organisasjon,
                            "regnskapsaar": regnskapsaar,
                            "bilagsserier": bilagsserier,
                            "kontoer": kontoer,
                            "dagens_dato": timezone.localdate(),
                            "dagens_dato_iso": timezone.localdate().isoformat(),
                            "kontonavn_json": kontonavn_json,
                            "avdelinger": avdelinger,
                            "prosjekter": prosjekter,
                        })

                    Bilagslinje.objects.create(
                        bilag=bilag,
                        linjenummer=linjenr,
                        kontonummer=konto,
                        avdeling_id=avdeling_id,
                        prosjekt_id=prosjekt_id,
                        linjetekst=tekst,
                        belop=Decimal(belop.replace(",", ".")),
                    )

        messages.success(
            request,
            f"Bilag {bilagsserie.kode}{bilagsnummer} er lagret."
        )

        return redirect(
            f"{reverse('regnskap:bilag_ny')}?aar={regnskapsaar.id}&serie={bilagsserie.id}"
        )
    dagens_dato = timezone.localdate()

    return render(request, "regnskap/bilag_skjema.html", {
        "organisasjon": organisasjon,
        "regnskapsaar": regnskapsaar,
        "bilagsserier": bilagsserier,
        "kontoer": kontoer,
        "dagens_dato": dagens_dato,
        "dagens_dato_iso": dagens_dato.isoformat(),
        "kontonavn_json": kontonavn_json,
        "avdelinger": avdelinger,
        "prosjekter": prosjekter,
        "valgt_serie_id": valgt_serie_id,
    })

@login_required
def bilag_endre(request, bilag_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    bilag = get_object_or_404(
        Bilag,
        id=bilag_id,
        organisasjon=organisasjon,
    )

    linjer = list(
        bilag.linjer.all().order_by("linjenummer")
    )

    linje1 = linjer[0] if len(linjer) > 0 else None
    linje2 = linjer[1] if len(linjer) > 1 else None
    linje3 = linjer[2] if len(linjer) > 2 else None
    linje4 = linjer[3] if len(linjer) > 3 else None
    linje5 = linjer[4] if len(linjer) > 4 else None
    linje6 = linjer[5] if len(linjer) > 5 else None

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon
    ).order_by("kontonummer")

    avdelinger = Avdeling.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("avdelingsnummer")

    prosjekter = Prosjekt.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("prosjektnummer")

    kontonavn_json = json.dumps({
        str(k.kontonummer): {
            "navn": k.kontonavn,
            "samlekonto": k.samlekonto,
        }
        for k in kontoer
    })
    if request.method == "POST":
        nye_linjer = []

        konto_liste = request.POST.getlist("konto[]")
        tekst_liste = request.POST.getlist("linjetekst[]")
        belop_liste = request.POST.getlist("belop[]")
        avdeling_liste = request.POST.getlist("avdeling[]")
        prosjekt_liste = request.POST.getlist("prosjekt[]")

        antall_linjer = max(
            len(konto_liste),
            len(tekst_liste),
            len(belop_liste),
            len(avdeling_liste),
            len(prosjekt_liste),
        )

        for i in range(antall_linjer):
            linjenr = i + 1

            konto = konto_liste[i].strip() if i < len(konto_liste) else ""
            tekst = tekst_liste[i].strip() if i < len(tekst_liste) else ""
            belop = belop_liste[i].strip() if i < len(belop_liste) else ""
            avdeling_id = avdeling_liste[i] if i < len(avdeling_liste) and avdeling_liste[i] else None
            prosjekt_id = prosjekt_liste[i] if i < len(prosjekt_liste) and prosjekt_liste[i] else None
            if konto and belop:
                konto_obj = Konto.objects.filter(
                    organisasjon=organisasjon,
                    kontonummer=konto,
                ).first()

                if not konto_obj:
                    messages.error(
                        request,
                        f"Konto {konto} på linje {linjenr} finnes ikke i kontoplanen."
                    )

                    return render(request, "regnskap/bilag_skjema.html", {
                        "organisasjon": organisasjon,
                        "regnskapsaar": bilag.regnskapsaar,
                        "bilag": bilag,
                        "modus": "endre",
                        "linjer": linjer,
                        "dagens_dato": bilag.bilagsdato,
                        "dagens_dato_iso": bilag.bilagsdato.isoformat(),
                        "bilagsserier": bilagsserier,
                        "valgt_serie_id": bilag.bilagsserie_id,
                        "kontoer": kontoer,
                        "kontonavn_json": kontonavn_json,
                        "feil_linje": str(linjenr),
                        "avdelinger": avdelinger,
                        "prosjekter": prosjekter,
                    })
                if not konto_kan_foeres_paa(konto_obj):
                    messages.error(
                        request,
                        f"Konto {konto_obj.kontonummer} {konto_obj.kontonavn} er samlekonto og kan ikke føres på."
                    )

                    return render(request, "regnskap/bilag_skjema.html", {
                        "organisasjon": organisasjon,
                        "regnskapsaar": bilag.regnskapsaar,
                        "bilag": bilag,
                        "modus": "endre",
                        "linjer": linjer,
                        "dagens_dato": bilag.bilagsdato,
                        "dagens_dato_iso": bilag.bilagsdato.isoformat(),
                        "bilagsserier": bilagsserier,
                        "valgt_serie_id": bilag.bilagsserie_id,
                        "kontoer": kontoer,
                        "kontonavn_json": kontonavn_json,
                        "feil_linje": str(linjenr),
                        "avdelinger": avdelinger,
                        "prosjekter": prosjekter,
                    })
                nye_linjer.append(
                    (
                        linjenr,
                        konto,
                        tekst,
                        belop,
                        avdeling_id,
                        prosjekt_id,
                    )
                )
        bilag.bilagsdato = request.POST.get("bilagsdato")
        bilag.foringsdato = request.POST.get("foringsdato")
        bilag.bilagstekst = request.POST.get("bilagstekst", "").strip()
        bilag.save()

        bilag.linjer.all().delete()

        for linjenr, konto, tekst, belop, avdeling_id, prosjekt_id in nye_linjer:
            Bilagslinje.objects.create(
                bilag=bilag,
                linjenummer=linjenr,
                kontonummer=konto,
                avdeling_id=avdeling_id,
                prosjekt_id=prosjekt_id,
                linjetekst=tekst,
                belop=Decimal(belop.replace(",", ".")),
            )
        return redirect("regnskap:bilag_detalj", bilag_id=bilag.id)


    return render(request, "regnskap/bilag_skjema.html", {
        "organisasjon": organisasjon,
        "regnskapsaar": bilag.regnskapsaar,
        "bilag": bilag,
        "linjer": linjer,
        "dagens_dato": bilag.bilagsdato,
        "dagens_dato_iso": bilag.bilagsdato.isoformat(),
        "kontoer": kontoer,
        "kontonavn_json": kontonavn_json,
        "linje1": linje1,
        "linje2": linje2,
        "linje3": linje3,
        "linje4": linje4,
        "linje5": linje5,
        "linje6": linje6,
        "avdelinger": avdelinger,
        "prosjekter": prosjekter,

    })

@login_required
def kontosporring(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon
    ).order_by("kontonummer")

    sok = request.GET.get("konto", "").strip()

    posteringer = []
    konto_treff = []
    valgt_konto = ""
    valgt_kontonavn = ""
    sum_belop = 0

    if sok:
        if sok.isdigit():
            konto_obj = Konto.objects.filter(
                organisasjon=organisasjon,
                kontonummer=sok,
            ).first()
        else:
            konto_obj = None

        if konto_obj:
            valgt_konto = konto_obj.kontonummer
            valgt_kontonavn = konto_obj.kontonavn

            posteringer = Bilagslinje.objects.filter(
                bilag__organisasjon=organisasjon,
                kontonummer=konto_obj.kontonummer,
            ).select_related(
                "bilag",
                "avdeling",
                "prosjekt",
            ).order_by(
                "bilag__bilagsdato",
                "bilag__bilagsnummer",
            )

        else:
            konto_treff = Konto.objects.filter(
                organisasjon=organisasjon,
                aktiv=True,
                kontonavn__icontains=sok,
            ).order_by("kontonummer")[:50]

    sum_belop = sum(p.belop for p in posteringer)

    return render(
        request,
        "regnskap/kontosporring.html",
        {
            "organisasjon": organisasjon,
            "kontoer": kontoer,
            "sok": sok,
            "konto_treff": konto_treff,
            "valgt_konto": valgt_konto,
            "posteringer": posteringer,
            "sum_belop": sum_belop,
            "valgt_kontonavn": valgt_kontonavn,
        }
    )

@login_required
def bilagsjournal(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    regnskapsaar_liste = Regnskapsaar.objects.filter(
        organisasjon=organisasjon
    ).order_by("-aar")

    bilagsserier = Bilagsserie.objects.filter(
        organisasjon=organisasjon
    ).order_by("kode")

    avdelinger = Avdeling.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("avdelingsnummer")

    prosjekter = Prosjekt.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("prosjektnummer")

    bilag_liste = (
        Bilag.objects
        .filter(organisasjon=organisasjon)
        .select_related("regnskapsaar", "bilagsserie")
        .prefetch_related("linjer")
        .order_by("bilagsdato", "bilagsnummer")
    )

    regnskapsaar_id = request.GET.get("regnskapsaar")
    bilagsserie_id = request.GET.get("bilagsserie")
    bilag_fra = request.GET.get("bilag_fra")
    bilag_til = request.GET.get("bilag_til")

    periode_fra = request.GET.get("periode_fra")
    periode_til = request.GET.get("periode_til")
    avdeling_id = request.GET.get("avdeling")
    prosjekt_id = request.GET.get("prosjekt")
    kun_differanse = request.GET.get("kun_differanse")

    if regnskapsaar_id:
        bilag_liste = bilag_liste.filter(regnskapsaar_id=regnskapsaar_id)

    if bilagsserie_id:
        bilag_liste = bilag_liste.filter(bilagsserie_id=bilagsserie_id)

    if bilag_fra:
        bilag_liste = bilag_liste.filter(bilagsnummer__gte=bilag_fra)

    if bilag_til:
        bilag_liste = bilag_liste.filter(bilagsnummer__lte=bilag_til)

    if periode_fra:
        bilag_liste = bilag_liste.filter(h_status__gte=periode_fra)

    if periode_til:
        bilag_liste = bilag_liste.filter(h_status__lte=periode_til)
    if avdeling_id:
        bilag_liste = bilag_liste.filter(linjer__avdeling_id=avdeling_id).distinct()

    if prosjekt_id:
        bilag_liste = bilag_liste.filter(linjer__prosjekt_id=prosjekt_id).distinct()

    if kun_differanse:
        bilag_liste = [
            bilag for bilag in bilag_liste
            if bilag.har_differanse
        ]

    return render(
        request,
        "regnskap/bilagsjournal.html",
        {
            "organisasjon": organisasjon,
            "bilag_liste": bilag_liste,
            "regnskapsaar_liste": regnskapsaar_liste,
            "bilagsserier": bilagsserier,
            "avdelinger": avdelinger,
            "prosjekter": prosjekter,
            "filter": request.GET,
        },
    )

def kontojournal(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon,
        samlekonto=False,
    ).order_by("kontonummer")

    regnskapsaar_liste = Regnskapsaar.objects.filter(
        organisasjon=organisasjon
    ).order_by("-aar")

    bilagsserier = Bilagsserie.objects.filter(
        organisasjon=organisasjon
    ).order_by("kode")

    avdelinger = Avdeling.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("avdelingsnummer")

    prosjekter = Prosjekt.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).order_by("prosjektnummer")

    linjer = (
        Bilagslinje.objects
        .filter(bilag__organisasjon=organisasjon)
        .select_related("bilag", "bilag__regnskapsaar", "bilag__bilagsserie", "avdeling", "prosjekt")
        .order_by("kontonummer", "bilag__bilagsdato", "bilag__bilagsnummer", "linjenummer")
    )

    regnskapsaar_id = request.GET.get("regnskapsaar")
    periode_fra = request.GET.get("periode_fra")
    periode_til = request.GET.get("periode_til")
    bilagsserie_id = request.GET.get("bilagsserie")
    bilag_fra = request.GET.get("bilag_fra")
    bilag_til = request.GET.get("bilag_til")
    konto_fra = request.GET.get("konto_fra")
    konto_til = request.GET.get("konto_til")
    avdeling_id = request.GET.get("avdeling")
    prosjekt_id = request.GET.get("prosjekt")

    if regnskapsaar_id:
        linjer = linjer.filter(bilag__regnskapsaar_id=regnskapsaar_id)

    if periode_fra:
        linjer = linjer.filter(bilag__h_status__gte=periode_fra)

    if periode_til:
        linjer = linjer.filter(bilag__h_status__lte=periode_til)

    if bilagsserie_id:
        linjer = linjer.filter(bilag__bilagsserie_id=bilagsserie_id)

    if bilag_fra:
        linjer = linjer.filter(bilag__bilagsnummer__gte=bilag_fra)

    if bilag_til:
        linjer = linjer.filter(bilag__bilagsnummer__lte=bilag_til)

    if konto_fra:
        linjer = linjer.filter(kontonummer__gte=konto_fra)

    if konto_til:
        linjer = linjer.filter(kontonummer__lte=konto_til)

    if avdeling_id:
        linjer = linjer.filter(avdeling_id=avdeling_id)

    if prosjekt_id:
        linjer = linjer.filter(prosjekt_id=prosjekt_id)

    konto_grupper = {}

    for linje in linjer:
        konto_grupper.setdefault(linje.kontonummer, {
            "kontonummer": linje.kontonummer,
            "kontonavn": linje.kontonavn,
            "linjer": [],
            "sum_debet": 0,
            "sum_kredit": 0,
            "saldo": 0,
        })

        gruppe = konto_grupper[linje.kontonummer]
        gruppe["linjer"].append(linje)

        if linje.belop >= 0:
            gruppe["sum_debet"] += linje.belop
        else:
            gruppe["sum_kredit"] += -linje.belop

        gruppe["saldo"] = gruppe["sum_debet"] - gruppe["sum_kredit"]

    return render(request, "regnskap/kontojournal.html", {
        "organisasjon": organisasjon,
        "kontoer": kontoer,
        "konto_grupper": konto_grupper.values(),
        "regnskapsaar_liste": regnskapsaar_liste,
        "bilagsserier": bilagsserier,
        "avdelinger": avdelinger,
        "prosjekter": prosjekter,
        "filter": request.GET,
    })

@login_required
def leverandor_brreg_sok(request):
    query = request.GET.get("q", "").strip()
    treff = []

    if query:
        url = "https://data.brreg.no/enhetsregisteret/api/enheter"

        response = requests.get(
            url,
            params={
                "navn": query,
                "size": 10,
            },
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            treff = data.get("_embedded", {}).get("enheter", [])

    return render(
        request,
        "regnskap/leverandor_brreg_sok.html",
        {
            "query": query,
            "treff": treff,
        },
    )

@login_required
def kunde_brreg_sok(request):
    return leverandor_brreg_sok(request)

@login_required
def medlemmer(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon,
    ).order_by(
        "etternavn",
        "fornavn",
    )

    return render(
        request,
        "regnskap/medlemmer.html",
        {
            "organisasjon": organisasjon,
            "medlemmer": medlemmer,
        },
    )

@login_required
def medlemmer_synkroniser(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    melding = None

    if request.method == "POST":

        if request.POST.get("handling") == "tildel_medlemsnummer":
            resultat = tildel_medlemsnummer(organisasjon)
            melding = (
                f"Tildelte medlemsnummer til "
                f"{resultat['tildelt_medlemsnummer']} medlemmer."
            )

        elif request.POST.get("handling") == "opprett_medlemskontoer":
            resultat = opprett_medlemskontoer(organisasjon)
            melding = (
                f"Opprettet "
                f"{resultat['opprettet_medlemskontoer']} medlemskontoer."
            )

    analyse = analyser_medlemssynkronisering(organisasjon)

    return render(
        request,
        "regnskap/medlemmer_synkroniser.html",
        {
            "organisasjon": organisasjon,
            "rapport": analyse["rapport"],
            "mangler_medlemsnummer_liste": analyse["mangler_medlemsnummer_liste"],
            "mangler_konto_liste": analyse["mangler_konto_liste"],
            "melding": melding,
        },
    )


