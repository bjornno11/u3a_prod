# forside/views.py
from django.shortcuts import render
from lag.models import Aktivitet


def forside_view(request):
    aktiviteter = (
        Aktivitet.objects
        .filter(publisert=True)
        .select_related("lag")
        .order_by("-dato", "-opprettet")[:10]  # siste 10
    )

    context = {
        "aktiviteter": aktiviteter,
    }
    return render(request, "index.html", context)
