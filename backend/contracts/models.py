from django.db import IntegrityError, models
import uuid
import random
import string


class ContractStatus(models.TextChoices):
    PENDING        = "PENDING", "Pending Approval"
    IN_NEGOTIATION = "IN_NEGOTIATION", "In Negotiation"
    ACTIVE         = "ACTIVE", "Active"
    EXPIRED        = "EXPIRED", "Expired"
    REJECTED       = "REJECTED", "Rejected"


class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey("providers.Provider", on_delete=models.CASCADE, related_name="contracts")
    service_request = models.ForeignKey("service_requests.ServiceRequest", on_delete=models.SET_NULL, null=True, blank=True)
    winning_offer = models.ForeignKey("service_requests.ServiceOffer", on_delete=models.SET_NULL, null=True, blank=True)

    title             = models.CharField(max_length=255)
    contract_code     = models.CharField(max_length=32, unique=True, editable=False)
    status            = models.CharField(max_length=32, choices=ContractStatus.choices, default=ContractStatus.PENDING)

    offered_daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    negotiated_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    response_deadline  = models.DateField()
    valid_from        = models.DateField()
    valid_to          = models.DateField()
    terms_and_condition    = models.TextField(blank=True)

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.contract_code:
            self.contract_code = self._generate_contract_code()

        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                super().save(*args, **kwargs)
                break
            except IntegrityError as e:
                if 'contract_code' in str(e) and attempt < max_attempts - 1:
                    # Regenerate code and retry
                    self.contract_code = self._generate_contract_code()
                else:
                    raise

    @staticmethod
    def _generate_contract_code():
        """
        Generates CNT-A3B9, CNT-X7K2, etc.
        """
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"CNT-{random_part}"


class ContractVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    counter_rate = models.DecimalField(max_digits=10, decimal_places=2)
    counter_offer_explanation = models.TextField(blank=True)
    proposed_terms_and_condition = models.TextField(blank=True)
    
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("contract", "version_number")]
