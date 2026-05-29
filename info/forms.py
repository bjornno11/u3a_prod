from django import forms


class U3AKontaktForm(forms.Form):
    navn = forms.CharField(label="Navn", max_length=100)
    epost = forms.EmailField(label="E-post")
    lokallag = forms.CharField(label="Lokallag / organisasjon", max_length=150, required=False)
    kommune = forms.CharField(label="Kommune", max_length=100, required=False)
    melding = forms.CharField(label="Melding", widget=forms.Textarea)

