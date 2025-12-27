# /srv/u3a/lag/management/commands/import_organisasjoner.py

import csv
from django.core.management.base import BaseCommand
from lag.models import Organisasjon 
import os

# DEFINER CSV-FILSTIEN HER
CSV_FIL = '/srv/u3a/organisasjoner.csv' 

class Command(BaseCommand):
    help = 'Importerer organisasjonsdata fra en semikolon-separert CSV-fil (cp1252 koding).'

    def handle(self, *args, **options):
        if not os.path.exists(CSV_FIL):
            self.stderr.write(self.style.ERROR(f'FEIL: Finner ikke CSV-filen på {CSV_FIL}'))
            return

        try:
            # Åpner filen med cp1252 koding og ignorerer feil
            with open(CSV_FIL, mode='r', encoding='cp1252', errors='ignore') as file:
                
                # Fjerner ^M (\r) og mellomrom fra overskriftene, og tvinger små bokstaver
                first_line = file.readline()
                headers = [h.strip().replace('\r', '').lower() for h in first_line.split(';')]

                # Flytter filpekeren tilbake til starten av dataene
                file.seek(len(first_line)) 
                
                # Setter opp DictReader med de korrigerte overskriftene
                reader = csv.DictReader(file, fieldnames=headers, delimiter=';') 
                
                count = 0 
                skipped_count = 0
                
                for row in reader:
                    # Nå bruker vi små bokstaver, strippet for skjulte tegn
                    organisasjonsnavn = row.get('organisasjon', '').strip()

                    # HOPPER OVER TOMME RADER
                    if not organisasjonsnavn:
                        self.stderr.write(self.style.WARNING('SKIPPER TOM RAD: Organisasjonsnavn mangler.'))
                        skipped_count += 1
                        continue 

                    # Normaliserer Status-feltet
                    status_verdi = row.get('status', 'ukjent').strip() # Bruker 'ukjent' for å matche default
                    if status_verdi not in ['aktiv', 'ukjent', 'passiv']:
                        status_verdi = 'ukjent' 
                        
                    try:
                        # VIKTIG: update_or_create-logikken ligger NÅ korrekt inne i loopen
                        Organisasjon.objects.update_or_create(
                            organisasjon=organisasjonsnavn,
                            defaults={
                                'fylke': row.get('fylke', ''),
                                'kommune': row.get('kommune', ''),
                                'adresse': row.get('adresse', ''),
                                'nettside': row.get('nettside', ''),
                                'epost': row.get('epost', ''),
                                'telefon': row.get('telefon', ''),
                                'status': status_verdi.capitalize(), # Lagrer som Aktiv/Ukjent/Passiv
                                'kilde': row.get('kilde', ''),
                            }
                        )
                        count += 1
                    except Exception as e:
                        # Dette fanger opp eventuelle duplikater som fortsatt sniker seg gjennom
                        self.stderr.write(self.style.ERROR(f'KRITISK FEIL ved import av "{organisasjonsnavn}": {e}'))
                
                self.stdout.write(self.style.SUCCESS('--- IMPORT OVERSIKT ---'))
                self.stdout.write(self.style.SUCCESS(f'✅ Vellykket import: {count} organisasjoner behandlet.'))
                if skipped_count > 0:
                    self.stdout.write(self.style.WARNING(f'⚠️ Antall rader hoppet over (tomt navn): {skipped_count}'))
        
        except Exception as file_error:
            self.stderr.write(self.style.ERROR(f'FEIL VED FILÅPNING/LESING: {file_error}'))

