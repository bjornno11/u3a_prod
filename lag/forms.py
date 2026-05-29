from django import forms
from .models import LagMedlem


class LagMedlemRegistreringForm(forms.ModelForm):
    class Meta:
        model = LagMedlem
        fields = [
            "fornavn",
            "etternavn",
            "epost",
            "telefon",
            "adresse",
            "postnummer",
            "poststed",
            "fodselsdato",
        ]

        widgets = {
            "fodselsdato": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["fornavn"].required = True
        self.fields["etternavn"].required = True
        self.fields["adresse"].required = True
        self.fields["postnummer"].required = True
        self.fields["epost"].required = True
        self.fields["telefon"].required = True
