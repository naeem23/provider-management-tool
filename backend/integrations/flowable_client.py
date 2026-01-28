import requests
from django.conf import settings
from datetime import datetime, time
from django.utils import timezone
import json


def generate_request_task(*, request_id, offer_deadline):
    url = f"{settings.FLOWABLE_BASE_URL}/runtime/process-instances"

    variables = [
        {"name": "request_id", "value": request_id, "type": "string"},
        {"name": "baseApiUrl", "value": settings.DJANGO_BASE_URL, "type": "string"},
    ]

    if offer_deadline:
        if isinstance(offer_deadline, datetime):
            deadline_datetime = offer_deadline
        else:
            deadline_datetime = datetime.combine(
                offer_deadline, 
                time(23, 59, 59)
            )
        
        if timezone.is_naive(deadline_datetime):
            deadline_datetime = timezone.make_aware(deadline_datetime)
        
        deadline_iso = deadline_datetime.isoformat()
        
        variables.append({
            "name": "offer_deadline",
            "value": deadline_iso,
            "type": "date"
        })
    
    payload = {
        "processDefinitionKey": "serviceRequestProcess",
        "businessKey": request_id,
        "variables": variables
    }
    
    try:
        response = requests.post(
            url,
            auth=settings.FLOWABLE_AUTH,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_msg = response.text
        try:
            error_detail = response.json()
            error_msg = error_detail.get('message', error_msg)
        except:
            pass
        
        raise Exception(f"Flowable returned {response.status_code}: {error_msg}")


def start_contract_negotiation(*, contract_data):
    url = f"{settings.FLOWABLE_BASE_URL}/runtime/process-instances"

    variables = [
        {"name": "contract_id", "value": contract_data.get('contract_id')},
        {"name": "title", "value": contract_data.get('title')},
        {"name": "specialist_name", "value": contract_data.get('specialist_name')},
        {"name": "proposed_rate", "value": contract_data.get('proposed_rate')},
        {"name": "providers_expected_rate", "value": contract_data.get('providers_expected_rate')},
        {"name": "valid_from", "value": str(contract_data.get('valid_from'))},
        {"name": "valid_till", "value": str(contract_data.get('valid_till'))},
        {"name": "response_deadline", "value": str(contract_data.get('response_deadline'))},
    ]
    
    payload = {
        "processDefinitionKey": "contractNegotiationProcess",
        "variables": [
            *variables,
            {"name": "baseApiUrl", "value": settings.DJANGO_BASE_URL, "type": "string"},
        ]
    }

    response = requests.post(
        url,
        auth=settings.FLOWABLE_AUTH,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()
    result = response.json()
    return response.json()


def get_tasks_by_group(*, group_id):
    """
    Get all active tasks for a specific group
    """
    url = f"{settings.FLOWABLE_BASE_URL}/runtime/tasks"
    
    params = {
        'candidateGroup': group_id,
        'includeProcessVariables': 'true'
    }
    
    try:
        response = requests.get(
            url,
            params=params,
            auth=settings.FLOWABLE_AUTH,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        tasks = result.get('data', [])
        
        # Extract relevant task information
        formatted_tasks = []
        for task in tasks:
            task_info = {
                'task_id': task.get('id'),
                'task_name': task.get('name'),
                'process_instance_id': task.get('processInstanceId'),
                'created_time': task.get('createTime'),
                'assignee': task.get('assignee'),
                'variables': {}
            }
            
            # Extract process variables
            if task.get('variables'):
                for var in task.get('variables', []):
                    task_info['variables'][var.get('name')] = var.get('value')
            
            formatted_tasks.append(task_info)
        
        return formatted_tasks
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Flowable get tasks failed: {str(e)}")


def get_task_variable(*, task_id):
    """
    Get details of a specific task
    """
    url = f"{settings.FLOWABLE_BASE_URL}/runtime/tasks/{task_id}/variables"
        
    try:
        response = requests.get(
            url,
            auth=settings.FLOWABLE_AUTH,
            timeout=10
        )
        response.raise_for_status()
        
        variables = response.json()
            
        task_info = {
            'task_id': task_id,
            'variables': {}
        }

        # Extract process variables
        if variables and len(variables) > 0:
            for var in variables:
                task_info['variables'][var.get('name')] = var.get('value')
        
        return task_info
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Flowable get task failed: {str(e)}")


def complete_task(*, task_id, action, variables = None):
    """
    Complete a task with action and optional variables
    """
    url = f"{settings.FLOWABLE_BASE_URL}/runtime/tasks/{task_id}"
        
    # Prepare completion variables
    task_variables = [
        {"name": "action", "value": action}
    ]
        
    # Add counter offer/submit offer variables if provided
    if variables:
        if variables.get('contract_id'):
            task_variables.append({
                "name": "contract_id",
                "value": variables.get('contract_id')
            })
        if variables.get('version_id'):
            task_variables.append({
                "name": "version_id",
                "value": variables.get('version_id')
            })
        if variables.get('counter_rate'):
            task_variables.append({
                "name": "counter_rate",
                "value": variables.get('counter_rate')
            })
        if variables.get('counter_explanation'):
            task_variables.append({
                "name": "counter_explanation",
                "value": variables.get('counter_explanation')
            })
        if variables.get('counter_terms'):
            task_variables.append({
                "name": "counter_terms",
                "value": variables.get('counter_terms')
            })

        
        if variables.get('offer_id'):
            task_variables.append({
                "name": "offer_id",
                "value": variables.get('offer_id')
            })
        
    payload = {
        "action": "complete",
        "variables": task_variables
    }
        
    try:
        response = requests.post(
            url,
            json=payload,
            auth=settings.FLOWABLE_AUTH,
            timeout=10
        )
        response.raise_for_status()
        
        return True
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Flowable task completion failed: {str(e)}")


def record_offer_submission(*, task_id, offer_id, provider_id):
    """
    Record that a provider submitted an offer by updating process variables.
    This doesn't complete the task - just tracks submissions.
    """
    try:
        # Get the process instance ID from the task
        task_url = f"{settings.FLOWABLE_BASE_URL}/runtime/tasks/{task_id}"
        response = requests.get(task_url, auth=settings.FLOWABLE_AUTH, timeout=10)
        response.raise_for_status()
        
        task_data = response.json()
        process_instance_id = task_data.get('processInstanceId')
        
        if not process_instance_id:
            return False
        
        # Get existing submissions
        variables_url = f"{settings.FLOWABLE_BASE_URL}/runtime/process-instances/{process_instance_id}/variables"
        
        try:
            var_response = requests.get(
                f"{variables_url}/submitted_offers",
                auth=settings.FLOWABLE_AUTH,
                timeout=10
            )
            if var_response.status_code == 200:
                submitted_offers = var_response.json().get('value', '[]')
                # Parse JSON string if needed
                if isinstance(submitted_offers, str):
                    submitted_offers = json.loads(submitted_offers)
            else:
                submitted_offers = []
        except:
            submitted_offers = []
        
        # Add new submission
        submitted_offers.append({
            'offer_id': offer_id,
            'provider_id': provider_id,
            'submitted_at': datetime.now().isoformat()
        })
        
        # Update process variable
        payload = [
            {
                "name": "submitted_offers",
                "value": json.dumps(submitted_offers),
                "type": "string"
            }
        ]
        
        response = requests.put(
            variables_url,
            json=payload,
            auth=settings.FLOWABLE_AUTH,
            timeout=10
        )
        response.raise_for_status()
        
        return True
        
    except Exception as e:
        print(f"Error recording offer in Flowable: {str(e)}")
        return False