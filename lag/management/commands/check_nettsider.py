from django.core.management.base import BaseCommand
from django.utils import timezone

from lag.models import Organisasjon

import requests


TIMEOUT = 5  # sek


def normalize_candidates(url: str) -> list[str]:
    url = (url or "").strip()
    if not url:
        return []
    # fjern trailing slash (valgfritt)
    url = url.rstrip("/")

    if url.startswith("http://") or url.startswith("https://"):
        return [url]
    # prøv https først, så http
    return [f"https://{url}", f"http://{url}"]


def check_url(url: str) -> tuple[bool, int | None, str | None]:
    """
    Return: (ok, status_code, error)
    ok = True hvis HTTP 200.
    """
    try:
        # HEAD først (raskt), fall tilbake til GET hvis blokkert
        r = requests.head(url, allow_redirects=True, timeout=TIMEOUT)
        if r.status_code in (405, 403):  # noen nekter HEAD
            r = requests.get(url, allow_redirects=True, timeout=TIMEOUT)

        return (r.status_code == 200, r.status_code, None)
    except Exception as e:
        return (False, None, str(e)[:200])


class Command(BaseCommand):
    help = "Sjekker nettsidene til lokallagene og lagrer status i DB"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Test: begrens antall rader")

    def handle(self, *args, **options):
        qs = Organisasjon.objects.all().only("id", "nettside")
        if options["limit"]:
            qs = qs[: options["limit"]]

        ok_count = 0
        fail_count = 0
        now = timezone.now()

        for org in qs:
            candidates = normalize_candidates(org.nettside)
            if not candidates:
                # ingen nettside registrert
                org.lenke_status = "down"
                # ALTERNATIV hvis du INSISTERER på status-feltet:
                # org.status = "inactive"
                org.sist_endret = now
                org.save(update_fields=["lenke_status", "sist_endret"])
                fail_count += 1
                continue

            final_ok = False
            final_code = None

            for u in candidates:
                ok, code, err = check_url(u)
                final_code = code
                if ok:
                    final_ok = True
                    break

            if final_ok:
                org.lenke_status = "active"   # <- anbefalt (blå)
                # org.status = "active"       # <- hvis du vil bruke status-feltet (ikke anbefalt)
                ok_count += 1
            else:
                org.lenke_status = "down"     # <- anbefalt (rød)
                # org.status = "down"         # <- hvis du vil bruke status-feltet
                fail_count += 1

            org.sist_endret = now
            org.save(update_fields=["lenke_status", "sist_endret"])

        self.stdout.write(self.style.SUCCESS(
            f"Ferdig. OK={ok_count}, FEIL={fail_count}"
        ))
