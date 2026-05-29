from django.urls import path
from . import views

app_name = "school"

urlpatterns = [
    path("", views.course_catalog, name="course_catalog"),
    path("kurs/<slug:slug>/", views.course_detail, name="course_detail"),
    path("kurs/<slug:course_slug>/fullfort/", views.completion_page, name="completion_page"),
    path("kurs/<slug:course_slug>/<slug:module_slug>/", views.module_detail, name="module_detail"),
]

