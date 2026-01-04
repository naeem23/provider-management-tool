import requests
from django.conf import settings


FLOWABLE_BASE_URL = "http://flowable-rest:8080/flowable-rest"
FLOWABLE_AUTH = ("rest-admin", "test")


def start_service_request_bidding_process(*, service_request_id):
    """
    Starts the Service Request Bidding BPMN process in Flowable.
    """
    url = f"{FLOWABLE_BASE_URL}/service/runtime/process-instances"

    payload = {
        "processDefinitionKey": "serviceRequestBidding",
        "variables": [
            {
                "name": "serviceRequestId",
                "value": str(service_request_id),
                "type": "string",
            },
            {
                "name": "baseApiUrl",
                "value": "http://django:8000",
                "type": "string",
            },
        ],
    }

    response = requests.post(
        url,
        auth=FLOWABLE_AUTH,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def start_contract_negotiation(*, contract_id):
    url = f"{FLOWABLE_BASE_URL}/service/runtime/process-instances"
    
    payload = {
        "processDefinitionKey": "contractNegotiation",
        "variables": [
            {"name": "contractId", "value": str(contract_id), "type": "string"},
            {"name": "baseApiUrl", "value": "http://django:8000", "type": "string"},
        ],
    }

    response = requests.post(
        url,
        auth=FLOWABLE_AUTH,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()
    return response.json()

