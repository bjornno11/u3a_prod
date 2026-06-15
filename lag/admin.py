from django.contrib import admin
from .models import (
    Organisasjon,
    Lokallag,
    Aktivitet,
    AktivitetPamelding,
    SiteConfig,
    LagMedlem,
    LagRolle,
    LagUtvalg,
    LagMedlemVerv,
    Postnummer,
    Arrangement,
    Nyhet,
    Dokument,
    Medlemsgruppe,
    SmsLeverandor,
    SmsLogg,
    Sidevisning,
)
from django.urls import path
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.models import User, Permission
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required

@admin.register(LagMedlem)
class LagMedlemAdmin(admin.ModelAdmin):
    change_list_template = "admin/lag/lagmedlem/change_list.html"
    list_display = (
        "etternavn",
        "fornavn",
        "gruppe",
        "status",
        "epost",
        "telefon",
        "organisasjon",
        "aktiv",
        "opprettet",
    )

    list_filter = (
        "organisasjon",
        "gruppe",
        "status",
        "aktiv",
    )

    search_fields = (
        "fornavn",
        "etternavn",
        "gruppe",
        "epost",
        "telefon",
        "adresse",
        "postnummer",
        "poststed",
    )

    ordering = (
        "organisasjon",
        "etternavn",
        "fornavn",
        "gruppe",
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "gruppe" and not request.user.is_superuser:
            organisasjon = Organisasjon.objects.filter(
                redaktorer=request.user
            ).first()

            if organisasjon:
                kwargs["queryset"] = Medlemsgruppe.objects.filter(
                    organisasjon=organisasjon,
                    aktiv=True
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("organisasjon", "gruppe")
        if request.user.is_superuser:
            return qs
        org_ids = Organisasjon.objects.filter(redaktorer=request.user).values_list("id", flat=True)
        return qs.filter(organisasjon_id__in=org_ids)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        return ("organisasjon",)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and obj.organisasjon_id is None:
            org = Organisasjon.objects.filter(redaktorer=request.user).first()
            if org:
                obj.organisasjon = org
        super().save_model(request, obj, form, change)
    actions = ["godkjenn_medlemmer", "sett_som_utmeldt"]
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "godkjenn/",
                self.admin_site.admin_view(self.godkjenn_redirect)
            ),
        ]
        return custom_urls + urls

    def godkjenn_redirect(self, request):
        return redirect("/godkjenn-medlemmer/")

    @admin.action(description="Godkjenn valgte medlemmer")
    def godkjenn_medlemmer(self, request, queryset):
        queryset.update(status=LagMedlem.STATUS_GODKJENT, aktiv=True)

    @admin.action(description="Sett valgte medlemmer som utmeldt")
    def sett_som_utmeldt(self, request, queryset):
        queryset.update(status=LagMedlem.STATUS_UTMELDT, aktiv=False)


@admin.register(LagRolle)
class LagRolleAdmin(admin.ModelAdmin):
    list_display = ("navn", "beskrivelse")
    search_fields = ("navn",)


@admin.register(LagUtvalg)
class LagUtvalgAdmin(admin.ModelAdmin):
    list_display = ("navn", "beskrivelse")
    search_fields = ("navn",)


@admin.register(LagMedlemVerv)
class LagMedlemVervAdmin(admin.ModelAdmin):
    list_display = (
        "medlem",
        "organisasjon",
        "rolle",
        "utvalg",
        "fra_dato",
        "til_dato",
        "aktiv",
    )
    list_filter = ("organisasjon", "rolle", "utvalg", "aktiv")
    search_fields = (
        "medlem__fornavn",
        "medlem__etternavn",
        "rolle__navn",
        "utvalg__navn",
    )
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "medlem":
            organisasjon_id = request.GET.get("organisasjon")
            if organisasjon_id:
                kwargs["queryset"] = LagMedlem.objects.filter(organisasjon_id=organisasjon_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Medlemsgruppe)
class MedlemsgruppeAdmin(admin.ModelAdmin):
    list_display = ("navn", "organisasjon", "aktiv")
    list_filter = ("organisasjon", "aktiv")
    search_fields = ("navn", "organisasjon__organisasjon")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("organisasjon")

        if request.user.is_superuser:
            return qs

        org_ids = Organisasjon.objects.filter(
            redaktorer=request.user
        ).values_list("id", flat=True)

        return qs.filter(organisasjon_id__in=org_ids)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organisasjon" and not request.user.is_superuser:
            kwargs["queryset"] = Organisasjon.objects.filter(
                redaktorer=request.user
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Organisasjon)
class OrganisasjonAdmin(admin.ModelAdmin):
    change_list_template = "admin/lag/organisasjon/change_list.html"
    list_display = ("organisasjon", "fylke", "kommune", "status", "lenke_status")
    list_filter = ("fylke", "status", "lenke_status")
    search_fields = ("organisasjon", "kommune", "fylke", "nettside", "epost")

    REDAKTOR_FELTER = (
        "organisasjon",
        "adresse",
        "nettside",
        "epost",
        "telefon",
        "forside_tittel",
        "forside_ingress",
        "forside_tekst",
        "forside_bilde",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(redaktorer=request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        perm = super().has_change_permission(request, obj=obj)
        if not perm:
            return False
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return obj.redaktorer.filter(pk=request.user.pk).exists()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        all_fields = [f.name for f in self.model._meta.fields]
        allowed = set(self.REDAKTOR_FELTER)
        readonly = [f for f in all_fields if f not in allowed]
        return tuple(readonly)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        return (
            ("Grunninfo", {"fields": ("organisasjon", "adresse", "nettside", "epost", "telefon")}),
            ("Forside", {"fields": ("forside_tittel", "forside_ingress", "forside_tekst", "forside_bilde")}),
        )


@admin.register(Aktivitet)
class AktivitetAdmin(admin.ModelAdmin):
    list_display = ("dato", "tittel", "owner_name", "publisert", "pamelding_aktiv")
    list_filter = ("publisert", "pamelding_aktiv", "dato")
    search_fields = ("tittel", "kortinfo", "beskrivelse")
    prepopulated_fields = {"slug": ("tittel",)}

    def owner_name(self, obj):
        if obj.organisasjon:
            return obj.organisasjon.organisasjon
        return obj.lag.navn
    owner_name.short_description = "Lokallag"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("organisasjon", "lag")
        if request.user.is_superuser:
            return qs
        org_ids = list(Organisasjon.objects.filter(redaktorer=request.user).values_list("id", flat=True))
        return qs.filter(organisasjon_id__in=org_ids)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        # Redaktør skal ikke kunne velge eierskap
        return ("organisasjon", "lag")

    def save_model(self, request, obj, form, change):
        # Sett eierskap automatisk ved opprettelse
        if not request.user.is_superuser and obj.organisasjon_id is None:
            org = Organisasjon.objects.filter(redaktorer=request.user).first()
            if org:
                obj.organisasjon = org
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Valgfritt: la redaktør slette egne aktiviteter eller ikke
        if request.user.is_superuser:
            return True
        return True

@admin.register(AktivitetPamelding)
class AktivitetPameldingAdmin(admin.ModelAdmin):
    list_display = ("opprettet", "navn", "epost", "telefon", "aktivitet")
    list_filter = ("aktivitet", "opprettet")
    search_fields = ("navn", "epost", "telefon", "aktivitet__tittel")
    readonly_fields = ("opprettet",)

@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = ("hoved_epost", "sist_endret")

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Lokallag)
class LokallagAdmin(admin.ModelAdmin):
    """
    DEPRECATED: Skjules for redaktører. Superuser kan fortsatt se den.
    """
    list_display = ("navn", "slug")
    prepopulated_fields = {"slug": ("navn",)}
    search_fields = ("navn",)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Postnummer)
class PostnummerAdmin(admin.ModelAdmin):
    list_display = ("postnummer", "poststed", "kommune", "fylke")
    search_fields = ("postnummer", "poststed", "kommune")
    ordering = ("postnummer",)

def subdomene_admin_lenke():
    url = reverse("subdomene_start")
    return format_html('<a class="button" href="{}">Aktiver / vedlikehold subdomene</a>', url)

@admin.register(Arrangement)
class ArrangementAdmin(admin.ModelAdmin):
    list_display = (
        "dato",
        "starttid",
        "tittel",
        "sted",
        "organisasjon",
        "publisert",
    )

    list_filter = (
        "organisasjon",
        "publisert",
        "dato",
    )

    search_fields = (
        "tittel",
        "sted",
        "foredragsholder",
        "ingress",
    )

    ordering = (
        "dato",
        "starttid",
    )

    fields = (
        "organisasjon",
        "tittel",
        "dato",
        "starttid",
        "sluttid",
        "sted",
        "foredragsholder",
        "ingress",
        "beskrivelse",
        "publisert",
    )
def get_queryset(self, request):
    qs = super().get_queryset(request)
    if request.user.is_superuser:
        return qs

    org_ids = Organisasjon.objects.filter(
        redaktorer=request.user
    ).values_list("id", flat=True)

    return qs.filter(organisasjon_id__in=org_ids)

def get_readonly_fields(self, request, obj=None):
    if request.user.is_superuser:
        return ()
    return ("organisasjon",)

def save_model(self, request, obj, form, change):
    if not request.user.is_superuser and obj.organisasjon_id is None:
        org = Organisasjon.objects.filter(
            redaktorer=request.user
        ).first()

        if org:
            obj.organisasjon = org

    super().save_model(request, obj, form, change)
@admin.register(Nyhet)
class NyhetAdmin(admin.ModelAdmin):

    list_display = (
        "tittel",
        "organisasjon",
        "publisert",
        "publisert_dato",
    )

    list_filter = (
        "organisasjon",
        "publisert",
    )

    search_fields = (
        "tittel",
        "ingress",
        "tekst",
    )

    ordering = (
        "-publisert_dato",
        "-opprettet",
    )

    fields = (
        "organisasjon",
        "tittel",
        "ingress",
        "tekst",
        "bilde",
        "publisert",
        "publisert_dato",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        org_ids = Organisasjon.objects.filter(
            redaktorer=request.user
        ).values_list("id", flat=True)

        return qs.filter(organisasjon_id__in=org_ids)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()

        return ("organisasjon",)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and obj.organisasjon_id is None:
            org = Organisasjon.objects.filter(
                redaktorer=request.user
            ).first()

            if org:
                obj.organisasjon = org

        super().save_model(request, obj, form, change)

@staff_member_required
def subadmin_start(request, org_id=None):
    if not request.user.is_superuser:
        return HttpResponse("Ingen tilgang")

    if org_id:
        org = Organisasjon.objects.get(id=org_id)

        if request.method == "POST" and request.POST.get("action") == "deactivate":
            user_id = request.POST.get("user_id")
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            return redirect(request.path)

        if request.method == "POST":
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "").strip()
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            email = request.POST.get("email", "").strip()

            if username and password:
                if User.objects.filter(username=username).exists():
                    return HttpResponse(f"Brukernavnet {username} finnes allerede.")

                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )

                user.is_staff = True
                user.is_active = True
                user.save()

                permissions = Permission.objects.filter(
                    content_type__app_label="lag",
                    codename__in=[
                        "view_organisasjon",
                        "change_organisasjon",
                        "view_aktivitet",
                        "add_aktivitet",
                        "change_aktivitet",
                        "view_arrangement",
                        "add_arrangement",
                        "change_arrangement",
                        "view_nyhet",
                        "add_nyhet",
                        "change_nyhet",
                        "view_lagmedlem",
                        "add_lagmedlem",
                        "change_lagmedlem",
                    ]
                )

                user.user_permissions.set(permissions)
                user.save()

                org.redaktorer.add(user)
                org.save()

                return redirect(request.path)

        return render(request, "admin/lag/subadmin_detalj.html", {
            "org": org,
            "redaktorer": org.redaktorer.all().order_by("username"),
        })

    organisasjoner = Organisasjon.objects.all().order_by("organisasjon")

    return render(request, "admin/lag/subadmin_start.html", {
        "organisasjoner": organisasjoner,
    })
from django.contrib.auth import logout

def u3a_logout(request):
    logout(request)
    return redirect("/")

@admin.register(Dokument)
class DokumentAdmin(admin.ModelAdmin):

    list_display = (
        "tittel",
        "kategori",
        "organisasjon",
        "publisert",
        "opprettet",
    )

    list_filter = (
        "organisasjon",
        "kategori",
        "publisert",
    )

    search_fields = (
        "tittel",
        "beskrivelse",
    )

@admin.register(SmsLeverandor)
class SmsLeverandorAdmin(admin.ModelAdmin):
    list_display = (
        "organisasjon",
        "navn",
        "avsender",
        "aktiv",
        "testmodus",
    )

    list_filter = (
        "aktiv",
        "testmodus",
    )

    search_fields = (
        "organisasjon__organisasjon",
        "navn",
    )

@admin.register(SmsLogg)
class SmsLoggAdmin(admin.ModelAdmin):
    list_display = (
        "opprettet",
        "organisasjon",
        "telefon",
        "status",
    )

    list_filter = (
        "status",
        "organisasjon",
    )

    search_fields = (
        "telefon",
        "melding",
    )

    ordering = (
        "-opprettet",
    )

@admin.register(Sidevisning)
class SidevisningAdmin(admin.ModelAdmin):
    list_display = (
        "dato",
        "host",
        "sti",
        "antall",
        "sist_besokt",
    )

    list_filter = (
        "dato",
        "host",
    )

    search_fields = (
        "host",
        "sti",
    )

    ordering = (
        "-dato",
        "-antall",
    )

    readonly_fields = (
        "dato",
        "host",
        "sti",
        "antall",
        "sist_besokt",
    )

