"""
URL configuration for u3a project.
"""
from django.contrib import admin
from django.urls import path
from lag.views import lokallag_liste, lokallag_kart, regnskap_side, aktivitet_detalj
from forside.views import forside_view
from info.views import om_u3a_norge, for_pressen, bli_med, starte_u3a

urlpatterns = [
    # Forside
    path("", forside_view, name="home"),
    path("lag/", lokallag_liste, name="lag_liste"),
    path("bli-med/", bli_med, name="bli_med"),
    path("starte-u3a/", starte_u3a, name="starte_u3a"),
    # Lokallag
    path("lokallag/liste/", lokallag_liste, name="lokallag_liste"),
    path("lokallag/kart/", lokallag_kart, name="lokallag_kart"),
    path("aktivitet/<slug:slug>/", aktivitet_detalj, name="aktivitet_detalj"),
    path("om-u3a-norge/", om_u3a_norge, name="om_u3a_norge"),
    path("for-pressen/", for_pressen, name="for_pressen"),
    # Regnskap
    path("regnskap/", regnskap_side, name="regnskap"),

    # Admin
    path("admin/", admin.site.urls),
]
