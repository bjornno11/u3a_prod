import csv
import urllib.request

from django.core.management.base import BaseCommand
from lag.models import Postnummer


URL = "https://www.bring.no/postnummerregister-ansi.txt"


class Command(BaseCommand):
    help = "Importer postnummer fra Bring/Posten"

    def handle(self, *args, **options):
        with urllib.request.urlopen(URL) as response:
            content = response.read().decode("cp1252")

        reader = csv.reader(content.splitlines(), delimiter="\t")

        count = 0

        for row in reader:
            if len(row) < 4:
                continue

            postnummer = row[0].strip()
            poststed = row[1].strip()
            kommunenavn = row[3].strip()

            if not postnummer.isdigit():
                continue

            Postnummer.objects.update_or_create(
                postnummer=postnummer,
                defaults={
                    "poststed": poststed.title(),
                    "kommune": kommunenavn.title(),
                },
            )

            count += 1

        self.stdout.write(self.style.SUCCESS(f"Importerte/oppdaterte {count} postnummer"))
