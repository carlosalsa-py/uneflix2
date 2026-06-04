from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    pass

class Membership(models.Model):
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('medium', 'Cinephile'),
        ('premium', 'Ultra'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('active', 'Activa'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan} ({self.status})"