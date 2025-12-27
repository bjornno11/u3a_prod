from django.db import models

# Create your models here.
from django.db import models

class Forside(models.Model):
    left_column = models.TextField(blank=True)
    center_column = models.TextField(blank=True)
    right_column = models.TextField(blank=True)

    class Meta:
        verbose_name = "Forsideinnhold"
        verbose_name_plural = "Forsideinnhold"

    def __str__(self):
        return "Forsideinnhold"
