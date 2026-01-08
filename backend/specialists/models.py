import uuid
import random
import string
from django.db import IntegrityError, models
from django.core.validators import MinValueValidator, MaxValueValidator


WORK_MODE_CHOICES = [
    ('Remote', 'Remote'),
    ('On-site', 'On-site'),
    ('Hybrid', 'Hybrid'),
]

STATUS_CHOICES = [
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
    ('On_Leave', 'On Leave'),
]

class ExperienceLevel(models.TextChoices):
    JUNIOR = "JUNIOR", "Junior (0-2 years)"
    MID    = "MID", "Mid-Level (3-5 years)"
    SENIOR = "SENIOR", "Senior (6-10 years)"
    LEAD   = "LEAD", "Lead (10+ years)"
    EXPERT = "EXPERT", "Expert/Architect (15+ years)"


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

    # Identity & contact
    first_name        = models.CharField(max_length=64)
    last_name         = models.CharField(max_length=64)
    email             = models.EmailField(unique=True)
    phone             = models.CharField(max_length=32, blank=True, null=True)
    specialist_code   = models.CharField(max_length=32, unique=True, editable=False)
    
    # Role & Skills
    role_name        = models.CharField(max_length=100, help_text="e.g., Software Engineer, Project Manager")
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices)
    skills           = models.TextField(help_text="Comma-separated skills (e.g., Python, React, AWS)")
    certifications   = models.TextField(blank=True, null=True, help_text="Comma-separated certifications")
    specialization   = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Frontend, Backend, Full-stack")

    # Financial & Availability
    avg_daily_rate    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    available_from    = models.DateField(blank=True, null=True)
    available_until   = models.DateField(blank=True, null=True, help_text="Leave blank if indefinite")
    max_weekly_hours = models.IntegerField(default=40, validators=[MinValueValidator(1), MaxValueValidator(168)])

    # Location & Work Preferences
    location = models.CharField(max_length=200, help_text="City, Country")
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='Remote')
    willing_to_travel = models.BooleanField(default=False)

    # Additional Info
    languages_spoken = models.CharField(max_length=200, help_text="Comma-separated languages (e.g., English, Spanish)")
    notes = models.TextField(blank=True, null=True, help_text="Internal notes")

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.specialist_code:
            self.specialist_code = self._generate_specialist_code()

        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                super().save(*args, **kwargs)
                break
            except IntegrityError as e:
                if 'specialist_code' in str(e) and attempt < max_attempts - 1:
                    # Regenerate code and retry
                    self.specialist_code = self._generate_specialist_code()
                else:
                    raise

    @staticmethod
    def _generate_specialist_code():
        """
        Generates SPE-A3B9, SPE-X7K2, etc.
        """
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"SPE-{random_part}"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.role_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_skills_list(self):
        """Returns skills as a list"""
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
    
    def get_certifications_list(self):
        """Returns certifications as a list"""
        if not self.certifications:
            return []
        return [cert.strip() for cert in self.certifications.split(',') if cert.strip()]