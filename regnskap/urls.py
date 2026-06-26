from django.urls import path
from . import views

app_name = "regnskap"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("faste-data/", views.faste_data, name="faste_data"),
    path("faste-data/kontoplan/", views.kontoplan, name="kontoplan"),
    path(
        "faste-data/kontoplan/<int:konto_id>/",
        views.konto_endre,
        name="konto_endre",
    ),

    path(
        "faste-data/kontoplan/ny/",
        views.konto_ny,
        name="konto_ny",
    ),

    path(
        "faste-data/kontoplan/<int:konto_id>/slett/",
        views.konto_slett,
        name="konto_slett",
    ),

    path("faste-data/styrekoder/", views.styrekoder, name="styrekoder"),
    path(
        "opprett-standard-startdata/",
        views.opprett_standard_startdata,
        name="opprett_standard_startdata",
    ),
    path(
        "styrekoder/ny/",
        views.styrekode_ny,
        name="styrekode_ny",
    ),
    path(
        "styrekoder/<int:styrekode_id>/",
        views.styrekode_endre,
        name="styrekode_endre",
    ),
    path(
        "styrekoder/<int:styrekode_id>/slett/",
        views.styrekode_slett,
        name="styrekode_slett",
    ),
    path(
        "faste-data/avdelinger/",
        views.avdelinger,
        name="avdelinger",
    ),

    path(
        "faste-data/avdelinger/ny/",
        views.avdeling_ny,
        name="avdeling_ny",
    ),

    path(
        "faste-data/avdelinger/<int:avdeling_id>/",
        views.avdeling_endre,
        name="avdeling_endre",
    ),

    path(
        "faste-data/avdelinger/<int:avdeling_id>/slett/",
        views.avdeling_slett,
        name="avdeling_slett",
    ),

    path("faste-data/prosjekter/", views.prosjekter, name="prosjekter"),
    path("faste-data/prosjekter/ny/", views.prosjekt_ny, name="prosjekt_ny"),
    path("faste-data/prosjekter/<int:prosjekt_id>/", views.prosjekt_endre, name="prosjekt_endre"),
    path("faste-data/prosjekter/<int:prosjekt_id>/slett/", views.prosjekt_slett, name="prosjekt_slett"),

    path(
        "faste-data/bilagsserier/",
        views.bilagsserier,
        name="bilagsserier",
    ),

    path(
        "faste-data/regnskapsaar/",
        views.regnskapsaar,
        name="regnskapsaar",
    ),

    path(
        "faste-data/regnskapsaar/ny/",
        views.regnskapsaar_ny,
        name="regnskapsaar_ny",
    ),

    path(
        "faste-data/regnskapsaar/<int:regnskapsaar_id>/",
        views.regnskapsaar_endre,
        name="regnskapsaar_endre",
    ),

    path(
        "faste-data/bilagsserier/ny/",
        views.bilagsserie_ny,
        name="bilagsserie_ny",
    ),

    path(
        "faste-data/bilagsserier/<int:bilagsserie_id>/",
        views.bilagsserie_endre,
        name="bilagsserie_endre",
    ),

    path(
        "faste-data/bilagsserier/<int:bilagsserie_id>/slett/",
        views.bilagsserie_slett,
        name="bilagsserie_slett",
    ),

    path(
        "bilag/",
        views.bilag_liste,
        name="bilag_liste",
    ),

    path(
        "bilag/ny/",
        views.bilag_ny,
        name="bilag_ny",
    ),
    path("bilag/journal/", views.bilagsjournal, name="bilagsjournal"),

    path(
        "bilag/<int:bilag_id>/",
        views.bilag_detalj,
        name="bilag_detalj",
    ),

    path(
        "bilag/<int:bilag_id>/endre/",
        views.bilag_endre,
        name="bilag_endre",
    ),

    path(
        "kontosporring/",
        views.kontosporring,
        name="kontosporring",
    ),

    path(
        "journaler/bilagsjournal/",
        views.bilagsjournal,
        name="bilagsjournal",
    ),
]

