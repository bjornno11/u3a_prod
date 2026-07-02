from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class Organisasjon(models.Model):
    STATUS_VALG = [
        ("Aktiv", "Aktiv"),
        ("Ukjent", "Ukjent"),
        ("Passiv", "Passiv"),
    ]

    fylke = models.CharField(max_length=100, verbose_name="Fylke")
    kommune = models.CharField(max_length=100, verbose_name="Kommune")
    organisasjon = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Organisasjonsnavn",
    )

    adresse = models.CharField(max_length=255, blank=True, null=True)
    nettside = models.URLField(max_length=200, blank=True, null=True)
    epost = models.EmailField(max_length=254, blank=True, null=True)
    telefon = models.CharField(max_length=20, blank=True, null=True)

    breddegrad = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lengdegrad = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    LENKE_VALG = [
        ("active", "active"),
        ("down", "down"),
        ("unknown", "unknown"),
    ]
    lenke_status = models.CharField(
        max_length=10,
        default="unknown",
        choices=LENKE_VALG,
        verbose_name="Lenkestatus",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_VALG,
        default="Ukjent",
    )
    orgnummer = models.CharField(
        "Organisasjonsnummer",
        max_length=9,
        blank=True,
        null=True,
    )

    hjemmesidetype = models.PositiveSmallIntegerField(
        choices=[
            (1, "1 - Enkel startside"),
            (2, "2 - Kalender og aktiviteter"),
            (3, "3 - Full lokallagsside"),
        ],
        default=1,
    )

    kilde = models.CharField(max_length=100, blank=True, null=True)

    subdomene = models.SlugField(
        max_length=63,
        blank=True,
        null=True,
        unique=True,
        help_text="f.eks. rakkestad (gir rakkestad.u3a.no)",
    )

    forside_tittel = models.CharField(max_length=200, blank=True, null=True)
    forside_ingress = models.CharField(max_length=300, blank=True, null=True)
    forside_tekst = models.TextField(blank=True, null=True)
    footer_tekst = models.TextField(
        blank=True,
        null=True
)

    forside_bilde = models.ImageField(
        upload_to="lokallag/forside/",
        blank=True,
        null=True,
        verbose_name="Forsidebilde",
    )

    redaktorer = models.ManyToManyField(
        User,
        blank=True,
        related_name="redaktor_for_organisasjoner",
        help_text="Brukere som kan redigere denne organisasjonen i admin.",
    )

    opprettet = models.DateTimeField(default=timezone.now, verbose_name="Registrert dato")
    sist_endret = models.DateTimeField(auto_now=True)
    opprettet_av = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name_plural = "Organisasjoner"
        ordering = ["organisasjon"]

    def __str__(self):
        return self.organisasjon


class Lokallag(models.Model):
    """
    DEPRECATED – beholdes midlertidig for bakoverkompatibilitet.
    Bruk Organisasjon i stedet.
    """
    navn = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.navn


class Aktivitet(models.Model):
    """
    Aktivitet tilknyttet Organisasjon (lokallag).

    Feltet `lag` beholdes midlertidig for eksisterende data, men er nå valgfritt
    slik at nye aktiviteter kan opprettes kun med `organisasjon`.
    """

    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="aktiviteter",
        null=True,
        blank=True,
        help_text="Organisasjonen (lokallaget) som eier aktiviteten",
    )

    # PATCH: lag er nå valgfritt (DB tillater NULL)
    lag = models.ForeignKey(
        Lokallag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aktiviteter",
        help_text="(DEPRECATED) Bruk organisasjon-feltet i stedet",
    )

    tittel = models.CharField(max_length=200)
    dato = models.DateField(help_text="Dato for aktiviteten")

    kortinfo = models.CharField(max_length=300)
    beskrivelse = models.TextField()

    sted = models.CharField(max_length=200, blank=True)
    starttid = models.TimeField(null=True, blank=True)
    sluttid = models.TimeField(null=True, blank=True)

    foredragsholder = models.CharField(max_length=200, blank=True)

    bilde = models.ImageField(
        upload_to="aktiviteter/bilder/",
        blank=True,
        null=True
    )

    vedlegg = models.FileField(
        upload_to="aktiviteter/vedlegg/",
        blank=True,
        null=True
    )

    slug = models.SlugField(max_length=220)

    publisert = models.BooleanField(default=True)

    pamelding_aktiv = models.BooleanField(
        default=False,
        verbose_name="Påmelding aktiv"
    )

    maks_antall = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Maks antall deltakere"
    )

    opprettet_av = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    opprettet = models.DateTimeField(auto_now_add=True)
    oppdatert = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dato", "-opprettet"]

    def __str__(self):
        if self.organisasjon:
            owner = self.organisasjon.organisasjon
        elif self.lag:
            owner = self.lag.navn
        else:
            owner = "Ukjent lokallag"
        return f"{self.dato} – {owner}: {self.tittel}"

class AktivitetPamelding(models.Model):
    aktivitet = models.ForeignKey(
        Aktivitet,
        on_delete=models.CASCADE,
        related_name="pameldinger"
    )

    navn = models.CharField(max_length=100)
    epost = models.EmailField()
    telefon = models.CharField(max_length=20, blank=True)

    opprettet = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["opprettet"]

    def __str__(self):
        return f"{self.navn} – {self.aktivitet.tittel}"

class SiteConfig(models.Model):
    hoved_epost = models.EmailField(
        max_length=254,
        default="u3a@u3a.no",
        verbose_name="Hoved e-post (u3a.no)",
    )

    sist_endret = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SiteConfig"
        verbose_name_plural = "SiteConfig"

    def __str__(self):
        return "SiteConfig (global)"

class Medlemsgruppe(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="medlemsgrupper"
    )
    navn = models.CharField(max_length=100)
    aktiv = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organisasjon", "navn")
        ordering = ["navn"]

    def __str__(self):
        return self.navn

class LagMedlem(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="medlemmer",
        help_text="Lokallaget som eier medlemmet",
    )

    fornavn = models.CharField(max_length=100)
    etternavn = models.CharField(max_length=100)

    epost = models.EmailField(max_length=254, blank=True, null=True)
    telefon = models.CharField(max_length=20, blank=True, null=True)

    adresse = models.CharField(max_length=255, blank=True, null=True)
    postnummer = models.CharField(max_length=10, blank=True, null=True)
    poststed = models.CharField(max_length=100, blank=True, null=True)

    fodselsdato = models.DateField(blank=True, null=True)
    gruppe = models.ForeignKey(
        Medlemsgruppe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medlemmer",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="lagmedlem",
    )

    medlemsnummer = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Medlemsnummer. Brukes også som kontonummer i regnskapet.",
    )

    familiemedlem = models.BooleanField(
        default=False,
        help_text="Markerer om medlemmet er familiemedlem.",
    )

    hovedmedlem = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="familiemedlemmer",
        help_text="Hovedmedlem dersom dette medlemmet er del av en familie.",
    )

    STATUS_REGISTRERT = 1
    STATUS_GODKJENT = 2
    STATUS_UTMELDT = 6
    STATUS_SUSPENDERT = 7
    STATUS_PERMANENT_SUSPENDERT = 8

    STATUS_CHOICES = [
        (STATUS_REGISTRERT, "Registrert - ikke godkjent"),
        (STATUS_GODKJENT, "Godkjent"),
        (STATUS_UTMELDT, "Utmeldt"),
        (STATUS_SUSPENDERT, "Suspendert"),
        (STATUS_PERMANENT_SUSPENDERT, "Permanent suspendert"),
    ]

    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        default=STATUS_REGISTRERT,
    )
    aktiv = models.BooleanField(default=True)

    opprettet = models.DateTimeField(default=timezone.now)
    sist_endret = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lagmedlem"
        verbose_name_plural = "Lagmedlemmer"
        ordering = ["etternavn", "fornavn"]

        constraints = [
            models.UniqueConstraint(
                fields=["organisasjon", "medlemsnummer"],
                name="unik_medlemsnummer_per_organisasjon",
            ),
        ]
    def __str__(self):
        return f"{self.etternavn}, {self.fornavn}"

    @property
    def navn(self):
        return f"{self.fornavn} {self.etternavn}"


class LagRolle(models.Model):
    navn = models.CharField(max_length=100, unique=True)
    beskrivelse = models.CharField(max_length=255, blank=True, null=True)
    opprettet = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Lagrolle"
        verbose_name_plural = "Lagroller"
        ordering = ["navn"]

    def __str__(self):
        return self.navn


class LagUtvalg(models.Model):
    navn = models.CharField(max_length=100, unique=True)
    beskrivelse = models.CharField(max_length=255, blank=True, null=True)
    opprettet = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Lagutvalg"
        verbose_name_plural = "Lagutvalg"
        ordering = ["navn"]

    def __str__(self):
        return self.navn


class LagMedlemVerv(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="verv",
        help_text="Lokallaget som eier vervet",
    )

    medlem = models.ForeignKey(
        LagMedlem,
        on_delete=models.CASCADE,
        related_name="verv",
    )

    rolle = models.ForeignKey(
        LagRolle,
        on_delete=models.PROTECT,
        related_name="verv",
    )

    utvalg = models.ForeignKey(
        LagUtvalg,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="verv",
    )

    fra_dato = models.DateField(blank=True, null=True)
    til_dato = models.DateField(blank=True, null=True)

    valgt_dato = models.DateField(blank=True, null=True)
    valgt_av = models.CharField(max_length=100, blank=True, null=True)

    merknad = models.CharField(max_length=255, blank=True, null=True)

    aktiv = models.BooleanField(default=True)

    opprettet = models.DateTimeField(default=timezone.now)
    sist_endret = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lagverv"
        verbose_name_plural = "Lagverv"
        ordering = ["-aktiv", "rolle__navn", "medlem__etternavn"]

    def __str__(self):
        return f"{self.medlem} - {self.rolle}"

    def clean(self):
        if self.medlem and self.organisasjon and self.medlem.organisasjon_id != self.organisasjon_id:
            raise ValidationError("Medlemmet tilhører ikke valgt organisasjon.")

class Postnummer(models.Model):
    postnummer = models.CharField(max_length=4, unique=True)
    poststed = models.CharField(max_length=100)
    kommune = models.CharField(max_length=100, blank=True, null=True)
    fylke = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Postnummer"
        verbose_name_plural = "Postnummer"
        ordering = ["postnummer"]

    def __str__(self):
        return f"{self.postnummer} {self.poststed}"

class Arrangement(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="arrangementer"
    )

    tittel = models.CharField(max_length=200)
    dato = models.DateField()
    starttid = models.TimeField()
    sluttid = models.TimeField(null=True, blank=True)

    sted = models.CharField(max_length=200)
    foredragsholder = models.CharField(max_length=200, blank=True)

    ingress = models.TextField(blank=True)
    beskrivelse = models.TextField(blank=True)

    publisert = models.BooleanField(default=True)

    opprettet = models.DateTimeField(auto_now_add=True)
    sist_endret = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["dato", "starttid"]
        verbose_name = "Arrangement"
        verbose_name_plural = "Arrangementer"

    def __str__(self):
        return f"{self.dato} - {self.tittel}"

class Nyhet(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="nyheter"
    )

    tittel = models.CharField(max_length=200)
    ingress = models.TextField(blank=True)
    tekst = models.TextField(blank=True)

    bilde = models.ImageField(
        upload_to="nyheter/",
        blank=True,
        null=True
    )

    publisert = models.BooleanField(default=True)
    publisert_dato = models.DateField(null=True, blank=True)

    opprettet = models.DateTimeField(auto_now_add=True)
    sist_endret = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publisert_dato", "-opprettet"]
        verbose_name = "Nyhet"
        verbose_name_plural = "Nyheter"

    def __str__(self):
        return self.tittel

class Dokument(models.Model):

    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE
    )

    tittel = models.CharField(
        max_length=200
    )

    KATEGORIER = [
        ("referat", "Referater"),
        ("innkalling", "Innkallinger"),
        ("arsmote", "Årsmøte"),
        ("strategi", "Strategi"),
        ("regnskap", "Regnskap"),
        ("budsjett", "Budsjett"),
        ("vedtekter", "Vedtekter"),
        ("kontrakt", "Kontrakter"),
        ("soknad", "Søknader"),
        ("program", "Program"),
        ("presentasjon", "Presentasjoner"),
        ("bilder", "Bilder"),
        ("annet", "Annet"),
    ]
    kategori = models.CharField(
        max_length=50,
        choices=KATEGORIER,
        default="annet"
    )
    er_styredokument = models.BooleanField(
        default=False
    )

    fil = models.FileField(
        upload_to="dokumenter/"
    )

    beskrivelse = models.TextField(
        blank=True
    )

    opprettet = models.DateTimeField(
        auto_now_add=True
    )
    sist_endret = models.DateTimeField(
        auto_now=True
    )

    opprettet_av = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    publisert = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.tittel

class Bilde(models.Model):

    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE
    )

    tittel = models.CharField(
        max_length=200
    )

    bilde = models.ImageField(
        upload_to="bilder/"
    )

    beskrivelse = models.TextField(
        blank=True
    )

    opprettet = models.DateTimeField(
        auto_now_add=True
    )

    publisert = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.tittel

class SmsLeverandor(models.Model):
    organisasjon = models.OneToOneField(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="sms_leverandor"
    )

    navn = models.CharField(max_length=100, blank=True)
    api_url = models.CharField(max_length=255, blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    avsender = models.CharField(max_length=50, blank=True)

    aktiv = models.BooleanField(default=False)
    testmodus = models.BooleanField(
        default=True,
        help_text="Når aktivert sendes ingen ekte SMS."
    )

    opprettet = models.DateTimeField(auto_now_add=True)
    sist_endret = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SMS – {self.organisasjon}"


class SmsUtsending(models.Model):
    STATUS_KLADD = 1
    STATUS_KLAR = 2
    STATUS_SENDT = 3
    STATUS_FEIL = 4
    STATUS_TEST = 5

    STATUS_CHOICES = [
        (STATUS_KLADD, "Kladd - ikke sendt"),
        (STATUS_KLAR, "Klar til sending"),
        (STATUS_SENDT, "Sendt"),
        (STATUS_FEIL, "Feil"),
        (STATUS_TEST, "Test - ikke sendt eksternt"),
    ]

    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="sms_utsendinger"
    )

    melding = models.TextField()
    mottakertekst = models.CharField(max_length=255, blank=True)

    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=STATUS_KLADD
    )

    antall_mottakere = models.IntegerField(default=0)

    opprettet = models.DateTimeField(auto_now_add=True)
    sist_endret = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SMS-utsending {self.organisasjon} – {self.opprettet}"

class SmsLogg(models.Model):
    STATUS_KLADD = 1
    STATUS_TEST = 2
    STATUS_SENDT = 3
    STATUS_FEIL = 4

    STATUS_CHOICES = [
        (STATUS_KLADD, "Kladd"),
        (STATUS_TEST, "Test"),
        (STATUS_SENDT, "Sendt"),
        (STATUS_FEIL, "Feil"),
    ]
    utsending = models.ForeignKey(
        SmsUtsending,
        on_delete=models.CASCADE,
        related_name="mottakere",
        null=True,
        blank=True
    )

    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="sms_logger"
    )

    medlem = models.ForeignKey(
        LagMedlem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_logger"
    )

    telefon = models.CharField(max_length=30, blank=True)
    melding = models.TextField()
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_KLADD)

    leverandor_svar = models.TextField(blank=True)

    opprettet = models.DateTimeField(auto_now_add=True)
    sendt_tid = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"SMS {self.organisasjon} – {self.opprettet}"

class Sidevisning(models.Model):
    dato = models.DateField()
    host = models.CharField(max_length=255)
    sti = models.CharField(max_length=500)
    antall = models.PositiveIntegerField(default=0)
    sist_besokt = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sidevisning"
        verbose_name_plural = "Sidevisninger"
        unique_together = ("dato", "host", "sti")
        ordering = ["-dato", "-antall"]

    def __str__(self):
        return f"{self.dato} {self.host}{self.sti} ({self.antall})"

