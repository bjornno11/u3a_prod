// Bilagsskjema-spesifikk logikk
// Bygger oppå BAS Spartacus

window.BASBilag = window.BASBilag || {};

BASBilag.oppdaterDifferanse = function () {
    let sum = 0;

    document.querySelectorAll(".belop-felt").forEach(function (felt) {
        const verdi = parseFloat(
            (felt.value || "").replace(",", ".")
        );

        if (!isNaN(verdi)) {
            sum += verdi;
        }
    });

    const diffFelt = document.getElementById("bilagDifferanse");

    if (!diffFelt) {
        return;
    }

    const restbelop = sum * -1;

    diffFelt.textContent = restbelop.toFixed(2).replace(".", ",");

    diffFelt.classList.remove("text-success", "text-danger");

    if (Math.abs(sum) < 0.005) {
        diffFelt.classList.add("text-success");
    } else {
        diffFelt.classList.add("text-danger");
    }
};

BASBilag.validerBilag = function () {
    const kontonavn = BASBilag.kontonavn || {};

    const belopFelter = document.querySelectorAll(".belop-felt");

    for (const belopFelt of belopFelter) {
        const navn = belopFelt.getAttribute("name"); // belop_2

        if (!navn) {
            continue;
        }

        const nr = navn.replace("belop_", "");
        const kontoFelt = document.querySelector('[name="konto_' + nr + '"]');

        const belop = parseFloat((belopFelt.value || "").replace(",", "."));
        const harBelop = !isNaN(belop) && Math.abs(belop) >= 0.005;

        const konto = kontoFelt ? kontoFelt.value.trim() : "";
        const harKonto = konto !== "";

        if (harBelop && !harKonto) {
            return {
                ok: false,
                felt: kontoFelt,
                melding: "Linje " + nr + " har beløp, men mangler konto."
            };
        }

        if (harKonto && !harBelop) {
            return {
                ok: false,
                felt: belopFelt,
                melding: "Linje " + nr + " har konto, men mangler beløp."
            };
        }

        if (harKonto) {
            if (!kontonavn[konto]) {
                return {
                    ok: false,
                    felt: kontoFelt,
                    melding: "Linje " + nr + " har ugyldig konto: " + konto
                };
            }

            if (kontonavn[konto].samlekonto) {
                return {
                    ok: false,
                    felt: kontoFelt,
                    melding: "Linje " + nr + " bruker samlekonto og kan ikke føres på."
                };
            }
        }
    }

    let sum = 0;

    belopFelter.forEach(function (belopFelt) {
        const belop = parseFloat((belopFelt.value || "").replace(",", "."));

        if (!isNaN(belop)) {
            sum += belop;
        }
    });

        if (Math.abs(sum) >= 0.005) {
            return {
                ok: false,
                felt: null,
                melding: "Bilaget går ikke i null. Differanse: " +
                         (sum * -1).toFixed(2).replace(".", ",")
            };
        }
    return {
        ok: true
    };
};

BASBilag.init = function (kontonavn) {
    console.log("BASBilag.init startet");

    BASBilag.kontonavn = kontonavn || {};
};
