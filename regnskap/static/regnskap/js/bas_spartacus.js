// BAS Spartacus Framework
console.log("BAS Spartacus lastet");
window.BAS = window.BAS || {};

// Enter = neste felt
BAS.initEnterSomTab = function () {
    document.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            const el = document.activeElement;

            if (!el || el.tagName === "TEXTAREA" || el.type === "submit") {
                return;
            }

            e.preventDefault();

            const felt = Array.from(
                document.querySelectorAll("input, select, textarea, button")
            ).filter(x => !x.disabled && x.offsetParent !== null);

            const index = felt.indexOf(el);

            if (index >= 0 && index < felt.length - 1) {
                felt[index + 1].focus();
            }
        }
    });
};

// F2 = lagre skjema

BAS.initF2Lagre = function (formId) {
    document.addEventListener("keydown", function (e) {
        if (e.key === "F2") {
            console.log("F2 trykket");
            e.preventDefault();

            const form = document.getElementById(formId);
            console.log("Form:", form);

            if (form) {
                const submitEvent = new Event("submit", {
                    cancelable: true,
                    bubbles: true
                });

                const ok = form.dispatchEvent(submitEvent);
                console.log("Submit ok:", ok);

                if (ok) {
                    form.submit();
                }
            }
        }
    });
};

// F5 = ny
BAS.initF5Ny = function (url) {
    document.addEventListener("keydown", function (e) {
        if (e.key === "F5") {
            e.preventDefault();
            window.location.href = url;
        }
    });
};

// F6 = journal
BAS.initF6Journal = function (url) {
    document.addEventListener("keydown", function (e) {
        if (e.key === "F6") {
            e.preventDefault();
            window.location.href = url;
        }
    });
};

// Esc = tilbake
BAS.initEsc = function (url) {
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            e.preventDefault();
            window.location.href = url;
        }
    });
};

// Statuslinje / funksjonstaster

// BAS Footer / funksjonstaster
BAS.initFooter = function (valg) {
    const container = document.getElementById("bas-footer");

    if (!container) {
        return;
    }

    const standard = {
        F1: "Hjelp",
        F2: "Lagre",
        F4: "Oppslag",
        F5: "Ny",
        F6: "Journal",
        Esc: "Tilbake"
    };

    const taster = Object.assign({}, standard, valg || {});

    container.innerHTML =
        "<strong>BAS Spartacus:</strong> " +
        Object.entries(taster)
            .filter(function ([tast, tekst]) {
                return tekst;
            })
            .map(function ([tast, tekst]) {
                return tast + "=" + tekst;
            })
            .join(" &nbsp; ");
};

