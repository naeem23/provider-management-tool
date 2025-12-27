from accounts.models import UserRole
from notifications.utils import create_notification
from audit_log.models import AuditAction


def handle_audit_event(audit_log):
    """
    Convert selected audit events into notifications.
    """
    entity = audit_log.entity_type
    action = audit_log.action
    actor = audit_log.actor

    # -------------------------------
    # SERVICE REQUEST EVENTS
    # -------------------------------
    if entity == "ServiceRequest" and action == AuditAction.STATUS_CHANGE:
        _notify_service_request_status_change(audit_log)

    # -------------------------------
    # SERVICE OFFER EVENTS
    # -------------------------------
    if entity == "ServiceOffer" and action == AuditAction.STATUS_CHANGE:
        _notify_service_offer_status_change(audit_log)

    # -------------------------------
    # SERVICE ORDER EVENTS
    # -------------------------------
    if entity == "ServiceOrder" and action == AuditAction.STATUS_CHANGE:
        _notify_service_order_status_change(audit_log)

    # -------------------------------
    # CONTRACT EVENTS
    # -------------------------------
    if entity == "Contract" and action == AuditAction.STATUS_CHANGE:
        _notify_contract_status_change(audit_log)



def _notify_service_request_status_change(audit_log):
    from requests.models import ServiceRequest

    request = ServiceRequest.objects.filter(pk=audit_log.entity_id).first()
    if not request:
        return

    # Notify Internal PMs
    users = request.provider.users.filter(
        role=UserRole.INTERNAL_PM
    )

    for user in users:
        create_notification(
            user=user,
            title="Service Request Status Updated",
            message=f"Service request {request.id} is now {request.status}.",
            entity=request,
        )



def _notify_service_offer_status_change(audit_log):
    from requests.models import ServiceOffer, OfferStatus

    offer = ServiceOffer.objects.filter(pk=audit_log.entity_id).first()
    if not offer:
        return

    if offer.status == OfferStatus.SUBMITTED:
        # Notify Internal PM
        pm_users = offer.provider.users.filter(
            role=UserRole.INTERNAL_PM
        )
        for user in pm_users:
            create_notification(
                user=user,
                title="New Offer Submitted",
                message="A supplier has submitted an offer.",
                entity=offer,
            )

    if offer.status in [OfferStatus.ACCEPTED, OfferStatus.REJECTED]:
        # Notify Supplier Rep
        if offer.submitted_by:
            create_notification(
                user=offer.submitted_by,
                title=f"Offer {offer.status}",
                message=f"Your offer has been {offer.status.lower()}.",
                entity=offer,
            )



def _notify_service_order_status_change(audit_log):
    from orders.models import ServiceOrder, OrderStatus

    order = ServiceOrder.objects.filter(pk=audit_log.entity_id).first()
    if not order:
        return

    if order.status == OrderStatus.CREATED:
        recipients = order.provider.users.filter(
            role=UserRole.SUPPLIER_REP
        )

    elif order.status == OrderStatus.IN_PROGRESS:
        recipients = order.provider.users.filter(
            role=UserRole.INTERNAL_PM
        )

    elif order.status == OrderStatus.COMPLETED:
        recipients = order.provider.users.filter(
            role__in=[UserRole.INTERNAL_PM, UserRole.PROVIDER_ADMIN]
        )

    else:
        return

    for user in recipients:
        create_notification(
            user=user,
            title="Service Order Update",
            message=f"Service order {order.id} is now {order.status}.",
            entity=order,
        )



def _notify_contract_status_change(audit_log):
    from contracts.models import Contract, ContractStatus

    contract = Contract.objects.filter(pk=audit_log.entity_id).first()
    if not contract:
        return

    recipients = contract.provider.users.filter(
        role__in=[
            UserRole.CONTRACT_COORDINATOR,
            UserRole.PROVIDER_ADMIN,
        ]
    )

    for user in recipients:
        create_notification(
            user=user,
            title="Contract Status Updated",
            message=f"Contract {contract.contract_code} is now {contract.status}.",
            entity=contract,
        )
