from django.urls import path
from . import views

app_name = "lokaladmin"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("forside/", views.forside, name="forside"),
    path("aktiviteter/", views.aktiviteter, name="aktiviteter"),
    path("aktiviteter/ny/", views.aktivitet_ny, name="aktivitet_ny"),
    path("aktiviteter/<int:aktivitet_id>/rediger/", views.aktivitet_rediger, name="aktivitet_rediger"),
    path(
    "aktiviteter/<int:aktivitet_id>/pameldinger/",
    views.aktivitet_pameldinger,
    name="aktivitet_pameldinger",
    ),
    path(
    "aktiviteter/<int:aktivitet_id>/pameldinger/csv/",
    views.aktivitet_pameldinger_csv,
    name="aktivitet_pameldinger_csv",
    ),
    path("logg-ut/", views.logg_ut, name="logg_ut"),
    path("medlemmer/", views.medlemmer, name="medlemmer"),
    path("dokumenter/", views.dokumenter, name="dokumenter"),
    path("dokumenter/arkiv/", views.dokumentarkiv, name="dokumentarkiv"),
    path("dokumenter/arkiv/ny/", views.dokument_nytt, name="dokument_nytt"),
    path("dokumenter/bilder/", views.bilder, name="bilder"),
    path("dokumenter/bilder/ny/", views.bilde_nytt, name="bilde_nytt"),
    path("dokumenter/styre/", views.styre, name="styre"),
    path("dokumenter/styre/ny/", views.verv_nytt, name="verv_nytt"),
    path("dokumenter/styre/<int:verv_id>/rediger/", views.verv_rediger, name="verv_rediger"),
    path("dokumenter/styredokumenter/", views.styredokumenter, name="styredokumenter"),
    path("styre-organisasjon/", views.styre_organisasjon, name="styre_organisasjon"),
    path("styre-organisasjon/roller/", views.roller, name="roller"),
    path("styre-organisasjon/roller/ny/", views.rolle_ny, name="rolle_ny"),
    path("styre-organisasjon/roller/<int:rolle_id>/rediger/", views.rolle_rediger, name="rolle_rediger"),
    path("styre-organisasjon/roller/<int:rolle_id>/slett/", views.rolle_slett, name="rolle_slett"),
    path("styre-organisasjon/utvalg/", views.utvalg, name="utvalg"),
    path("styre-organisasjon/utvalg/ny/", views.utvalg_ny, name="utvalg_ny"),
    path("styre-organisasjon/utvalg/<int:utvalg_id>/rediger/", views.utvalg_rediger, name="utvalg_rediger"),
    path("styre-organisasjon/utvalg/<int:utvalg_id>/slett/", views.utvalg_slett, name="utvalg_slett"),
    path("styre-organisasjon/styremedlemmer/", views.styremedlemmer, name="styremedlemmer"),
    path("styre-organisasjon/styremedlemmer/ny/", views.styremedlem_ny, name="styremedlem_ny"),
    path("styre-organisasjon/styremedlemmer/<int:verv_id>/rediger/", views.styremedlem_rediger, name="styremedlem_rediger"),
    path("styre-organisasjon/styremedlemmer/<int:verv_id>/slett/", views.styremedlem_slett, name="styremedlem_slett"),

    path("dokumenter/<int:dokument_id>/", views.dokument_detalj, name="dokument_detalj"),
    path("styre-organisasjon/redaktorer/", views.redaktorer, name="redaktorer"),
    path("styre-organisasjon/redaktorer/legg-til/", views.redaktor_legg_til, name="redaktor_legg_til"),
    path("styre-organisasjon/redaktorer/<int:user_id>/fjern/", views.redaktor_fjern, name="redaktor_fjern"),
    path(
        "dokumenter/<int:dokument_id>/rediger/",
        views.dokument_rediger,
        name="dokument_rediger",
    ),

    path(
        "styredokumenter/<int:dokument_id>/last-ned/",
        views.styredokument_last_ned,
        name="styredokument_last_ned",
    ),
    path(
        "dokument/<int:dokument_id>/slett/",
        views.dokument_slett,
        name="dokument_slett",
    ),
    path(
        "medlemmer/liste/",
        views.medlemsliste,
        name="medlemsliste",
    ),
    path("medlemsgrupper/", views.medlemsgrupper, name="medlemsgrupper"),
    path("medlemsgrupper/ny/", views.medlemsgruppe_ny, name="medlemsgruppe_ny"),
    path("medlemsgrupper/<int:gruppe_id>/rediger/", views.medlemsgruppe_rediger, name="medlemsgruppe_rediger"),
    path("medlemmer/<int:medlem_id>/rediger/", views.medlem_rediger, name="medlem_rediger"),
    path("medlemmer/liste/csv/", views.medlemsliste_csv, name="medlemsliste_csv"),
    path("tekstmeldinger/", views.tekstmeldinger, name="tekstmeldinger"),
    path("tekstmeldinger/innstillinger/", views.sms_innstillinger, name="sms_innstillinger"),
    path("tekstmeldinger/ny/", views.sms_ny, name="sms_ny"),
    path("tekstmeldinger/<int:utsending_id>/", views.sms_utsending_detalj, name="sms_utsending_detalj"),
    path(
    "tekstmeldinger/<int:utsending_id>/send/",
    views.sms_utsending_send,
    name="sms_utsending_send"
    ),
    path(
    "tekstmeldinger/<int:utsending_id>/mottaker/<int:logg_id>/slett/",
    views.sms_mottaker_slett,
    name="sms_mottaker_slett"
    ),
    path(
    "tekstmeldinger/<int:utsending_id>/tilbakestill/",
    views.sms_utsending_tilbakestill,
    name="sms_utsending_tilbakestill"
    ),
    path("nyheter/", views.nyheter, name="nyheter"),
    path("nyheter/ny/", views.nyhet_ny, name="nyhet_ny"),
    path(
    "nyheter/<int:nyhet_id>/rediger/",
    views.nyhet_rediger,
    name="nyhet_rediger"
    ),
]
