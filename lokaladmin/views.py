from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from lag.models import Organisasjon, Aktivitet, Dokument, Bilde, LagMedlemVerv, LagMedlem, LagRolle, LagUtvalg, Medlemsgruppe, SmsLeverandor, SmsLogg, SmsUtsending
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib.auth.models import User
import calendar, csv
from datetime import date
from django.http import FileResponse, Http404, HttpResponse
from django.db.models import Q
from lokaladmin.sms_service import send_sms_logg
from lag.models import Nyhet

@login_required
def dashboard(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    return render(
        request,
        "lokaladmin/dashboard.html",
        {
            "organisasjon": organisasjon,
        }
    )

@login_required
def styre_organisasjon(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    return render(
        request,
        "lokaladmin/styre_organisasjon.html",
        {
            "organisasjon": organisasjon,
        }
    )

@login_required
def styremedlemmer(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    verv = LagMedlemVerv.objects.filter(
        organisasjon=organisasjon
    ).select_related(
        "medlem",
        "rolle",
        "utvalg",
    ).order_by(
        "rolle__navn",
        "medlem__etternavn",
        "medlem__fornavn",
    )

    return render(
        request,
        "lokaladmin/styremedlemmer.html",
        {
            "organisasjon": organisasjon,
            "verv": verv,
        }
    )


@login_required
def styremedlem_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).exclude(
        user__in=organisasjon.redaktorer.all()
    ).order_by("etternavn", "fornavn")

    if request.method == "POST":
        medlem_id = request.POST.get("medlem")

        medlem = get_object_or_404(
            LagMedlem,
            id=medlem_id,
            organisasjon=organisasjon
        )

        if not medlem.user:
            user = opprett_loginbruker_for_medlem(medlem)
        else:
            user = medlem.user

        organisasjon.redaktorer.add(user)

        messages.success(request, "Redaktøren ble lagt til.")
        return redirect("lokaladmin:redaktorer")

    return render(
        request,
        "lokaladmin/redaktor_skjema.html",
        {
            "organisasjon": organisasjon,
            "medlemmer": medlemmer,
        }
    )

@login_required
def styremedlem_rediger(request, verv_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    verv = get_object_or_404(
        LagMedlemVerv,
        id=verv_id,
        organisasjon=organisasjon,
    )

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon,
        aktiv=True
    ).order_by("etternavn", "fornavn")

    roller = LagRolle.objects.all().order_by("navn")
    utvalg = LagUtvalg.objects.all().order_by("navn")

    if request.method == "POST":

        medlem = get_object_or_404(
            LagMedlem,
            id=request.POST.get("medlem"),
            organisasjon=organisasjon,
        )

        rolle = get_object_or_404(
            LagRolle,
            id=request.POST.get("rolle"),
        )

        verv.medlem = medlem
        verv.rolle = rolle

        utvalg_id = request.POST.get("utvalg") or None

        if utvalg_id:
            verv.utvalg = get_object_or_404(LagUtvalg, id=utvalg_id)
        else:
            verv.utvalg = None

        verv.fra_dato = request.POST.get("fra_dato") or None
        verv.til_dato = request.POST.get("til_dato") or None
        verv.valgt_dato = request.POST.get("valgt_dato") or None
        verv.valgt_av = request.POST.get("valgt_av", "").strip()
        verv.merknad = request.POST.get("merknad", "").strip()
        verv.aktiv = bool(request.POST.get("aktiv"))

        verv.save()

        messages.success(request, "Vervet ble oppdatert.")
        return redirect("lokaladmin:styremedlemmer")

    return render(
        request,
        "lokaladmin/styremedlem_skjema.html",
        {
            "organisasjon": organisasjon,
            "verv": verv,
            "medlemmer": medlemmer,
            "roller": roller,
            "utvalg": utvalg,
        }
    )


@login_required
def styremedlem_slett(request, verv_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    verv = get_object_or_404(
        LagMedlemVerv,
        id=verv_id,
        organisasjon=organisasjon,
    )

    verv.delete()

    messages.success(request, "Vervet ble slettet.")
    return redirect("lokaladmin:styremedlemmer")

@login_required
def roller(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    roller = LagRolle.objects.all().order_by("navn")

    return render(
        request,
        "lokaladmin/roller.html",
        {
            "organisasjon": organisasjon,
            "roller": roller,
        }
    )

@login_required
def rolle_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    if request.method == "POST":

        navn = request.POST.get("navn", "").strip()
        beskrivelse = request.POST.get("beskrivelse", "").strip()

        if not navn:
            messages.error(request, "Rollen må ha et navn.")
        else:

            LagRolle.objects.create(
                navn=navn,
                beskrivelse=beskrivelse,
            )

            messages.success(request, "Rollen ble opprettet.")
            return redirect("lokaladmin:roller")

    return render(
        request,
        "lokaladmin/rolle_skjema.html",
        {
            "organisasjon": organisasjon,
            "rolle": None,
        }
    )

@login_required
def rolle_rediger(request, rolle_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    rolle = get_object_or_404(LagRolle, id=rolle_id)

    if request.method == "POST":
        navn = request.POST.get("navn", "").strip()
        beskrivelse = request.POST.get("beskrivelse", "").strip()

        if not navn:
            messages.error(request, "Rollen må ha et navn.")
        else:
            rolle.navn = navn
            rolle.beskrivelse = beskrivelse
            rolle.save()

            messages.success(request, "Rollen ble oppdatert.")
            return redirect("lokaladmin:roller")

    return render(
        request,
        "lokaladmin/rolle_skjema.html",
        {
            "organisasjon": organisasjon,
            "rolle": rolle,
        }
    )
@login_required
def rolle_slett(request, rolle_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    rolle = get_object_or_404(LagRolle, id=rolle_id)

    if LagMedlemVerv.objects.filter(rolle=rolle).exists():
        messages.error(request, "Rollen er i bruk og kan ikke slettes.")
        return redirect("lokaladmin:roller")

    rolle.delete()

    messages.success(request, "Rollen ble slettet.")
    return redirect("lokaladmin:roller")

@login_required
def redaktorer(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    redaktorer = organisasjon.redaktorer.all().order_by(
        "last_name",
        "first_name",
        "username"
    )
    return render(
        request,
        "lokaladmin/redaktorer.html",
        {
            "organisasjon": organisasjon,
            "redaktorer": redaktorer,
        }
    )

def opprett_loginbruker_for_medlem(medlem):
    if medlem.user:
        return medlem.user

    username = medlem.epost.strip().lower() if medlem.epost else f"medlem-{medlem.id}"

    base_username = username
    teller = 1

    while User.objects.filter(username=username).exists():
        teller += 1
        username = f"{base_username}-{teller}"

    user = User.objects.create_user(
        username=username,
        email=medlem.epost or "",
        first_name=medlem.fornavn or "",
        last_name=medlem.etternavn or "",
    )

    user.set_unusable_password()
    user.is_staff = True
    user.save()

    medlem.user = user
    medlem.save(update_fields=["user"])

    return user


@login_required
def redaktor_legg_til(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon,
        aktiv=True,
    ).exclude(
        user__in=organisasjon.redaktorer.all()
    ).order_by("etternavn", "fornavn")
    if request.method == "POST":
        medlem_id = request.POST.get("medlem")

        medlem = get_object_or_404(
            LagMedlem,
            id=medlem_id,
            organisasjon=organisasjon
        )

        if not medlem.user:
            user = opprett_loginbruker_for_medlem(medlem)
        else:
            user = medlem.user

        organisasjon.redaktorer.add(user)
        messages.success(request, "Redaktøren ble lagt til.")
        return redirect("lokaladmin:redaktorer")

    return render(
        request,
        "lokaladmin/redaktor_skjema.html",
        {
            "organisasjon": organisasjon,
            "medlemmer": medlemmer,
        }
    )

@login_required
def redaktor_fjern(request, user_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    bruker = get_object_or_404(User, id=user_id)

    if bruker not in organisasjon.redaktorer.all():
        messages.error(request, "Brukeren er ikke redaktør i dette lokallaget.")
        return redirect("lokaladmin:redaktorer")
    if bruker == request.user:
        messages.error(request, "Du kan ikke fjerne deg selv som redaktør.")
        return redirect("lokaladmin:redaktorer")

    organisasjon.redaktorer.remove(bruker)

    messages.success(request, "Redaktøren ble fjernet.")
    return redirect("lokaladmin:redaktorer")

@login_required
def utvalg(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    utvalg = LagUtvalg.objects.all().order_by("navn")

    return render(
        request,
        "lokaladmin/utvalg.html",
        {
            "organisasjon": organisasjon,
            "utvalg": utvalg,
        }
    )


@login_required
def utvalg_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    if request.method == "POST":
        navn = request.POST.get("navn", "").strip()
        beskrivelse = request.POST.get("beskrivelse", "").strip()

        if not navn:
            messages.error(request, "Utvalget må ha et navn.")
        else:
            LagUtvalg.objects.create(
                navn=navn,
                beskrivelse=beskrivelse,
            )

            messages.success(request, "Utvalget ble opprettet.")
            return redirect("lokaladmin:utvalg")

    return render(
        request,
        "lokaladmin/utvalg_skjema.html",
        {
            "organisasjon": organisasjon,
            "utvalg_objekt": None,
        }
    )


@login_required
def utvalg_rediger(request, utvalg_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    utvalg_objekt = get_object_or_404(LagUtvalg, id=utvalg_id)

    if request.method == "POST":
        navn = request.POST.get("navn", "").strip()
        beskrivelse = request.POST.get("beskrivelse", "").strip()

        if not navn:
            messages.error(request, "Utvalget må ha et navn.")
        else:
            utvalg_objekt.navn = navn
            utvalg_objekt.beskrivelse = beskrivelse
            utvalg_objekt.save()

            messages.success(request, "Utvalget ble oppdatert.")
            return redirect("lokaladmin:utvalg")

    return render(
        request,
        "lokaladmin/utvalg_skjema.html",
        {
            "organisasjon": organisasjon,
            "utvalg_objekt": utvalg_objekt,
        }
    )


@login_required
def utvalg_slett(request, utvalg_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    utvalg_objekt = get_object_or_404(LagUtvalg, id=utvalg_id)

    if LagMedlemVerv.objects.filter(utvalg=utvalg_objekt).exists():
        messages.error(request, "Utvalget er i bruk og kan ikke slettes.")
        return redirect("lokaladmin:utvalg")

    utvalg_objekt.delete()

    messages.success(request, "Utvalget ble slettet.")
    return redirect("lokaladmin:utvalg")


@login_required
def forside(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Din bruker er ikke koblet til et lokallag.")
        return redirect("lokaladmin:dashboard")

    if request.method == "POST":
        organisasjon.forside_tittel = request.POST.get("forside_tittel", "")
        organisasjon.forside_ingress = request.POST.get("forside_ingress", "")
        organisasjon.forside_tekst = request.POST.get("forside_tekst", "")
        organisasjon.footer_tekst = request.POST.get("footer_tekst", "")
        organisasjon.epost = request.POST.get("epost", "")
        organisasjon.telefon = request.POST.get("telefon", "")
        if request.FILES.get("forside_bilde"):
            organisasjon.forside_bilde = request.FILES["forside_bilde"]

        organisasjon.save()
        messages.success(request, "Forsiden er oppdatert.")
        return redirect("lokaladmin:forside")

    return render(
        request,
        "lokaladmin/forside.html",
        {
            "organisasjon": organisasjon,
        }
    )
@login_required
def aktiviteter(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    aktiviteter = Aktivitet.objects.filter(
        organisasjon=organisasjon
    ).order_by("-dato")

    year = request.GET.get("year")
    month = request.GET.get("month")

    today = timezone.localdate()

    try:
        year = int(year) if year else today.year
        month = int(month) if month else today.month
    except ValueError:
        year = today.year
        month = today.month

    cal = calendar.Calendar(firstweekday=0)

    calendar_weeks = cal.monthdatescalendar(
        year,
        month
    )

    current_month = date(year, month, 1)

    if month == 1:
        prev_month = (year - 1, 12)
    else:
        prev_month = (year, month - 1)

    if month == 12:
        next_month = (year + 1, 1)
    else:
        next_month = (year, month + 1)


    aktivitet_datoer = set(
        aktiviteter.values_list("dato", flat=True)
    )

    return render(
        request,
        "lokaladmin/aktiviteter.html",
        {
            "organisasjon": organisasjon,
            "aktiviteter": aktiviteter,
            "calendar_weeks": calendar_weeks,
            "aktivitet_datoer": aktivitet_datoer,
            "today": today,
            "current_month": current_month,
            "prev_month": prev_month,
            "next_month": next_month,
        }
    )

@login_required
def aktivitet_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    if request.method == "POST":
        aktivitet = Aktivitet(
            organisasjon=organisasjon,
            tittel=request.POST.get("tittel", ""),
            kortinfo=request.POST.get("kortinfo", ""),
            sted=request.POST.get("sted", ""),
            beskrivelse=request.POST.get("beskrivelse", ""),
            dato=request.POST.get("dato") or timezone.localdate(),
            publisert=bool(request.POST.get("publisert")),
            pamelding_aktiv=bool(request.POST.get("pamelding_aktiv")),
            starttid=request.POST.get("starttid") or None,
            sluttid=request.POST.get("sluttid") or None,
        )

        aktivitet.slug = slugify(aktivitet.tittel)[:50]
        if request.FILES.get("bilde"):
            aktivitet.bilde = request.FILES["bilde"]

        if request.FILES.get("vedlegg"):
            aktivitet.vedlegg = request.FILES["vedlegg"]
        aktivitet.save()

        messages.success(request, "Aktiviteten er opprettet.")
        return redirect("lokaladmin:aktiviteter")

    return render(
        request,
        "lokaladmin/aktivitet_skjema.html",
        {
            "organisasjon": organisasjon,
            "aktivitet": None,
        }
    )
@login_required
def aktivitet_rediger(request, aktivitet_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    aktivitet = Aktivitet.objects.filter(
        id=aktivitet_id,
        organisasjon=organisasjon
    ).first()

    if not aktivitet:
        messages.error(request, "Fant ikke aktiviteten.")
        return redirect("lokaladmin:aktiviteter")

    if request.method == "POST":
        aktivitet.tittel = request.POST.get("tittel", "")
        aktivitet.kortinfo = request.POST.get("kortinfo", "")
        aktivitet.sted = request.POST.get("sted", "")
        aktivitet.beskrivelse = request.POST.get("beskrivelse", "")
        aktivitet.dato = request.POST.get("dato") or timezone.localdate()
        aktivitet.publisert = bool(request.POST.get("publisert"))
        aktivitet.pamelding_aktiv = bool(request.POST.get("pamelding_aktiv"))
        aktivitet.starttid = request.POST.get("starttid") or None
        aktivitet.sluttid = request.POST.get("sluttid") or None

        if request.FILES.get("bilde"):
            aktivitet.bilde = request.FILES["bilde"]

        if request.FILES.get("vedlegg"):
            aktivitet.vedlegg = request.FILES["vedlegg"]

        if aktivitet.tittel:
            aktivitet.slug = slugify(aktivitet.tittel)[:50]

        aktivitet.save()

        messages.success(request, "Aktiviteten er oppdatert.")
        return redirect("lokaladmin:aktiviteter")

    return render(
        request,
        "lokaladmin/aktivitet_skjema.html",
        {
            "organisasjon": organisasjon,
            "aktivitet": aktivitet,
        }
    )

@login_required
def logg_ut(request):
    logout(request)
    return redirect("/")

@login_required
def medlemmer(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    return render(
        request,
        "lokaladmin/medlemmer.html",
        {
            "organisasjon": organisasjon,
        }
    )

@login_required
def medlemsliste(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    q = request.GET.get("q", "").strip()
    gruppe_id = request.GET.get("gruppe", "").strip()
    status = request.GET.get("status", "").strip()

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon
    ).select_related("gruppe")

    if q:
        medlemmer = medlemmer.filter(
            Q(fornavn__icontains=q) |
            Q(etternavn__icontains=q) |
            Q(epost__icontains=q) |
            Q(telefon__icontains=q)
        )

    if gruppe_id:
        medlemmer = medlemmer.filter(gruppe_id=gruppe_id)

    if status:
        medlemmer = medlemmer.filter(status=status)

    medlemmer = medlemmer.order_by("etternavn", "fornavn")

    grupper = Medlemsgruppe.objects.filter(
        organisasjon=organisasjon,
        aktiv=True
    ).order_by("navn")

    return render(
        request,
        "lokaladmin/medlemsliste.html",
        {
            "organisasjon": organisasjon,
            "medlemmer": medlemmer,
            "grupper": grupper,
            "q": q,
            "valgt_gruppe": gruppe_id,
            "valgt_status": status,
        }
    )

@login_required
def medlemsliste_csv(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon
    ).select_related("gruppe").order_by("etternavn", "fornavn")

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="medlemsliste.csv"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Etternavn", "Fornavn", "Gruppe", "E-post", "Telefon", "Status"])

    for m in medlemmer:
        writer.writerow([
            m.etternavn,
            m.fornavn,
            m.gruppe.navn if m.gruppe else "",
            m.epost,
            m.telefon,
            m.status,
        ])

    return response

@login_required
def medlem_rediger(request, medlem_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    medlem = get_object_or_404(
        LagMedlem,
        id=medlem_id,
        organisasjon=organisasjon
    )

    grupper = Medlemsgruppe.objects.filter(
        organisasjon=organisasjon,
        aktiv=True
    ).order_by("navn")

    if request.method == "POST":
        medlem.fornavn = request.POST.get("fornavn", "").strip()
        medlem.etternavn = request.POST.get("etternavn", "").strip()
        medlem.epost = request.POST.get("epost", "").strip()
        medlem.telefon = request.POST.get("telefon", "").strip()
        medlem.adresse = request.POST.get("adresse", "").strip()
        medlem.postnummer = request.POST.get("postnummer", "").strip()
        medlem.poststed = request.POST.get("poststed", "").strip()

        gruppe_id = request.POST.get("gruppe")
        if gruppe_id:
            medlem.gruppe = Medlemsgruppe.objects.filter(
                id=gruppe_id,
                organisasjon=organisasjon
            ).first()
        else:
            medlem.gruppe = None

        status = request.POST.get("status")
        if status:
            medlem.status = int(status)
        medlem.save()
        messages.success(request, "Medlem er lagret.")
        return redirect("lokaladmin:medlemsliste")

    return render(
        request,
        "lokaladmin/medlem_rediger.html",
        {
            "organisasjon": organisasjon,
            "medlem": medlem,
            "grupper": grupper,
            "status_choices": LagMedlem.STATUS_CHOICES,
        }
    )

@login_required
def medlemsgruppe_rediger(request, gruppe_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    gruppe = get_object_or_404(
        Medlemsgruppe,
        id=gruppe_id,
        organisasjon=organisasjon
    )

    if request.method == "POST":
        gruppe.navn = request.POST.get("navn", "").strip()
        gruppe.aktiv = request.POST.get("aktiv") == "on"

        if not gruppe.navn:
            messages.error(request, "Navn på gruppe må fylles ut.")
        else:
            gruppe.save()
            messages.success(request, "Medlemsgruppe er lagret.")
            return redirect("lokaladmin:medlemsgrupper")

    return render(
        request,
        "lokaladmin/medlemsgruppe_skjema.html",
        {
            "organisasjon": organisasjon,
            "gruppe": gruppe,
        }
    )

@login_required
def dokumenter(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    return render(
        request,
        "lokaladmin/dokumenter.html",
        {
            "organisasjon": organisasjon,
        }
    )

@login_required
def dokumentarkiv(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    kategori = request.GET.get("kategori")

    dokumenter = Dokument.objects.filter(
        organisasjon=organisasjon
    )

    if kategori:
        dokumenter = dokumenter.filter(
            kategori=kategori
        )

    dokumenter = dokumenter.order_by("-opprettet")

    return render(
        request,
        "lokaladmin/dokumentarkiv.html",
    {
        "organisasjon": organisasjon,
        "dokumenter": dokumenter,
        "valgt_kategori": kategori,
        "kategorier": Dokument.KATEGORIER,
    }
    )

@login_required
def dokument_nytt(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    if request.method == "POST":

        retur = request.GET.get("retur")

        dokument = Dokument(
            organisasjon=organisasjon,
            tittel=request.POST.get("tittel", ""),
            kategori=request.POST.get("kategori", ""),
            er_styredokument=(retur == "styredokumenter"),
            beskrivelse=request.POST.get("beskrivelse", ""),
            publisert=bool(request.POST.get("publisert")),
            opprettet_av=request.user,
        )

        if request.FILES.get("fil"):
            dokument.fil = request.FILES["fil"]

        dokument.save()

        messages.success(request, "Dokument lastet opp.")

        if retur == "styredokumenter":
            return redirect("lokaladmin:styredokumenter")

        return redirect("lokaladmin:dokumentarkiv")
    return render(
        request,
        "lokaladmin/dokument_skjema.html",
        {
            "organisasjon": organisasjon,
            "kategorier": Dokument.KATEGORIER,
        }
    )

@login_required
def bilder(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    bilder = Bilde.objects.filter(
        organisasjon=organisasjon,
        publisert=True
    ).order_by("-opprettet")

    return render(
        request,
        "lokaladmin/bilder.html",
        {
            "organisasjon": organisasjon,
            "bilder": bilder,
        }
    )

@login_required
def bilde_nytt(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    if request.method == "POST":

        bilde = Bilde(
            organisasjon=organisasjon,
            tittel=request.POST.get("tittel", ""),
            beskrivelse=request.POST.get("beskrivelse", ""),
            publisert=bool(request.POST.get("publisert")),
        )

        if request.FILES.get("bilde"):
            bilde.bilde = request.FILES["bilde"]

        bilde.save()

        messages.success(request, "Bilde lastet opp.")
        return redirect("lokaladmin:bilder")

    return render(
        request,
        "lokaladmin/bilde_skjema.html",
        {
            "organisasjon": organisasjon,
        }
    )

@login_required
def styre(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    verv = LagMedlemVerv.objects.filter(
        organisasjon=organisasjon
    ).select_related(
        "medlem",
        "rolle",
        "utvalg"
    ).order_by(
        "rolle__navn",
        "medlem__etternavn"
    )
    return render(
        request,
        "lokaladmin/styre.html",
        {
            "organisasjon": organisasjon,
            "verv": verv,
        }
    )

@login_required
def verv_nytt(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    medlemmer = LagMedlem.objects.filter(
        organisasjon=organisasjon,
        aktiv=True
    ).order_by("etternavn", "fornavn")

    roller = LagRolle.objects.all().order_by("navn")
    utvalg = LagUtvalg.objects.all().order_by("navn")

    if request.method == "POST":
        medlem_id = request.POST.get("medlem")
        rolle_id = request.POST.get("rolle")
        utvalg_id = request.POST.get("utvalg") or None
        fra_dato = request.POST.get("fra_dato") or None
        LagMedlemVerv.objects.create(
            organisasjon=organisasjon,
            medlem_id=medlem_id,
            rolle_id=rolle_id,
            utvalg_id=utvalg_id,
            aktiv=True,
            fra_dato=fra_dato,
        )

        messages.success(request, "Vervet er registrert.")
        return redirect("lokaladmin:styre")

    return render(
        request,
        "lokaladmin/verv_skjema.html",
        {
            "organisasjon": organisasjon,
            "medlemmer": medlemmer,
            "roller": roller,
            "utvalg": utvalg,
        }
    )

@login_required
def verv_rediger(request, verv_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    verv = LagMedlemVerv.objects.get(
        id=verv_id,
        organisasjon=organisasjon
    )

    if request.method == "POST":

        verv.fra_dato = request.POST.get("fra_dato") or None
        verv.til_dato = request.POST.get("til_dato") or None
        verv.aktiv = bool(request.POST.get("aktiv"))

        verv.save()

        messages.success(request, "Verv oppdatert.")

        return redirect("lokaladmin:styre")

    return render(
        request,
        "lokaladmin/verv_rediger.html",
        {
            "organisasjon": organisasjon,
            "verv": verv,
        }
    )

@login_required
def medlemsgrupper(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    grupper = Medlemsgruppe.objects.filter(
        organisasjon=organisasjon
    ).order_by("navn")

    return render(
        request,
        "lokaladmin/medlemsgrupper.html",
        {
            "organisasjon": organisasjon,
            "grupper": grupper,
        }
    )


@login_required
def medlemsgruppe_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    if request.method == "POST":
        navn = request.POST.get("navn", "").strip()
        aktiv = request.POST.get("aktiv") == "on"

        if not navn:
            messages.error(request, "Navn på gruppe må fylles ut.")
        else:
            Medlemsgruppe.objects.create(
                organisasjon=organisasjon,
                navn=navn,
                aktiv=aktiv
            )
            messages.success(request, "Medlemsgruppe er opprettet.")
            return redirect("lokaladmin:medlemsgrupper")

    return render(
        request,
        "lokaladmin/medlemsgruppe_skjema.html",
        {
            "organisasjon": organisasjon,
            "gruppe": None,
        }
    )

@login_required
def styredokumenter(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    dokumenter = Dokument.objects.filter(
        organisasjon=organisasjon,
        er_styredokument=True
    ).order_by("-opprettet")

    return render(
        request,
        "lokaladmin/styredokumenter.html",
        {
            "organisasjon": organisasjon,
            "dokumenter": dokumenter,
        }
    )

@login_required
def styredokument_last_ned(request, dokument_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        raise Http404("Ingen organisasjon koblet til brukeren.")

    dokument = get_object_or_404(
        Dokument,
        id=dokument_id,
        organisasjon=organisasjon,
        er_styredokument=True,
    )

    if not dokument.fil:
        raise Http404("Dokumentet har ingen fil.")

    return FileResponse(
        dokument.fil.open("rb"),
        as_attachment=False,
        filename=dokument.fil.name.split("/")[-1],
    )

@login_required
def dokument_detalj(request, dokument_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    dokument = Dokument.objects.get(
        id=dokument_id,
        organisasjon=organisasjon
    )

    return render(
        request,
        "lokaladmin/dokument_detalj.html",
        {
            "organisasjon": organisasjon,
            "dokument": dokument,
        }
    )

@login_required
def dokument_rediger(request, dokument_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    dokument = get_object_or_404(
        Dokument,
        id=dokument_id,
        organisasjon=organisasjon
    )

    if request.method == "POST":

        dokument.tittel = request.POST.get("tittel", "")
        dokument.kategori = request.POST.get("kategori", "annet")
        dokument.beskrivelse = request.POST.get("beskrivelse", "")
        dokument.er_styredokument = bool(request.POST.get("er_styredokument"))
        dokument.publisert = bool(request.POST.get("publisert"))

        if request.FILES.get("fil"):
            if dokument.fil:
                dokument.fil.delete(save=False)
            dokument.fil = request.FILES["fil"]

        dokument.save()

        messages.success(request, "Dokument oppdatert.")

        return redirect("lokaladmin:dokument_detalj", dokument_id=dokument.id)

    return render(
        request,
        "lokaladmin/dokument_rediger.html",
        {
            "organisasjon": organisasjon,
            "dokument": dokument,
            "kategorier": Dokument.KATEGORIER,
        }
    )


@login_required
def dokument_slett(request, dokument_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    dokument = get_object_or_404(
        Dokument,
        id=dokument_id,
        organisasjon=organisasjon
    )

    if request.method == "POST":

        retur_styre = dokument.er_styredokument

        if dokument.fil:
            dokument.fil.delete(save=False)

        dokument.delete()

        messages.success(request, "Dokument slettet.")

        if retur_styre:
            return redirect("lokaladmin:styredokumenter")

        return redirect("lokaladmin:dokumentarkiv")

    return render(
        request,
        "lokaladmin/dokument_slett.html",
        {
            "organisasjon": organisasjon,
            "dokument": dokument,
        }
    )

@login_required
def tekstmeldinger(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    leverandor = SmsLeverandor.objects.filter(
        organisasjon=organisasjon
    ).first()

    utsendinger = SmsUtsending.objects.filter(
        organisasjon=organisasjon
    ).order_by("-opprettet")[:10]

    return render(
        request,
        "lokaladmin/tekstmeldinger.html",
        {
            "organisasjon": organisasjon,
            "leverandor": leverandor,
            "utsendinger": utsendinger,
        }
    )
@login_required
def sms_innstillinger(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    leverandor, created = SmsLeverandor.objects.get_or_create(
        organisasjon=organisasjon
    )

    if request.method == "POST":
        leverandor.navn = request.POST.get("navn", "").strip()
        leverandor.api_url = request.POST.get("api_url", "").strip()
        leverandor.api_key = request.POST.get("api_key", "").strip()
        leverandor.api_secret = request.POST.get("api_secret", "").strip()
        leverandor.avsender = request.POST.get("avsender", "").strip()
        leverandor.aktiv = request.POST.get("aktiv") == "on"
        leverandor.testmodus = request.POST.get("testmodus") == "on"
        leverandor.save()

        messages.success(request, "SMS-innstillinger er lagret.")
        return redirect("lokaladmin:tekstmeldinger")

    return render(
        request,
        "lokaladmin/sms_innstillinger.html",
        {
            "organisasjon": organisasjon,
            "leverandor": leverandor,
        }
    )


@login_required
def sms_ny(request):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    grupper = Medlemsgruppe.objects.filter(
        organisasjon=organisasjon,
        aktiv=True
    ).order_by("navn")

    if request.method == "POST":

        melding = request.POST.get("melding", "").strip()
        gruppe_id = request.POST.get("gruppe")
        status = request.POST.get("status")

        medlemmer = LagMedlem.objects.filter(
            organisasjon=organisasjon
        )

        if status:
            medlemmer = medlemmer.filter(status=status)

        if gruppe_id:
            medlemmer = medlemmer.filter(gruppe_id=gruppe_id)

        mottakertekst = "Alle medlemmer"

        if status:
            status_navn = dict(LagMedlem.STATUS_CHOICES).get(int(status), status)
            mottakertekst = f"Status: {status_navn}"

        if gruppe_id:
            gruppe = Medlemsgruppe.objects.filter(
                id=gruppe_id,
                organisasjon=organisasjon
            ).first()

            if gruppe:
                mottakertekst += f" / Gruppe: {gruppe.navn}"

        utsending = SmsUtsending.objects.create(
            organisasjon=organisasjon,
            melding=melding,
            mottakertekst=mottakertekst,
            status=SmsUtsending.STATUS_KLADD,
        )

        antall = 0

        for medlem in medlemmer:

            if medlem.telefon:

                SmsLogg.objects.create(
                    organisasjon=organisasjon,
                    utsending=utsending,
                    medlem=medlem,
                    telefon=medlem.telefon,
                    melding=melding,
                    status=SmsLogg.STATUS_KLADD,
                )

                antall += 1

        utsending.antall_mottakere = antall
        utsending.save()

        messages.success(
            request,
            f"Tekstmelding er lagret som kladd for {antall} mottakere."
        )

        return redirect("lokaladmin:tekstmeldinger")
        return redirect("lokaladmin:tekstmeldinger")

    return render(
        request,
        "lokaladmin/sms_ny.html",
        {
            "organisasjon": organisasjon,
            "grupper": grupper,
            "status_choices": LagMedlem.STATUS_CHOICES,
        }
    )
@login_required
def sms_utsending_detalj(request, utsending_id):
    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    utsending = get_object_or_404(
        SmsUtsending,
        id=utsending_id,
        organisasjon=organisasjon
    )

    mottakere = SmsLogg.objects.filter(
        organisasjon=organisasjon,
        utsending=utsending
    ).select_related("medlem").order_by(
        "medlem__etternavn",
        "medlem__fornavn"
    )

    return render(
        request,
        "lokaladmin/sms_utsending_detalj.html",
        {
            "organisasjon": organisasjon,
            "utsending": utsending,
            "mottakere": mottakere,
        }
    )

@login_required
def sms_utsending_send(request, utsending_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    utsending = get_object_or_404(
        SmsUtsending,
        id=utsending_id,
        organisasjon=organisasjon
    )

    leverandor = SmsLeverandor.objects.filter(
        organisasjon=organisasjon
    ).first()

    if not leverandor:
        messages.error(request, "SMS-leverandør mangler.")
        return redirect(
            "lokaladmin:sms_utsending_detalj",
            utsending_id=utsending.id
        )

    mottakere = SmsLogg.objects.filter(
        organisasjon=organisasjon,
        utsending=utsending,
        status=SmsLogg.STATUS_KLADD,
    )

    sendt = 0
    feil = 0

    for logg in mottakere:

        ok = send_sms_logg(logg, leverandor)

        if ok:
            sendt += 1
        else:
            feil += 1

    if feil > 0:
        utsending.status = SmsUtsending.STATUS_FEIL
    elif leverandor.testmodus:
        utsending.status = SmsUtsending.STATUS_TEST
    else:
        utsending.status = SmsUtsending.STATUS_SENDT
    utsending.save()

    messages.success(
        request,
        f"SMS behandlet. OK: {sendt} / Feil: {feil}"
    )

    return redirect(
        "lokaladmin:sms_utsending_detalj",
        utsending_id=utsending.id
    )

@login_required
def sms_utsending_tilbakestill(request, utsending_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    utsending = get_object_or_404(
        SmsUtsending,
        id=utsending_id,
        organisasjon=organisasjon
    )

    SmsLogg.objects.filter(
        organisasjon=organisasjon,
        utsending=utsending,
        status=SmsLogg.STATUS_TEST,
    ).update(
        status=SmsLogg.STATUS_KLADD,
        leverandor_svar="",
        sendt_tid=None,
    )

    utsending.status = SmsUtsending.STATUS_KLADD
    utsending.save()

    messages.success(request, "Testutsending er tilbakestilt til kladd.")

    return redirect(
        "lokaladmin:sms_utsending_detalj",
        utsending_id=utsending.id
    )

@login_required
def sms_mottaker_slett(request, utsending_id, logg_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    utsending = get_object_or_404(
        SmsUtsending,
        id=utsending_id,
        organisasjon=organisasjon
    )

    logg = get_object_or_404(
        SmsLogg,
        id=logg_id,
        utsending=utsending,
        organisasjon=organisasjon
    )

    if logg.status != SmsLogg.STATUS_KLADD:
        messages.error(request, "Kan bare slette mottakere før sending.")
        return redirect(
            "lokaladmin:sms_utsending_detalj",
            utsending_id=utsending.id
        )

    logg.delete()

    utsending.antall_mottakere = SmsLogg.objects.filter(
        utsending=utsending,
        organisasjon=organisasjon
    ).count()
    utsending.save()

    messages.success(request, "Mottaker er slettet fra utsendingen.")

    return redirect(
        "lokaladmin:sms_utsending_detalj",
        utsending_id=utsending.id
    )

@login_required
def nyheter(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    nyheter = Nyhet.objects.filter(
        organisasjon=organisasjon
    )

    return render(
        request,
        "lokaladmin/nyheter.html",
        {
            "organisasjon": organisasjon,
            "nyheter": nyheter,
        }
    )

@login_required
def nyhet_ny(request):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    if request.method == "POST":

        nyhet = Nyhet.objects.create(
            organisasjon=organisasjon,
            tittel=request.POST.get("tittel"),
            ingress=request.POST.get("ingress"),
            tekst=request.POST.get("tekst"),
            publisert=bool(request.POST.get("publisert")),
            publisert_dato=request.POST.get("publisert_dato") or None,
            bilde=request.FILES.get("bilde"),
        )

        messages.success(request, "Nyheten ble opprettet.")
        return redirect("lokaladmin:nyheter")

    return render(
        request,
        "lokaladmin/nyhet_skjema.html",
        {
            "organisasjon": organisasjon,
        }
    )
@login_required
def nyhet_rediger(request, nyhet_id):

    organisasjon = Organisasjon.objects.filter(
        redaktorer=request.user
    ).first()

    if not organisasjon:
        messages.error(request, "Ingen organisasjon koblet til brukeren.")
        return redirect("lokaladmin:dashboard")

    nyhet = get_object_or_404(
        Nyhet,
        id=nyhet_id,
        organisasjon=organisasjon
    )

    if request.method == "POST":

        nyhet.tittel = request.POST.get("tittel")
        nyhet.ingress = request.POST.get("ingress")
        nyhet.tekst = request.POST.get("tekst")

        nyhet.publisert = bool(
            request.POST.get("publisert")
        )

        nyhet.publisert_dato = (
            request.POST.get("publisert_dato") or None
        )

        if request.FILES.get("bilde"):
            nyhet.bilde = request.FILES.get("bilde")

        nyhet.save()

        messages.success(request, "Nyheten ble oppdatert.")
        return redirect("lokaladmin:nyheter")

    return render(
        request,
        "lokaladmin/nyhet_skjema.html",
        {
            "organisasjon": organisasjon,
            "nyhet": nyhet,
        }
    )

