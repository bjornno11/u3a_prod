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
