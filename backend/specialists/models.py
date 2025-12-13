from django.db import models
import uuid


class ExperienceLevel(models.TextChoices):
    JUNIOR = "JUNIOR", "Junior"
    MID    = "MID", "Mid"
    SENIOR = "SENIOR", "Senior"


class TechnologyLevel(models.TextChoices):
    L1 = "L1", "L1"
    L2 = "L2", "L2"
    L3 = "L3", "L3"
    L4 = "L4", "L4"
    L5 = "L5", "L5"


class Specialist(models.Model):
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        "providers.Provider", 
        on_delete=models.CASCADE, 
        related_name="specialists"
    )

    first_name        = models.CharField(max_length=64)
    last_name         = models.CharField(max_length=64)

    role_name         = models.CharField(max_length=128) # e.g. Developer, Analyst
    experience_level  = models.CharField(max_length=16, choices=ExperienceLevel.choices)
    technology_level  = models.CharField(max_length=16, choices=TechnologyLevel.choices)

    avg_daily_rate    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    performance_grade = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_available      = models.BooleanField(default=True)

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)