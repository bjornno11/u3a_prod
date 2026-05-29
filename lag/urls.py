from django.urls import path
from .views import (
    registrer_medlem,
    registrer_medlem_takk,
    postnummer_lookup,
    godkjenn_medlemmer,
    godkjenn_medlem,
    nyhet_detalj,
    program,
)
urlpatterns = [
    path("registrer-medlem/", registrer_medlem, name="registrer_medlem"),
    path("registrer-medlem/takk/", registrer_medlem_takk, name="registrer_medlem_takk"),
    path("postnummer-lookup/", postnummer_lookup, name="postnummer_lookup"),
    path("godkjenn-medlemmer/", godkjenn_medlemmer, name="godkjenn_medlemmer"),
    path("godkjenn-medlemmer/<int:medlem_id>/", godkjenn_medlem, name="godkjenn_medlem"),
    path("nyheter/<int:nyhet_id>/", nyhet_detalj, name="nyhet_detalj"),
    path("program/", program, name="program"),
]
