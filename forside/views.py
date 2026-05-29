# forside/views.py
from django.shortcuts import render
from lag.models import Aktivitet, Arrangement, Nyhet
from lag.context_processors import lokallag_from_host
from django.utils import timezone

def forside_view(request):
    lokallag = lokallag_from_host(request).get("lokallag")
    today = timezone.localdate()

    qs = Aktivitet.objects.filter(
        publisert=True,
        dato__gte=today
    ).select_related("organisasjon")

    if lokallag:
        qs = qs.filter(organisasjon=lokallag)

    aktiviteter = qs.order_by("dato", "opprettet")[:10]
    nyheter_qs = Nyhet.objects.filter(
        publisert=True
    ).select_related("organisasjon")

    if lokallag:
        nyheter_qs = nyheter_qs.filter(
            organisasjon=lokallag
        )

    nyheter = nyheter_qs.order_by(
        "-publisert_dato",
        "-opprettet"
    )[:3]

    template = "index.html"

    if lokallag and lokallag.hjemmesidetype == 2:
        template = "index2.html"
    elif lokallag and lokallag.hjemmesidetype == 3:
        template = "index3.html"

    return render(
        request,
        template,
        {
            "lokallag": lokallag,
            "aktiviteter": aktiviteter,
            "nyheter": nyheter,
        }
    )
