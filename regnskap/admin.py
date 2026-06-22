from django.contrib import admin

from .models import (
    Regnskapsaar,
    Regnskapsperiode,
    Bilagsserie,
    Konto,
    Styrekode,
    Avdeling,
    Prosjekt,
    ReskontroKonto,
    Momskode,
    Bilag,
    Bilagslinje,
    SystemLogg,
)


class RegnskapsperiodeInline(admin.TabularInline):
    model = Regnskapsperiode
    extra = 0


@admin.register(Regnskapsaar)
class RegnskapsaarAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "aar", "navn", "fra_dato", "til_dato", "aktiv", "avsluttet")
    list_filter = ("aktiv", "avsluttet", "organisasjon")
    search_fields = ("navn", "organisasjon__organisasjon")
    inlines = [RegnskapsperiodeInline]


@admin.register(Konto)
class KontoAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "kontonummer", "kontonavn", "kontogruppe", "styrekode", "samlekonto", "aktiv")
    list_filter = ("organisasjon", "samlekonto", "aktiv")
    search_fields = ("kontonummer", "kontonavn")


@admin.register(Bilagsserie)
class BilagsserieAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "regnskapsaar", "kode", "navn", "neste_nummer", "standard_konto", "standard_fortegn", "aktiv")
    list_filter = ("organisasjon", "regnskapsaar", "aktiv")
    search_fields = ("kode", "navn")


@admin.register(Avdeling)
class AvdelingAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "avdelingsnummer", "navn", "ansvarlig_medlem", "fra_dato", "til_dato", "aktiv")
    list_filter = ("organisasjon", "aktiv")
    search_fields = ("avdelingsnummer", "navn")


@admin.register(Prosjekt)
class ProsjektAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "prosjektnummer", "navn", "ansvarlig_medlem", "fra_dato", "til_dato", "aktiv")
    list_filter = ("organisasjon", "aktiv")
    search_fields = ("prosjektnummer", "navn")


@admin.register(ReskontroKonto)
class ReskontroKontoAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "kontonummer", "navn", "reskontrotype", "samlekonto", "medlem", "aktiv")
    list_filter = ("organisasjon", "reskontrotype", "aktiv")
    search_fields = ("kontonummer", "navn")


@admin.register(Momskode)
class MomskodeAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "kode", "navn", "sats", "aktiv")
    list_filter = ("organisasjon", "aktiv")
    search_fields = ("kode", "navn")


class BilagslinjeInline(admin.TabularInline):
    model = Bilagslinje
    extra = 1


@admin.register(Bilag)
class BilagAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "regnskapsaar", "bilagsserie", "bilagsnummer", "bilagsdato", "foringsdato", "h_status", "bilagstekst", "sum_belop", "har_differanse")
    list_filter = ("organisasjon", "regnskapsaar", "bilagsserie", "h_status")
    search_fields = ("bilagsnummer", "bilagstekst")
    inlines = [BilagslinjeInline]

@admin.register(Styrekode)
class StyrekodeAdmin(admin.ModelAdmin):
    list_display = (
        "organisasjon",
        "kode",
        "fortekst",
        "sumtekst",
        "aktiv",
    )
    list_filter = (
        "organisasjon",
        "aktiv",
    )
    search_fields = (
        "kode",
        "fortekst",
        "sumtekst",
    )


@admin.register(SystemLogg)
class SystemLoggAdmin(admin.ModelAdmin):
    list_display = ("tidspunkt", "organisasjon", "bruker", "modul", "tabellnavn", "post_id", "handling", "felt_navn")
    list_filter = ("organisasjon", "modul", "tabellnavn", "handling")
    search_fields = ("tabellnavn", "post_id", "handling", "felt_navn", "gammel_verdi", "ny_verdi", "kommentar")
    readonly_fields = (
        "organisasjon",
        "tidspunkt",
        "bruker",
        "modul",
        "tabellnavn",
        "post_id",
        "handling",
        "felt_navn",
        "gammel_verdi",
        "ny_verdi",
        "kommentar",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


