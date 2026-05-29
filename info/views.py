from django.core.mail import send_mail
from .forms import U3AKontaktForm
from django.shortcuts import render
from django.conf import settings
from django.core.mail import EmailMessage
import logging

logger = logging.getLogger(__name__)

def u3a_norge(request):
    sendt = False

    if request.method == "POST":
        form = U3AKontaktForm(request.POST)

        if form.is_valid():
            cd = form.cleaned_data

            subject = f"Kontakt fra U3A Norge-siden: {cd['navn']}"

            message = f"""
Navn: {cd['navn']}
E-post: {cd['epost']}
Lokallag / organisasjon: {cd.get('lokallag', '')}
Kommune: {cd.get('kommune', '')}

Melding:
{cd['melding']}
"""

            send_mail(
                subject,
                message,
                "u3a@u3a.no",
                ["u3a@u3a.no"],
                fail_silently=False,
            )

            sendt = True
            form = U3AKontaktForm()
    else:
        form = U3AKontaktForm()

    return render(request, "info/u3a_norge.html", {
        "form": form,
        "sendt": sendt,
    })
def om_u3a_no(request):
    return render(request, "info/om_u3a_no.html")

def om_u3a_norge(request):
    return render(request, "info/om_u3a_norge.html")


def for_pressen(request):
    return render(request, "info/for_pressen.html")


def bli_med(request):
    return render(request, "info/bli_med.html")


def starte_u3a(request):
    if request.method == "POST":
        # Honeypot: bot -> vis takk-side, men ikke send e-post
        if (request.POST.get("hp_fax") or "").strip():
            return render(request, "info/starte_u3a_takk.html")

        navn = (request.POST.get("navn") or "").strip()
        epost = (request.POST.get("epost") or "").strip()
        sted = (request.POST.get("sted") or "").strip()
        melding = (request.POST.get("melding") or "").strip()

        subject = f"U3A – ønske om å starte lokallag ({sted or 'ikke oppgitt'})"
        body = (
            f"Navn: {navn or 'ikke oppgitt'}\n"
            f"E-post: {epost or 'ikke oppgitt'}\n"
            f"Sted/kommune: {sted or 'ikke oppgitt'}\n\n"
            f"Melding:\n{melding or 'ikke oppgitt'}"
        )

        # 1) Hovedmail til U3A
        try:
            msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=["u3a@u3a.no"],
            )
            if epost:
                msg.reply_to = [epost]

            msg.send(fail_silently=False)

        except Exception as e:
            logger.exception("E-post sending feilet i starte_u3a: %s", e)
            # Vis takk-siden uansett (ingen 500 til bruker)
            return render(request, "info/starte_u3a_takk.html")

        # 2) Bekreftelse til avsender
        if epost:
            try:
                confirm_subject = "U3A Norge – vi har mottatt din henvendelse"
                confirm_body = (
                    f"Hei{f' {navn}' if navn else ''},\n\n"
                    "Takk for at du tok kontakt med U3A Norge.\n"
                    "Vi har mottatt din forespørsel om å starte U3A lokalt"
                    f"{f' i {sted}' if sted else ''}.\n\n"
                    "Vi tar kontakt med deg så snart som mulig.\n\n"
                    "Vennlig hilsen\n"
                    "U3A Norge\n"
                    "https://u3a.no"
                )

                EmailMessage(
                    subject=confirm_subject,
                    body=confirm_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[epost],
                ).send(fail_silently=False)

            except Exception as e:
                logger.exception("Bekreftelsesmail feilet: %s", e)

        return render(request, "info/starte_u3a_takk.html")

    return render(request, "info/starte_u3a.html")
