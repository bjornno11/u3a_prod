from django.urls import path
from . import views

urlpatterns = [
    path("u3a-norge/", views.u3a_norge, name="u3a_norge"),
    path("om-u3a-no/", views.om_u3a_no, name="om_u3a_no"),

    path("for-pressen/", views.for_pressen, name="for_pressen"),
    path("starte-u3a/", views.starte_u3a, name="starte_u3a"),
    path("bli-med/", views.bli_med, name="bli_med"),
]
