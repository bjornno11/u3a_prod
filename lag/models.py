# /srv/u3a/lag/models.py - STABIL UTGAVE (uten URL-sjekk)

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Organisasjon(models.Model):
    # Statusvalg
    STATUS_VALG = [
        ('Aktiv', 'Aktiv'),
        ('Ukjent', 'Ukjent'),
        ('Passiv', 'Passiv'),
    ]

    # Kolonnene dine
    fylke = models.CharField(max_length=100, verbose_name="Fylke")
    kommune = models.CharField(max_length=100, verbose_name="Kommune")
    organisasjon = models.CharField(max_length=200, unique=True, verbose_name="Organisasjonsnavn")
    adresse = models.CharField(max_length=255, blank=True, null=True, verbose_name="Adresse")
    nettside = models.URLField(max_length=200, blank=True, null=True, verbose_name="Nettside")
    epost = models.EmailField(max_length=254, blank=True, null=True, verbose_name="E-post")
    telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    breddegrad = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True, 
        verbose_name="Breddegrad (Latitude)"
        )
    lengdegrad = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True, 
        verbose_name="Lengdegrad (Longitude)"
        ) 
    LENKE_VALG = [
        ('OK', 'OK'),
        ('FEIL', 'FEIL'),
        ('UKJENT', 'UKJENT'),
    ]
    lenke_status = models.CharField(
        max_length=10, 
        default='UKJENT', 
        choices=LENKE_VALG,
        verbose_name="Lenkestatus"
    )
    
    # Statusfelt med forhåndsdefinerte valg
    status = models.CharField(
        max_length=10,
        choices=STATUS_VALG,
        default='Ukjent',
        verbose_name="Status"
    )
    
    kilde = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kilde")
    
    # Tidstempler
    opprettet = models.DateTimeField(default=timezone.now, verbose_name="Opprettet")
    sist_endret = models.DateTimeField(auto_now=True, verbose_name="Sist endret")

    # FJERNET: is_website_active-metoden

    class Meta:
        verbose_name_plural = "Organisasjoner"
        ordering = ['organisasjon'] 

    def __str__(self):
        return self.organisasjon

# lag/models.py

class Lokallag(models.Model):
    navn = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    # ... resten av feltene dine

    def __str__(self):
        return self.navn


class Aktivitet(models.Model):
    lag = models.ForeignKey(
        Lokallag,
        on_delete=models.CASCADE,
        related_name="aktiviteter",
        help_text="Lokallaget som eier denne aktiviteten",
    )

    # Det som vises som tittel både i kortinfo og på siden
    tittel = models.CharField(max_length=200)

    # Dato er påkrevd – brukes både til sortering og visning
    dato = models.DateField(help_text="Dato for aktiviteten")

    # Kortinfo til «Fra lagene» – 3–5 linjer tekst, vi begrenser i template/CSS
    kortinfo = models.CharField(
        max_length=300,
        help_text="Kort tekst (3–5 linjer) som vises under 'Fra lagene'",
    )

    # Full tekst til egen aktivitetsside
    beskrivelse = models.TextField(
        help_text="Full beskrivelse av aktiviteten som vises på aktivitetssiden",
    )

    sted = models.CharField(
        max_length=200,
        blank=True,
        help_text="Valgfritt: Sted for aktiviteten",
    )

    slug = models.SlugField(
        max_length=220,
        help_text="Brukes i URL for aktivitetssiden",
    )

    publisert = models.BooleanField(
        default=True,
        help_text="Hvis denne er av, vises ikke aktiviteten offentlig",
    )

    opprettet_av = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Bruker som opprettet aktiviteten",
    )

    opprettet = models.DateTimeField(auto_now_add=True)
    oppdatert = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dato", "-opprettet"]  # nyeste først

    def __str__(self):
        return f"{self.dato} – {self.lag.navn}: {self.tittel}"
