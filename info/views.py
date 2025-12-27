from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings

def om_u3a_norge(request):
    return render(request, "info/om_u3a_norge.html")

def for_pressen(request):
    return render(request, "info/for_pressen.html")

def bli_med(request):
    return render(request, "info/bli_med.html")


def starte_u3a(request):
    if request.method == "POST":
        navn = request.POST.get("navn")
        epost = request.POST.get("epost")
        sted = request.POST.get("sted")
        melding = request.POST.get("melding")

        send_mail(
            subject="Ønske om å starte U3A lokalt",
            message=(
                f"Navn: {navn}\n"
                f"E-post: {epost}\n"
                f"Sted: {sted}\n\n"
                f"Melding:\n{melding}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["post@u3a.no"],
        )

        return render(request, "info/starte_u3a_takk.html")

    return render(request, "info/starte_u3a.html")

