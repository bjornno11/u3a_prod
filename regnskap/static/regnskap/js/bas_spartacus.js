// BAS Spartacus Framework

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
            e.preventDefault();

            const form = document.getElementById(formId);
            if (form) {
                form.submit();
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

