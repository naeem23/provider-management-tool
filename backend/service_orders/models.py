from django.db import models
import uuid


class OrderStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class ServiceOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.ForeignKey("service_requests.ServiceRequest", null=True, blank=True, on_delete=models.SET_NULL)
    winning_offer = models.ForeignKey("service_requests.ServiceOffer", null=True, blank=True, on_delete=models.SET_NULL)

    provider = models.ForeignKey("providers.Provider", on_delete=models.CASCADE, related_name="service_orders")
    specialist = models.ForeignKey("specialists.Specialist", null=True, blank=True, on_delete=models.SET_NULL)

    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.CREATED)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    man_days = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ChangeRequestStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class SubstitutionRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="substitutions")

    requested_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, choices=ChangeRequestStatus.choices, default=ChangeRequestStatus.REQUESTED)

    current_specialist = models.ForeignKey("specialists.Specialist", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    proposed_specialist = models.ForeignKey("specialists.Specialist", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ExtensionRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="extensions")

    requested_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, choices=ChangeRequestStatus.choices, default=ChangeRequestStatus.REQUESTED)

    new_end_date = models.DateField(null=True, blank=True)
    additional_man_days = models.PositiveIntegerField(null=True, blank=True)

    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
