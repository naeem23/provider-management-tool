from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AuditLog(models.Model):
    """
    Audit log to track all user actions in the system
    """
    
    # Action Categories
    ACTION_CATEGORIES = [
        ('USER_MANAGEMENT', 'User Management'),
        ('SPECIALIST_MANAGEMENT', 'Specialist Management'),
        ('OFFER_MANAGEMENT', 'Offer Management'),
        ('CONTRACT_MANAGEMENT', 'Contract Management'),
        ('AUTHENTICATION', 'Authentication'),
    ]
    
    # Specific Actions
    ACTION_TYPES = [
        # User Management (Provider Admin)
        ('USER_CREATED', 'User Created'),
        ('USER_UPDATED', 'User Updated'),
        ('USER_ROLE_CHANGED', 'User Role Changed'),
        ('USER_DELETED', 'User Deleted'),
        
        # Specialist Management (Provider Admin)
        ('SPECIALIST_CREATED', 'Specialist Created'),
        ('SPECIALIST_UPDATED', 'Specialist Updated'),
        ('SPECIALIST_DELETED', 'Specialist Deleted'),
        ('SPECIALIST_ASSIGNED', 'Specialist Assigned to Service Request'),
        
        # Offer Management (Supplier Representative)
        ('REQUEST_GENERATED', 'Request Generated'),
        ('OFFER_SUBMITTED', 'Offer Submitted'),
        ('OFFER_UPDATED', 'Offer Updated'),
        ('OFFER_WITHDRAWN', 'Offer Withdrawn'),
        ('OFFER_ACCEPTED', 'Offer Accepted'),
        ('OFFER_REJECTED', 'Offer Rejected'),
        
        # Contract Management (Contract Coordinator)
        ('CONTRACT_ACCEPTED', 'Contract Accepted'),
        ('CONTRACT_REJECTED', 'Contract Rejected'),
        ('CONTRACT_EXPIRED', 'Contract Expired'),
        ('CONTRACT_UPDATED', 'Contract Updated'),
        ('CONTRACT_COUNTER_OFFER', 'Contract Counter Offer Submitted'),
        ('CONTRACT_NEGOTIATION_STARTED', 'Contract Negotiation Started'),
        
        # Authentication
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('PASSWORD_CHANGED', 'Password Changed'),
        ('PASSWORD_RESET', 'Password Reset'),
    ]
    
    # Result/Status
    RESULT_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('PENDING', 'Pending'),
        ('ERROR', 'Error'),
    ]
    
    # User who performed the action
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        help_text='User who performed the action'
    )
    
    # User role at the time of action
    user_role = models.CharField(
        max_length=50,
        help_text='Role of the user when action was performed'
    )
    
    # Action details
    action_category = models.CharField(
        max_length=50,
        choices=ACTION_CATEGORIES,
        db_index=True
    )
    
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        db_index=True
    )
    
    # Result of the action
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='SUCCESS'
    )
    
    # Description/Details
    description = models.TextField(
        help_text='Detailed description of the action',
        blank=True
    )
    
    # Related object information
    entity_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='Type of related object (e.g., Offer, Contract, Specialist)'
    )
    
    entity_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='ID of the related object'
    )
    
    # Additional context (JSON field for flexibility)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context data (e.g., old values, new values,)'
    )
    
    # created_at
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_category', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.user} - {self.action_type}"
    
    @classmethod
    def log_action(cls, user, action_type, action_category, description='', entity_type='', entity_id='', metadata=None, result='SUCCESS', request=None):
        """
        Helper method to create audit log entries
        
        Usage:
        AuditLog.log_action(
            user=request.user,
            action_type='OFFER_SUBMITTED',
            action_category='OFFER_MANAGEMENT',
            description='Submitted offer for SR-2024-001',
            entity_type='Offer',
            entity_id='OFF-001',
            metadata={'service_request_id': 'SR-2024-001', 'daily_rate': 850},
            request=request
        )
        """
        return cls.objects.create(
            user=user,
            user_role=getattr(user, 'role', 'Unknown'),
            action_category=action_category,
            action_type=action_type,
            result=result,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
        )
