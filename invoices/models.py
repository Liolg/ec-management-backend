from django.db import models

class Invoice(models.Model):
    employee=models.CharField(max_length=255)
