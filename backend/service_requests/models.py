from django.db import models
from specialists.models import ExperienceLevel, TechnologyLevel
import uuid


class RequestStatus(models.TextChoices):
    IMPORTED  = "IMPORTED", "Imported"
    OPEN      = "OPEN", "Open for offers"
    CLOSED    = "CLOSED", "Closed"
    AWARDED   = "AWARDED", "Awarded"
    CANCELLED = "CANCELLED", "Cancelled"


class ServiceRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    external_request_id = models.CharField(max_length=128, blank=True) # imported from 3rd party
    status              = models.CharField(max_length=16, choices=RequestStatus.choices, default=RequestStatus.IMPORTED)

    domain              = models.CharField(max_length=128) # business domain
    role_name           = models.CharField(max_length=128) # requested role
    technology          = models.CharField(max_length=128, blank=True)

    experience_level    = models.CharField(max_length=16, choices=ExperienceLevel.choices, blank=True)
    technology_level    = models.CharField(max_length=8, choices=TechnologyLevel.choices, blank=True)

    start_date          = models.DateField(null=True, blank=True)
    end_date            = models.DateField(null=True, blank=True)
    expected_man_days   = models.PositiveIntegerField(null=True, blank=True)

    criteria_json       = models.JSONField(default=dict, blank=True)

    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)


class OfferStatus(models.TextChoices):
    DRAFT     = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"
    REJECTED  = "REJECTED", "Rejected"
    ACCEPTED  = "ACCEPTED", "Accepted"


class ServiceOffer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request      = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="offers")
    provider     = models.ForeignKey("providers.Provider", on_delete=models.CASCADE, related_name="offers")
    submitted_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)

    status       = models.CharField(max_length=16, choices=OfferStatus.choices, default=OfferStatus.DRAFT)

    proposed_specialist = models.ForeignKey(
        "specialists.Specialist", 
        null=True, blank=True, 
        on_delete=models.SET_NULL
    )

    daily_rate   = models.DecimalField(max_digits=10, decimal_places=2)
    travel_cost  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost   = models.DecimalField(max_digits=12, decimal_places=2)

    notes        = models.TextField(blank=True)

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["request", "status"]),
        ]
