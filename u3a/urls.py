"""
URL configuration for u3a project.
"""
from lag.admin import subadmin_start, u3a_logout
from django.contrib import admin
from django.urls import path, include
from lag.subdomene_views import subdomene_start, subdomene_detalj
# Admin-tekster
admin.site.site_header = "U3A Administrasjon"
admin.site.site_title = "U3A Administrasjon"
admin.site.index_title = "Administrasjon"

# Views
from forside.views import forside_view
from info.views import om_u3a_norge, for_pressen, bli_med, starte_u3a
from lag.views import (
    lokallag_liste,
    lokallag_kart,
    regnskap_side,
    aktivitet_detalj,
    styre_side,
)
from lag.views_aktivitet import aktivitet_liste
from lag.admin import subadmin_start
from django.urls import include, path
from school.views import course_catalog

def root_view(request):
    host = request.get_host().split(":")[0]
    if host == "skole.u3a.no":
        return course_catalog(request)
    return forside_view(request)


urlpatterns = [
    # Forside
    path("", root_view, name="home"),
    path("", forside_view, name="home"),
    path("", include("forside.urls")),
    path("", include("info.urls")),   # ← denne linjen

    # Lokallag
    path("lag/", lokallag_liste, name="lag_liste"),
    path("lokallag/liste/", lokallag_liste, name="lokallag_liste"),
    path("lokallag/kart/", lokallag_kart, name="lokallag_kart"),
    path("", include("lag.urls")),

    # Aktiviteter  ✅ (rekkefølge er viktig)
    path("aktivitet/", aktivitet_liste, name="aktivitet_liste"),
    path("aktivitet/<slug:slug>/", aktivitet_detalj, name="aktivitet_detalj"),
    path("styre/", styre_side, name="styre_side"),
    # Regnskap
    path("regnskap/", regnskap_side, name="regnskap"),

    # Lag
    path(
        "admin/subdomene/",
        subdomene_start,
        name="subdomene_start"
    ),

    path(
        "admin/subdomene/<str:subdomene>/",
        subdomene_detalj,
        name="subdomene_detalj"
    ),
    path("u3a-logout/", u3a_logout, name="u3a_logout"),
    # Admin
    path("admin/lag/subadmin/", subadmin_start, name="subadmin_start"),
    path(
        "admin/lag/subadmin/<int:org_id>/",
        subadmin_start,
        name="subadmin_detalj"
    ),
    path("admin/", admin.site.urls),
    path("lokaladmin/", include("lokaladmin.urls")),
    path("", include("school.urls")),
#    path("skole/", include("school.urls")),
]
