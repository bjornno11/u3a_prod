# lag/admin.py
from django.contrib import admin
from .models import Organisasjon, Lokallag, Aktivitet


@admin.register(Organisasjon)
class OrganisasjonAdmin(admin.ModelAdmin):
    list_display = ("organisasjon", "fylke", "kommune", "status", "lenke_status")
    list_filter = ("fylke", "status", "lenke_status")
    search_fields = ("organisasjon", "kommune", "fylke", "nettside", "epost")


@admin.register(Lokallag)
class LokallagAdmin(admin.ModelAdmin):
    list_display = ("navn", "slug")
    prepopulated_fields = {"slug": ("navn",)}
    search_fields = ("navn",)


@admin.register(Aktivitet)
class AktivitetAdmin(admin.ModelAdmin):
    list_display = ("dato", "tittel", "lag", "publisert")
    list_filter = ("lag", "publisert", "dato")
    search_fields = ("tittel", "kortinfo", "beskrivelse")
    prepopulated_fields = {"slug": ("tittel",)}
