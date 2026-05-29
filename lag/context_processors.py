# lag/context_processors.py
from lag.models import Organisasjon


def lokallag_from_host(request):
    """
    Gjør 'lokallag' tilgjengelig i alle templates basert på hostnavn.
    - u3a.no / www.u3a.no -> lokallag = None
    - rakkestad.u3a.no -> lokallag = Organisasjon(subdomene="rakkestad")
    - www.rakkestad.u3a.no -> lokallag = Organisasjon(subdomene="rakkestad")
    """
    host = (request.get_host() or "").split(":")[0].lower()

    # Hoveddomene: ingen lokallag
    if host in ("u3a.no", "www.u3a.no", "localhost", "127.0.0.1"):
        return {"lokallag": None}

    # Vi støtter kun subdomener under u3a.no
    if not host.endswith(".u3a.no"):
        return {"lokallag": None}

    parts = host.split(".")
    if len(parts) < 3:
        return {"lokallag": None}

    # www.rakkestad.u3a.no -> rakkestad
    if parts[0] == "www" and len(parts) >= 4:
        sub = parts[1]
    else:
        sub = parts[0]

    lokallag = Organisasjon.objects.filter(subdomene=sub).first()
    return {"lokallag": lokallag}


