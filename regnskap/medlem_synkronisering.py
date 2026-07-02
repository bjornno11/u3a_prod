from django.db import transaction

from lag.models import LagMedlem
from .models import Konto, SamlekontoType


def analyser_medlemssynkronisering(organisasjon):
    """
    Analyserer sammenhengen mellom medlemsregisteret
    og regnskapet uten å gjøre databaseendringer.
    """

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    )

    godkjente = medlemmer.filter(
        status=LagMedlem.STATUS_GODKJENT,
    )

    registrerte = medlemmer.filter(
        status=LagMedlem.STATUS_REGISTRERT,
    )

    har_medlemsnummer = godkjente.exclude(
        medlemsnummer__isnull=True,
    )

    mangler_medlemsnummer = godkjente.filter(
        medlemsnummer__isnull=True,
    )

    kontonummer_i_regnskap = set(
        str(k)
        for k in Konto.objects.filter(
            organisasjon=organisasjon,
        ).values_list("kontonummer", flat=True)
    )
    mangler_konto_liste = []

    for medlem in godkjente:

        if not medlem.medlemsnummer:
            mangler_konto_liste.append(medlem)
            continue

        if str(medlem.medlemsnummer) not in kontonummer_i_regnskap:
            mangler_konto_liste.append(medlem)

    rapport = {
        "aktive_medlemmer": medlemmer.count(),
        "godkjente": godkjente.count(),
        "registrerte": registrerte.count(),
        "har_medlemsnummer": har_medlemsnummer.count(),
        "mangler_medlemsnummer": mangler_medlemsnummer.count(),
        "mangler_konto": len(mangler_konto_liste),
        "konto_uten_medlem": 0,
        "konto_maa_oppdateres": 0,
    }

    return {
        "rapport": rapport,
        "mangler_medlemsnummer_liste": list(mangler_medlemsnummer),
        "mangler_konto_liste": mangler_konto_liste,
    }

def hent_medlem_samlekontotype(organisasjon):
    return SamlekontoType.objects.select_for_update().get(
        hovedbokskonto__organisasjon=organisasjon,
        navn__iexact="Medlemmer",
        aktiv=True,
    )


def tildel_medlemsnummer(organisasjon):
    """
    Tildeler medlemsnummer til godkjente medlemmer
    som mangler medlemsnummer.

    Oppretter ikke konto.
    """

    antall = 0

    with transaction.atomic():
        samlekontotype = hent_medlem_samlekontotype(organisasjon)

        medlemmer = LagMedlem.objects.select_for_update().filter(
            organisasjon=organisasjon,
            status=LagMedlem.STATUS_GODKJENT,
            medlemsnummer__isnull=True,
        ).order_by("id")

        for medlem in medlemmer:
            nummer = samlekontotype.neste_nummer

            if nummer < samlekontotype.nummer_fra:
                nummer = samlekontotype.nummer_fra

            if nummer > samlekontotype.nummer_til:
                raise ValueError("Nummerintervallet for medlemmer er brukt opp.")

            medlem.medlemsnummer = nummer
            medlem.save(update_fields=["medlemsnummer", "sist_endret"])

            samlekontotype.neste_nummer = nummer + 1
            samlekontotype.save(update_fields=["neste_nummer"])

            antall += 1

    return {
        "tildelt_medlemsnummer": antall,
    }


def opprett_medlemskontoer(organisasjon):
    """
    Oppretter regnskapskontoer for godkjente medlemmer
    som har medlemsnummer, men mangler konto.
    """

    godkjente = LagMedlem.objects.filter(
        organisasjon=organisasjon,
        status=LagMedlem.STATUS_GODKJENT,
        medlemsnummer__isnull=False,
    ).order_by("medlemsnummer")

    opprettet = 0

    with transaction.atomic():
        for medlem in godkjente:
            kontonummer = str(medlem.medlemsnummer)

            if Konto.objects.filter(
                organisasjon=organisasjon,
                kontonummer=kontonummer,
            ).exists():
                continue

            Konto.objects.create(
                organisasjon=organisasjon,
                kontonummer=kontonummer,
                kontonavn=medlem.navn,
                aktiv=True,
            )

            opprettet += 1

    return {
        "opprettet_medlemskontoer": opprettet,
    }


