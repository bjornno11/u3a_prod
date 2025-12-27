from django.contrib import admin
from django import forms
from .models import Forside


class ForsideAdminForm(forms.ModelForm):
    class Meta:
        model = Forside
        fields = "__all__"

    class Media:
        js = (
            # TinyMCE fra CDN
            "https://cdn.tiny.cloud/1/izlyw1gaawi5af1oehi5yi0fw9f6h2ws9pho38nvyfej4t9d/tinymce/7/tinymce.min.js",
            # Din egen init-fil
            "forside/js/forside_tinymce_init.js",
        )


@admin.register(Forside)
class ForsideAdmin(admin.ModelAdmin):
    form = ForsideAdminForm
    list_display = ("id",)
