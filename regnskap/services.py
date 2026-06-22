from .models import Styrekode, Konto

STANDARD_STYREKODER = [
    ("1xxx", "Aktiva", "Sum aktiva"),
    ("10xx", "Likvider", "Sum likvider"),
    ("11xx", "Fordringer", "Sum fordringer"),
    ("12xx", "Andre omløpsmidler", "Sum andre omløpsmidler"),

    ("2xxx", "Passiva", "Sum passiva"),
    ("20xx", "Egenkapital", "Sum egenkapital"),
    ("29xx", "Gjeld", "Sum gjeld"),

    ("3xxx", "Inntekter", "Sum inntekter"),
    ("30xx", "Driftsinntekter", "Sum driftsinntekter"),

    ("5xxx", "Møtekostnader", "Sum møtekostnader"),
    ("54xx", "Instruktører og foredrag", "Sum instruktører og foredrag"),

    ("6xxx", "Administrasjon", "Sum administrasjon"),
    ("7xxx", "Finans", "Sum finans"),
    ("8xxx", "Diverse kostnader", "Sum diverse kostnader"),
    ("9xxx", "Årsoppgjør", "Sum årsoppgjør"),
]


STANDARD_KONTOPLAN = [
    (100, "Kasse", "1001"),
    (190, "Bank", "1002"),
    (120, "Medlemsfordringer", "1101"),
    (130, "Andre fordringer", "1102"),

    (200, "Egenkapital", "2001"),
    (290, "Leverandørgjeld", "2901"),
    (291, "Skyldige kostnader", "2902"),

    (300, "Medlemskontingent", "3001"),
    (310, "Kursinntekter", "3002"),
    (320, "Møteinntekter", "3003"),
    (330, "Offentlige tilskudd", "3004"),
    (340, "Gaver", "3005"),
    (350, "Andre inntekter", "3006"),

    (500, "Møtekostnader", "5001"),
    (510, "Kurskostnader", "5002"),
    (520, "Reisekostnader", "5003"),
    (530, "Foredragsholder", "5401"),
    (540, "Trenerlønn", "5402"),

    (600, "Kontorrekvisita", "6001"),
    (610, "Porto", "6002"),
    (620, "Telefon og internett", "6003"),
    (630, "Programvare og IT", "6004"),

    (700, "Bankgebyrer", "7001"),
    (710, "Forsikringer", "7002"),

    (800, "Andre kostnader", "8001"),
    (900, "Overføring resultat", "9001"),
]


def opprett_standard_regnskap(organisasjon):
    for kode, fortekst, sumtekst in STANDARD_STYREKODER:
        Styrekode.objects.get_or_create(
            organisasjon=organisasjon,
            kode=kode,
            defaults={
                "fortekst": fortekst,
                "sumtekst": sumtekst,
            }
        )

    for kontonummer, kontonavn, styrekode in STANDARD_KONTOPLAN:
        Konto.objects.get_or_create(
            organisasjon=organisasjon,
            kontonummer=kontonummer,
            defaults={
                "kontonavn": kontonavn,
                "styrekode": styrekode,
            }
        )

