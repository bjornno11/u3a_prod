import os
import sys
import django
from datetime import date
from calendar import monthrange

sys.path.append("/srv/u3a_prod")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "u3a.settings")
django.setup()

from lag.models import Organisasjon
from regnskap.models import (
    Regnskapsaar,
    Regnskapsperiode,
    Konto,
    Bilagsserie,
    Momskode,
)

org = Organisasjon.objects.get(id=7)

aar, _ = Regnskapsaar.objects.get_or_create(
    organisasjon=org,
    aar=2026,
    defaults={
        "navn": "2026",
        "fra_dato": date(2026, 1, 1),
        "til_dato": date(2026, 12, 31),
    },
)

for mnd in range(1, 13):
    siste_dag = monthrange(2026, mnd)[1]
    Regnskapsperiode.objects.get_or_create(
        regnskapsaar=aar,
        periodenummer=mnd,
        defaults={
            "fra_dato": date(2026, mnd, 1),
            "til_dato": date(2026, mnd, siste_dag),
        },
    )

kontoer = [
    (100, "Kasse", "1000", False),
    (120, "Medlemsfordringer", "1200", True),
    (190, "Bank", "1900", False),
    (200, "Egenkapital", "2000", False),
    (240, "Leverandørgjeld", "2400", True),
    (300, "Medlemskontingent", "3000", False),
    (310, "Tilskudd", "3100", False),
    (320, "Andre inntekter", "3200", False),
    (400, "Møtekostnader", "4000", False),
    (500, "Lokalleie", "5000", False),
    (550, "Markedsføring", "5500", False),
    (650, "Utstyr og inventar", "6500", False),
    (700, "Kurs og foredrag", "7000", False),
    (750, "Reisekostnader", "7500", False),
    (800, "Administrasjon", "8000", False),
    (850, "Bankgebyrer", "8500", False),
    (890, "Andre kostnader", "8900", False),
]

for nr, navn, styrekode, samlekonto in kontoer:
    Konto.objects.get_or_create(
        organisasjon=org,
        kontonummer=nr,
        defaults={
            "kontonavn": navn,
            "styrekode": styrekode,
            "samlekonto": samlekonto,
        },
    )

serier = [
    ("D", "Daglig bilag", 1, None, ""),
    ("B", "Bankbilag", 1, 190, "+"),
    ("F", "Faktura", 10001, 300, "-"),
    ("K", "Korreksjon", 1, None, ""),
]

for kode, navn, neste, standard_konto, fortegn in serier:
    Bilagsserie.objects.get_or_create(
        organisasjon=org,
        regnskapsaar=aar,
        kode=kode,
        defaults={
            "navn": navn,
            "neste_nummer": neste,
            "standard_konto": standard_konto,
            "standard_fortegn": fortegn,
        },
    )

Momskode.objects.get_or_create(
    organisasjon=org,
    kode="0",
    defaults={
        "navn": "Ingen mva",
        "sats": 0,
    },
)

print("Ferdig: testdata for regnskap er opprettet.")
