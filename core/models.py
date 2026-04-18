from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


class Organization(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


def __str__(self):
    return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=[
        ('OWNER', 'Owner'),
        ('ORG_ADMIN', 'Org admin'),
        ('STAFF', 'Staff'),
    ])


def __str__(self):
    return f"{self.user.username} ({self.role})"    