from django.db import models
from django.core.exceptions import ValidationError

from lag.models import Organisasjon


class Regnskapsaar(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="regnskapsaar"
    )

    aar = models.PositiveIntegerField()

    navn = models.CharField(
        max_length=50,
        blank=True
    )

    fra_dato = models.DateField()
    til_dato = models.DateField()

    aktiv = models.BooleanField(default=True)
    avsluttet = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Regnskapsår"
        verbose_name_plural = "Regnskapsår"
        ordering = ["-aar"]
        unique_together = ("organisasjon", "aar")

    def __str__(self):
        return f"{self.organisasjon} - {self.aar}"


class Regnskapsperiode(models.Model):
    regnskapsaar = models.ForeignKey(
        Regnskapsaar,
        on_delete=models.CASCADE,
        related_name="perioder"
    )

    periodenummer = models.PositiveSmallIntegerField()

    fra_dato = models.DateField()
    til_dato = models.DateField()

    STATUS_VALG = [
        (1, "Åpen"),
        (0, "Avsluttet"),
    ]

    status = models.IntegerField(
        choices=STATUS_VALG,
        default=1
    )

    class Meta:
        verbose_name = "Regnskapsperiode"
        verbose_name_plural = "Regnskapsperioder"
        ordering = ["periodenummer"]
        unique_together = ("regnskapsaar", "periodenummer")

    def __str__(self):
        return (
            f"{self.regnskapsaar.aar}"
            f"-{self.periodenummer:02d}"
        )

class Regnskapsoppsett(models.Model):
    organisasjon = models.OneToOneField(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="regnskapsoppsett"
    )

    navn = models.CharField(max_length=150)
    adresse = models.CharField(max_length=150, blank=True)
    postnummer = models.CharField(max_length=10, blank=True)
    poststed = models.CharField(max_length=80, blank=True)

    bankkonto = models.CharField(max_length=30, blank=True)
    organisasjonsnummer = models.CharField(max_length=20, blank=True)

    mva_pliktig = models.BooleanField(default=False)

    hovedbok_fra = models.PositiveIntegerField(default=100)
    hovedbok_til = models.PositiveIntegerField(default=999)

    leverandor_fra = models.PositiveIntegerField(default=1000)
    leverandor_til = models.PositiveIntegerField(default=1999)

    medlem_fra = models.PositiveIntegerField(default=2000)
    medlem_til = models.PositiveIntegerField(default=2999)

    kunde_fra = models.PositiveIntegerField(default=3000)
    kunde_til = models.PositiveIntegerField(default=3999)

    regnskapsaar_fra = models.PositiveIntegerField(default=2020)
    regnskapsaar_til = models.PositiveIntegerField(default=2099)

    logo = models.ImageField(
        upload_to="regnskap/logo/",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Regnskapsoppsett"
        verbose_name_plural = "Regnskapsoppsett"

    def __str__(self):
        return self.navn


class Bilagsserie(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="bilagsserier"
    )

    regnskapsaar = models.ForeignKey(
        Regnskapsaar,
        on_delete=models.CASCADE,
        related_name="bilagsserier"
    )

    kode = models.CharField(
        max_length=5
    )

    navn = models.CharField(
        max_length=100
    )

    standard_tekst = models.CharField(
        max_length=100,
        blank=True
    )

    neste_nummer = models.PositiveIntegerField(
        default=1
    )

    standard_konto = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    STANDARD_FORTEGN = [
        ("+", "Debet"),
        ("-", "Kredit"),
    ]

    standard_fortegn = models.CharField(
        max_length=1,
        choices=STANDARD_FORTEGN,
        blank=True
    )

    aktiv = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bilagsserie"
        verbose_name_plural = "Bilagsserier"
        ordering = ["kode"]
        unique_together = (
            "organisasjon",
            "regnskapsaar",
            "kode",
        )

    def __str__(self):
        return f"{self.kode} - {self.navn}"

class Styrekode(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="regnskap_styrekoder"
    )

    kode = models.CharField(
        max_length=4
    )

    fortekst = models.CharField(
        max_length=100
    )

    sumtekst = models.CharField(
        max_length=100
    )

    aktiv = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = "Styrekode"
        verbose_name_plural = "Styrekoder"
        ordering = ["kode"]
        unique_together = (
            "organisasjon",
            "kode",
        )

    def __str__(self):
        return f"{self.kode} {self.fortekst}"


class Konto(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="kontoer"
    )

    kontonummer = models.PositiveSmallIntegerField()

    kontonavn = models.CharField(
        max_length=100
    )

    styrekode = models.CharField(
        max_length=4
    )

    samlekonto = models.BooleanField(
        default=False
    )

    krever_avdeling = models.BooleanField(
        default=False
    )

    krever_prosjekt = models.BooleanField(
        default=False
    )

    aktiv = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = "Konto"
        verbose_name_plural = "Kontoplan"
        ordering = ["kontonummer"]
        unique_together = (
            "organisasjon",
            "kontonummer",
        )

    def __str__(self):
        return (
            f"{self.kontonummer} "
            f"{self.kontonavn}"
        )

    @property
    def kontogruppe(self):
        første = str(self.kontonummer)[0]

        if første == "1":
            return "Aktiva"

        if første == "2":
            return "Passiva"

        if første == "3":
            return "Inntekter"

        return "Utgifter"

class Avdeling(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="avdelinger"
    )

    avdelingsnummer = models.PositiveIntegerField()

    navn = models.CharField(
        max_length=100
    )

    ansvarlig_medlem = models.ForeignKey(
        "lag.LagMedlem",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    fra_dato = models.DateField(
        null=True,
        blank=True
    )

    til_dato = models.DateField(
        null=True,
        blank=True
    )

    aktiv = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["avdelingsnummer"]
        unique_together = (
            "organisasjon",
            "avdelingsnummer",
        )

    def __str__(self):
        return f"{self.avdelingsnummer} {self.navn}"


class Prosjekt(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="prosjekter"
    )

    prosjektnummer = models.PositiveIntegerField()

    navn = models.CharField(
        max_length=100
    )

    beskrivelse = models.TextField(
        blank=True
    )

    ansvarlig_medlem = models.ForeignKey(
        "lag.LagMedlem",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    fra_dato = models.DateField(
        null=True,
        blank=True
    )

    til_dato = models.DateField(
        null=True,
        blank=True
    )

    aktiv = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["prosjektnummer"]
        unique_together = (
            "organisasjon",
            "prosjektnummer",
        )

    def __str__(self):
        return f"{self.prosjektnummer} {self.navn}"


class ReskontroKonto(models.Model):
    RESKONTROTYPE_VALG = [
        ("MEDLEM", "Medlem"),
        ("KUNDE", "Kunde"),
        ("LEVERANDOR", "Leverandør"),
    ]

    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="reskontro_kontoer"
    )

    samlekonto = models.ForeignKey(
        Konto,
        on_delete=models.PROTECT,
        related_name="reskontro_kontoer"
    )

    kontonummer = models.PositiveIntegerField()

    navn = models.CharField(
        max_length=100
    )

    reskontrotype = models.CharField(
        max_length=20,
        choices=RESKONTROTYPE_VALG,
        default="MEDLEM"
    )

    medlem = models.ForeignKey(
        "lag.LagMedlem",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reskontro_kontoer"
    )

    aktiv = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = "Reskontrokonto"
        verbose_name_plural = "Reskontrokontoer"
        ordering = ["kontonummer"]
        unique_together = (
            "organisasjon",
            "kontonummer",
        )

    def __str__(self):
        return f"{self.kontonummer} {self.navn}"

    def clean(self):
        if self.samlekonto and not self.samlekonto.samlekonto:
            raise ValidationError(
                "Reskontrokonto må peke til en konto som er merket som samlekonto."
            )

        if self.medlem and self.medlem.organisasjon_id != self.organisasjon_id:
            raise ValidationError(
                "Medlemmet tilhører ikke samme organisasjon som reskontrokontoen."
            )

class Momskode(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="momskoder"
    )

    kode = models.CharField(max_length=10)
    navn = models.CharField(max_length=100)
    sats = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    aktiv = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Momskode"
        verbose_name_plural = "Momskoder"
        ordering = ["kode"]
        unique_together = ("organisasjon", "kode")

    def __str__(self):
        return f"{self.kode} {self.navn}"


class Bilag(models.Model):
    STATUS_SLETTET = 0
    STATUS_REGISTRERT = 1

    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.CASCADE,
        related_name="bilag"
    )

    regnskapsaar = models.ForeignKey(
        Regnskapsaar,
        on_delete=models.PROTECT,
        related_name="bilag"
    )

    bilagsserie = models.ForeignKey(
        Bilagsserie,
        on_delete=models.PROTECT,
        related_name="bilag"
    )

    bilagsnummer = models.PositiveIntegerField()

    bilagsdato = models.DateField()
    foringsdato = models.DateField()

    h_status = models.IntegerField(default=STATUS_REGISTRERT)
    a_status = models.IntegerField(default=STATUS_REGISTRERT)
    p_status = models.IntegerField(default=STATUS_REGISTRERT)

    bilagstekst = models.CharField(max_length=200)

    # Dersom dette bilaget er en tilbakeføring,
    # peker feltet på bilaget som tilbakeføres.
    tilbakeforing_av = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tilbakeforinger",
    )

    registrert_av = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registrerte_bilag"
    )

    opprettet = models.DateTimeField(auto_now_add=True)
    sist_endret = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bilag"
        verbose_name_plural = "Bilag"
        ordering = ["regnskapsaar", "bilagsserie", "bilagsnummer"]
        unique_together = (
            "regnskapsaar",
            "bilagsserie",
            "bilagsnummer",
        )

    def __str__(self):
        return f"{self.bilagsserie.kode}-{self.bilagsnummer}"

    @property
    def sum_belop(self):
        return sum(linje.belop for linje in self.linjer.all())

    @property
    def har_differanse(self):
        return self.sum_belop != 0


class Bilagslinje(models.Model):
    bilag = models.ForeignKey(
        Bilag,
        on_delete=models.CASCADE,
        related_name="linjer"
    )

    linjenummer = models.PositiveIntegerField()

    kontonummer = models.PositiveIntegerField()

    avdeling = models.ForeignKey(
        Avdeling,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="bilagslinjer"
    )

    prosjekt = models.ForeignKey(
        Prosjekt,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="bilagslinjer"
    )

    momskode = models.ForeignKey(
        Momskode,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="bilagslinjer"
    )

    linjetekst = models.CharField(max_length=200, blank=True)

    belop = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Bilagslinje"
        verbose_name_plural = "Bilagslinjer"
        ordering = ["bilag", "linjenummer"]
        unique_together = ("bilag", "linjenummer")

    def __str__(self):
        return f"{self.bilag} linje {self.linjenummer}"

    def clean(self):
        if self.avdeling and self.avdeling.organisasjon_id != self.bilag.organisasjon_id:
            raise ValidationError(
                "Avdelingen tilhører ikke samme organisasjon som bilaget."
            )

        if self.prosjekt and self.prosjekt.organisasjon_id != self.bilag.organisasjon_id:
            raise ValidationError(
                "Prosjektet tilhører ikke samme organisasjon som bilaget."
            )

        if self.momskode and self.momskode.organisasjon_id != self.bilag.organisasjon_id:
            raise ValidationError(
                "Momskoden tilhører ikke samme organisasjon som bilaget."
            )

class SystemLogg(models.Model):
    organisasjon = models.ForeignKey(
        Organisasjon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="systemlogger"
    )

    tidspunkt = models.DateTimeField(auto_now_add=True)

    bruker = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="systemlogger"
    )

    modul = models.CharField(max_length=50, blank=True)

    tabellnavn = models.CharField(max_length=100)
    post_id = models.CharField(max_length=50, blank=True)

    handling = models.CharField(max_length=50)

    felt_navn = models.CharField(max_length=100, blank=True)
    gammel_verdi = models.TextField(blank=True)
    ny_verdi = models.TextField(blank=True)

    kommentar = models.TextField(blank=True)

    class Meta:
        verbose_name = "Systemlogg"
        verbose_name_plural = "Systemlogger"
        ordering = ["-tidspunkt"]

    def __str__(self):
        return f"{self.tidspunkt} {self.handling} {self.tabellnavn}"


