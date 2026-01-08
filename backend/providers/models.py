import uuid
import random
import string
from django.db import IntegrityError, models


class Provider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name          = models.CharField(max_length=255)
    provider_code = models.CharField(max_length=32, unique=True, editable=False)
    email         = models.EmailField()
    phone         = models.CharField(max_length=32)

    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city          = models.CharField(max_length=128, blank=True)
    postal_code   = models.CharField(max_length=16, blank=True)
    country       = models.CharField(max_length=64, blank=True)

    is_active     = models.BooleanField(default=True)

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "email", "phone"],
                name="unique_provider_identity"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.provider_code:
            self.provider_code = self._generate_provider_code()

        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                super().save(*args, **kwargs)
                break
            except IntegrityError as e:
                if 'provider_code' in str(e) and attempt < max_attempts - 1:
                    # Regenerate code and retry
                    self.provider_code = self._generate_provider_code()
                else:
                    raise

    @staticmethod
    def _generate_provider_code():
        """
        Generates PROV-A3B9, PROV-X7K2, etc.
        """
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"PROV-{random_part}"

    def __str__(self):
        return f"{self.provider_code} - {self.name}"

