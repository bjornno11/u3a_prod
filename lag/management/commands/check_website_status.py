import requests
from django.core.management.base import BaseCommand
from lag.models import Organisasjon


def normalize_url(raw_url: str) -> str:
    """
    Sørger for at vi har en ordentlig URL med skjema.
    - Hvis brukeren har skrevet 'fsuni.no' -> prøv https://fsuni.no
    - Hvis brukeren har skrevet http/https, bruker vi det.
    """
    if not raw_url:
        return ""

    raw_url = raw_url.strip()

    # Har allerede http/https -> bruk som den er
    if raw_url.startswith("http://") or raw_url.startswith("https://"):
        return raw_url

    # Ellers: prøv https som default
    return "https://" + raw_url


class Command(BaseCommand):
    help = "Sjekker nettside-status for alle Organisasjon-objekter og oppdaterer lenke_status-feltet."

    def handle(self, *args, **options):
        self.stdout.write("Starter sjekk av lenkestatus for alle organisasjoner...")

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        })


        for org in Organisasjon.objects.all():
            raw_url = org.nettside

            if not raw_url:
                ny_status = "UKJENT"
            else:
                url = normalize_url(raw_url)
                ny_status = self.check_url(session, url)

            if org.lenke_status != ny_status:
                self.stdout.write(f"- {org} : {org.lenke_status} -> {ny_status}")
                org.lenke_status = ny_status
                org.save(update_fields=["lenke_status"])

        self.stdout.write(self.style.SUCCESS("Ferdig med sjekk av lenkestatus."))

    def check_url(self, session: requests.Session, url: str) -> str:
        """
        Returnerer 'OK' hvis vi får en 'normal' respons (200–399),
        ellers 'FEIL'.

        Strategi:
        1. Prøv HEAD (lett og rask).
        2. Hvis HEAD feiler (exception) -> prøv GET.
        3. Hvis HEAD gir 'rare' koder (405/403/501) -> prøv GET.
        4. Godta både 2xx og 3xx som OK (redirect er vanlig).
        """

        # Først: prøv HEAD
        try:
            resp = session.head(url, allow_redirects=True, timeout=5)
        except requests.RequestException:
            # HEAD feilet teknisk → prøv GET
            try:
                resp = session.get(url, allow_redirects=True, timeout=8)
            except requests.RequestException:
                return "FEIL"
            else:
                if 200 <= resp.status_code < 400:
                    return "OK"
                return "FEIL"
        else:
            # HEAD svarte
            if 200 <= resp.status_code < 400:
                return "OK"

            # For enkelte koder (HEAD ikke tillatt / ikke implementert / forbidden)
            # prøver vi GET som fallback.
            if resp.status_code in (405, 403, 501):
                try:
                    resp = session.get(url, allow_redirects=True, timeout=8)
                except requests.RequestException:
                    return "FEIL"
                else:
                    if 200 <= resp.status_code < 400:
                        return "OK"
                    return "FEIL"

                        # Andre koder (4xx/5xx) → anser vi som feil
            # Logg for å kunne feilsøke konkrete domener som ser "FEIL" ut
            print(f"[lenkesjekk] {url} ga status {resp.status_code}")
            return "FEIL"

