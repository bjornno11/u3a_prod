# BAS Spartacus

**BAS Spartacus er operativsystemet for forretningsapplikasjoner i Maximus.**

Formålet er å gi alle skjermbilder samme brukeropplevelse, samme hurtigtaster, samme oppslagsmotor og samme struktur.

## Prinsipper

### 1. BAS Spartacus eier brukergrensesnittet

`bas_spartacus.js` skal inneholde generell funksjonalitet:

* hurtigtaster
* Esc
* F2 lagre
* F4 oppslag
* footer/statuslinje
* dialoger
* grids
* fokuslogikk
* generelle skjermfunksjoner

BAS Spartacus skal ikke kjenne forretningsreglene.

---

### 2. Modulene eier forretningslogikken

Hver skjermtype får sin egen JavaScript-modul.

Eksempler:

```text
bilag_skjema.js
ordre_skjema.js
kunde_skjema.js
leverandor_skjema.js
medlem_skjema.js
```

Eksempelstruktur:

```javascript
window.BASBilag = window.BASBilag || {};

BASBilag.dom = {};
BASBilag.state = {};

BASBilag.init = function () {
};

BASBilag.validerBilag = function () {
};
```

---

### 3. HTML beskriver skjermbildet

HTML skal primært inneholde:

* felter
* knapper
* tabeller
* layout
* enkle initialiseringer

HTML skal ikke inneholde omfattende forretningslogikk.

---

### 4. `init()` eier oppstarten

Alle moduler skal ha en `init()`-funksjon.

Eksempel:

```javascript
BASBilag.init(kontonavn);
```

`init()` skal hente DOM-elementer og lagre dem i:

```javascript
BASBilag.dom
```

Eksempel:

```javascript
BASBilag.dom.form = document.querySelector("#bilag-form");
```

---

### 5. DOM-oppslag samles i `init()`

Som hovedregel skal `document.querySelector()` bare brukes i `init()`.

Resten av modulen skal bruke:

```javascript
BASBilag.dom
```

Dette gir ryddigere kode og færre feil.

---

### 6. `state` brukes til skjermbildets tilstand

Eksempel:

```javascript
BASBilag.state.endret = false;
BASBilag.state.differanse = 0;
```

DOM er skjermen.
State er tilstanden.
Data fra serveren lagres separat.

---

### 7. Wrappere er midlertidige

Under refaktorering kan HTML inneholde wrapper-funksjoner:

```javascript
function oppdaterKontonavn() {
    BASBilag.oppdaterKontonavn();
}
```

Disse skal fjernes etter hvert som funksjonene flyttes helt inn i modulen.

---

## Filstruktur

Foreløpig struktur:

```text
regnskap/static/regnskap/js/
│
├── bas_spartacus.js
└── bilag_skjema.js
```

Mulig fremtidig struktur:

```text
regnskap/static/regnskap/js/
│
├── bas_spartacus.js
├── bilag_skjema.js
├── ordre_skjema.js
├── faktura_skjema.js
├── kunde_skjema.js
├── leverandor_skjema.js
├── medlem_skjema.js
├── kontoplan.js
├── hovedbok.js
└── rapporter.js
```

---

## Nåværende BASBilag-modul

`bilag_skjema.js` inneholder foreløpig:

```text
BASBilag.init()
BASBilag.oppdaterDifferanse()
BASBilag.oppdaterKontonavn()
BASBilag.hentValgtBilagsserie()
BASBilag.fyllFraBilagsserie()
BASBilag.validerBilag()
```

Dette er første modul bygget på BAS Spartacus.

---

## Motto

**BAS Spartacus – operativsystemet for forretningsapplikasjoner.**
