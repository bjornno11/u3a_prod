// Bilagsskjema-spesifikk logikk
// Bygger oppå BAS Spartacus

window.BASBilag = window.BASBilag || {};
BASBilag.dom = BASBilag.dom || {};
BASBilag.state = BASBilag.state || {};

BASBilag.hentLinjer = function () {
    return document.querySelectorAll("#bilagslinjer-body tr.bilagslinje");
};

BASBilag.hentFelt = function (index, navn) {
    return document.querySelectorAll('[name="' + navn + '[]"]')[index];
};

BASBilag.fokus = function (felt) {
    if (felt) {
        felt.focus();
        if (felt.select) {
            felt.select();
        }
    }
};

BASBilag.leggTilLinje = function () {
    return BAS.leggTilTabellLinje("#bilagslinjer-body");
};

BASBilag.oppdaterDifferanse = function () {
    let sum = 0;

    document.querySelectorAll('[name="belop[]"]').forEach(function (felt) {
        const verdi = parseFloat((felt.value || "").replace(",", "."));

        if (!isNaN(verdi)) {
            sum += verdi;
        }
    });

    const diffFelt = document.getElementById("bilagDifferanse");
    if (!diffFelt) return;

    const restbelop = sum * -1;

    diffFelt.textContent = restbelop.toFixed(2).replace(".", ",");
    diffFelt.classList.remove("text-success", "text-danger");

    if (Math.abs(sum) < 0.005) {
        diffFelt.classList.add("text-success");
    } else {
        diffFelt.classList.add("text-danger");
    }
};

BASBilag.oppdaterKontonavn = function () {
    const kontonavn = BASBilag.kontonavn || {};

    document.querySelectorAll('[name="konto[]"]').forEach(function (felt) {
        const navnFelt = felt.parentElement.querySelector(".kontonavn");
        const konto = felt.value.trim();

        felt.classList.remove("is-invalid");

        if (!navnFelt) return;

        if (!konto) {
            navnFelt.textContent = "";
            navnFelt.classList.remove("text-danger");
            navnFelt.classList.add("text-muted");
            return;
        }

        if (kontonavn[konto]) {
            if (kontonavn[konto].samlekonto) {
                navnFelt.textContent = kontonavn[konto].navn + " er samlekonto og kan ikke føres på";
                navnFelt.classList.remove("text-muted");
                navnFelt.classList.add("text-danger");
                felt.classList.add("is-invalid");
            } else {
                navnFelt.textContent = kontonavn[konto].navn;
                navnFelt.classList.remove("text-danger");
                navnFelt.classList.add("text-muted");
            }
        } else {
            navnFelt.textContent = "Konto finnes ikke";
            navnFelt.classList.remove("text-muted");
            navnFelt.classList.add("text-danger");
            felt.classList.add("is-invalid");
        }
    });
};

BASBilag.hentValgtBilagsserie = function () {
    const bilagsserie = BASBilag.dom.bilagsserie;
    if (!bilagsserie) return null;

    return bilagsserie.options[bilagsserie.selectedIndex];
};

BASBilag.fyllBelop = function () {
    const bilagsbelop = BASBilag.dom.bilagsbelop;
    if (!bilagsbelop) return;

    let linjer = BASBilag.hentLinjer();

    while (linjer.length < 2) {
        BASBilag.leggTilLinje();
        linjer = BASBilag.hentLinjer();
    }

    const konto1 = BASBilag.hentFelt(0, "konto");
    const belop1 = BASBilag.hentFelt(0, "belop");
    const belop2 = BASBilag.hentFelt(1, "belop");

    if (!konto1 || !belop1 || !belop2) return;

    const valgt = BASBilag.hentValgtBilagsserie();
    if (!valgt) return;

    const standardFortegn = valgt.dataset.standardFortegn || "";
    const standardKonto = valgt.dataset.standardKonto || "";
    const verdi = parseFloat((bilagsbelop.value || "").replace(",", "."));

    if (isNaN(verdi)) return;

    konto1.value = standardKonto;

    if (standardFortegn === "-") {
        belop1.value = (-verdi).toFixed(2);
        belop2.value = verdi.toFixed(2);
    } else {
        belop1.value = verdi.toFixed(2);
        belop2.value = (-verdi).toFixed(2);
    }

    BASBilag.oppdaterKontonavn();
    BASBilag.oppdaterDifferanse();
};

BASBilag.fyllFraBilagsserie = function () {
    const valgt = BASBilag.hentValgtBilagsserie();
    if (!valgt) return;

    const standardTekst = valgt.dataset.standardTekst || "";

    if (BASBilag.dom.bilagstekst) {
        BASBilag.dom.bilagstekst.value = standardTekst;
    }

    BASBilag.fyllBelop();
};

BASBilag.validerBilag = function () {
    const kontonavn = BASBilag.kontonavn || {};

    const kontoFelter = document.querySelectorAll('[name="konto[]"]');
    const belopFelter = document.querySelectorAll('[name="belop[]"]');

    for (let i = 0; i < belopFelter.length; i++) {
        const linjeNr = i + 1;
        const kontoFelt = kontoFelter[i];
        const belopFelt = belopFelter[i];

        const konto = kontoFelt ? kontoFelt.value.trim() : "";
        const belop = parseFloat((belopFelt.value || "").replace(",", "."));

        const harKonto = konto !== "";
        const harBelop = !isNaN(belop) && Math.abs(belop) >= 0.005;

        if (harBelop && !harKonto) {
            return { ok: false, felt: kontoFelt, melding: "Linje " + linjeNr + " har beløp, men mangler konto." };
        }

        if (harKonto && !harBelop) {
            return { ok: false, felt: belopFelt, melding: "Linje " + linjeNr + " har konto, men mangler beløp." };
        }

        if (harKonto && !kontonavn[konto]) {
            return { ok: false, felt: kontoFelt, melding: "Linje " + linjeNr + " har ugyldig konto: " + konto };
        }

        if (harKonto && kontonavn[konto].samlekonto) {
            return {
                ok: false,
                felt: kontoFelt,
                melding: "Linje " + linjeNr + " bruker samlekonto og kan ikke føres på."
            };
        }
    }

    let sum = 0;

    belopFelter.forEach(function (felt) {
        const verdi = parseFloat((felt.value || "").replace(",", "."));

        if (!isNaN(verdi)) {
            sum += verdi;
        }
    });

    const modusFelt = document.querySelector('[name="modus"]');
    const modus = modusFelt ? modusFelt.value : "";

    if (modus !== "tilbakeforing" && Math.abs(sum) >= 0.005) {
        return {
            ok: false,
            melding: "Bilaget går ikke i null. Differanse: " +
                     (-sum).toFixed(2).replace(".", ",")
        };
    }

    return { ok: true };
};

BASBilag.initEnterMotor = function () {
    const bilagsbelop = BASBilag.dom.bilagsbelop;
    const body = document.querySelector("#bilagslinjer-body");

    if (bilagsbelop) {
        bilagsbelop.addEventListener("keydown", function (event) {
            if (event.key !== "Enter") return;

            event.preventDefault();
            event.stopPropagation();

            BASBilag.fyllBelop();
            BASBilag.fokus(BASBilag.hentFelt(0, "konto"));
        });
    }

    if (!body) return;

    body.addEventListener("keydown", function (event) {
        if (event.key !== "Enter") return;

        const felt = event.target;
        const linje = felt.closest("tr.bilagslinje");
        if (!linje) return;

        event.preventDefault();
        event.stopPropagation();

        const linjer = Array.from(BASBilag.hentLinjer());
        const index = linjer.indexOf(linje);

        if (felt.name === "konto[]") {
            BASBilag.oppdaterKontonavn();
            BASBilag.fokus(BASBilag.hentFelt(index, "belop"));
            return;
        }

        if (felt.name === "belop[]") {
            BASBilag.oppdaterDifferanse();

            let nesteRad = linjer[index + 1];

            if (!nesteRad) {
                nesteRad = BASBilag.leggTilLinje();
            }

            if (nesteRad) {
                BASBilag.fokus(nesteRad.querySelector('[name="konto[]"]'));
            }

            return;
        }

        if (felt.name === "avdeling[]") {
            BASBilag.fokus(BASBilag.hentFelt(index, "prosjekt"));
            return;
        }

        if (felt.name === "prosjekt[]") {
            const nyRad = BASBilag.leggTilLinje();
            if (nyRad) {
                BASBilag.fokus(nyRad.querySelector('[name="konto[]"]'));
            }
        }
    });
};

BASBilag.init = function (kontonavn) {
    console.log("BASBilag.init startet");

    BASBilag.kontonavn = kontonavn || {};

    BASBilag.dom.bilagsserie = document.querySelector('[name="bilagsserie"]');
    BASBilag.dom.bilagsbelop = document.querySelector("#bilagsbelop");
    BASBilag.dom.bilagstekst = document.querySelector('[name="bilagstekst"]');
    BASBilag.dom.form = document.querySelector("#bilag-form");

    if (BASBilag.dom.form) {
        BASBilag.dom.form.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
            }
        });

        BASBilag.dom.form.addEventListener("submit", function (event) {
            const resultat = BASBilag.validerBilag();

            if (!resultat.ok) {
                event.preventDefault();
                alert(resultat.melding);

                if (resultat.felt) {
                    BASBilag.fokus(resultat.felt);
                }
            }
        });
    }

    if (BASBilag.dom.bilagsserie) {
        BASBilag.dom.bilagsserie.addEventListener("change", function () {
            BASBilag.fyllFraBilagsserie();
        });
    }

    if (BASBilag.dom.bilagsbelop) {
        BASBilag.dom.bilagsbelop.addEventListener("change", function () {
            BASBilag.fyllBelop();
        });
    }

    document.addEventListener("input", function (event) {
        if (event.target.name === "konto[]") {
            BASBilag.oppdaterKontonavn();
        }

        if (event.target.name === "belop[]") {
            BASBilag.oppdaterDifferanse();
        }
    });

    BASBilag.initEnterMotor();

    BASBilag.fyllFraBilagsserie();
    BASBilag.oppdaterKontonavn();
    BASBilag.oppdaterDifferanse();

    BASBilag.fokus(BASBilag.dom.bilagsbelop);

    BASBilag.state.endret = false;
};
