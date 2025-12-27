# /srv/u3a/lag/management/commands/show_urls.py

from django.core.management.base import BaseCommand
from lag.models import Organisasjon # Importer modellen
import io
import sys

class Command(BaseCommand):
    help = 'Viser rå URL-er fra databasen for å identifisere usynlige tegn (debugging).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("ADVARSEL: Dette sjekker alle URL-er for usynlige tegn."))
        self.stdout.write("---------------------------------------------------------------------")

        feil_funnet = False

        for org in Organisasjon.objects.all():
            if not org.nettside:
                continue
            
            raw_url = org.nettside
            
            # 1. Standard utskrift
            self.stdout.write(f"\nNavn: {org.organisasjon}")
            self.stdout.write(f"DB-verdi (Normal): '{raw_url}'")
            
            # 2. Rå Python repr() for å vise usynlige tegn
            raw_repr = repr(raw_url)
            self.stdout.write(f"DB-verdi (Rå Python): {raw_repr}")
            
            # 3. Sjekk for den feilformede protokollen
            if raw_url.strip().startswith('http//'):
                self.stdout.write(self.style.ERROR(f"!!! KRITISK FEIL FUNNET: Starter med 'http//'!"))
                feil_funnet = True
            
            # 4. Hvis databasen er OK, men sjekken feiler (debugging)
            if 'http://' in raw_repr and len(raw_url) != len(raw_url.strip()):
                self.stdout.write(self.style.ERROR(f"!!! KRITISK FEIL FUNNET: Skjult mellomrom/tegn funnet!"))
                feil_funnet = True


        if feil_funnet:
            self.stdout.write(self.style.ERROR("\nFEIL SJEKK FULLFØRT. VENNLIGST SE ETTER '\\r', '\\n', eller UGYLDIGE PROTOKOLLER."))
        else:
             self.stdout.write(self.style.SUCCESS("\nFULLFØRT: Ingen åpenbare feilfunn i rådata."))
