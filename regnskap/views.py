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
import json

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

    kontoer = Konto.objects.filter(
        organisasjon=organisasjon
    ).order_by("kontonummer")

    return render(
        request,
        "regnskap/kontoplan.html",
        {
            "organisasjon": organisasjon,
            "kontoer": kontoer,
            "oppslag": oppslag,
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

    for linje in linjer:
        linje.kontonavn = konto_map.get(linje.kontonummer, "")

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

    valgt_konto = request.GET.get("konto")

    posteringer = []
    valgt_kontonavn = ""

    sum_belop = 0

    if valgt_konto:
        konto_obj = Konto.objects.filter(
            organisasjon=organisasjon,
            kontonummer=valgt_konto,
        ).first()

        if konto_obj:
            valgt_kontonavn = konto_obj.kontonavn

        posteringer = Bilagslinje.objects.filter(
            bilag__organisasjon=organisasjon,
            kontonummer=valgt_konto,
        ).select_related(
            "bilag",
            "avdeling",
            "prosjekt",
        ).order_by(
            "bilag__bilagsdato",
            "bilag__bilagsnummer",
        )
    sum_belop = sum(p.belop for p in posteringer)

    return render(
        request,
        "regnskap/kontosporring.html",
        {
            "organisasjon": organisasjon,
            "kontoer": kontoer,
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

    bilag_liste = (
        Bilag.objects
        .filter(organisasjon=organisasjon)
        .select_related("regnskapsaar")
        .order_by("-bilagsdato", "-bilagsnummer")
    )

    return render(
        request,
        "regnskap/bilagsjournal.html",
        {
            "organisasjon": organisasjon,
            "bilag_liste": bilag_liste,
        },
    )

