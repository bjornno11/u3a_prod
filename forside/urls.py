from django.urls import path
from .views import forside_view
from .views_upload import tinymce_image_upload

urlpatterns = [
    path("", forside_view, name="forside"),
    path("upload-image/", tinymce_image_upload, name="tinymce_image_upload"),
]
