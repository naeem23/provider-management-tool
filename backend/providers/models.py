from django.db import models
import uuid


class Provider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name          = models.CharField(max_length=255)
    provider_code = models.CharField(max_length=32, unique=True)
    email         = models.EmailField(blank=True)
    phone         = models.CharField(max_length=32, blank=True)

    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city          = models.CharField(max_length=128, blank=True)
    postal_code   = models.CharField(max_length=16, blank=True)
    country       = models.CharField(max_length=64, blank=True)

    is_active     = models.BooleanField(default=True)

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)
