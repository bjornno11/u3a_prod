# Prosjekt: U3A regnskapsmodul v1

Dette er en Django-basert regnskapsmodul for U3A/lag og organisasjoner.
# U3A Norge

Eksisterende system:
- Django
- MariaDB
- Gunicorn
- Nginx

Viktig:
- Gjør aldri endringer direkte i produksjonsdata.
- Foreslå migrasjoner før de kjøres.
- Behold eksisterende navngivning på norsk.
- Gi komplette kodeblokker ved endringer.

Arbeidsform:
- Gjør små endringer om gangen.
- Ikke bygg avanserte funksjoner før v1 virker.
- Spør før store strukturelle endringer.
- Behold norsk navngivning i modeller, views og templates.

Regnskap v1 skal være enkelt:
- Ingen MVA
- Ingen skatt
- Ingen offentlig innrapportering
- Ingen bankintegrasjon i v1
- Ingen fakturering i v1

Kontoplan:
- 3-sifret hovedbokskonto
- Første siffer bestemmer gruppe:
  - 1 = aktiva/eiendeler
  - 2 = passiva/gjeld
  - 3 = inntekter
  - 4–9 = utgifter
- Ikke bruk eget kontotypefelt.
- Hver konto skal ha styrekode på 4 siffer for rapportstyring.
- Konto kan være samlekonto.
- Konto kan kreve avdeling.
- Konto kan kreve prosjekt.

Reskontro:
- Medlemmer skal kunne brukes som konto ved bilagsføring.
- Eksempel:
  - Debet 190 Bank
  - Kredit 1234 Ole Olsen
- Medlemskonto summeres til samlekonto, f.eks. 120 Medlemsfordringer.
- Medlemsnummer lagres numerisk, men kan vises med 4 eller 6 siffer.
- 01234 og 1234 skal forstås som samme medlemsnummer ved føring.

Start med:
1. Modell for Konto
2. Modell for reskontro/medlemskonto
3. Enkel adminside
4. Deretter bilagsføring
