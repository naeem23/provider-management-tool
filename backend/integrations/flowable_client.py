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


def start_contract_negotiation(*, contract_data):
    url = f"{FLOWABLE_BASE_URL}/service/runtime/process-instances"

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
            {"name": "baseApiUrl", "value": "http://django:8000", "type": "string"},
        ]
    }

    response = requests.post(
        url,
        auth=FLOWABLE_AUTH,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()
    result = response.json()
    print(f"Process started successfully: {result.get('id')}")
    return response.json()


def get_tasks_by_group(*, group_id):
    """
    Get all active tasks for a specific group
    """
    url = f"{FLOWABLE_BASE_URL}/service/runtime/tasks"
    
    params = {
        'candidateGroup': group_id,
        'includeProcessVariables': 'true'
    }
    
    try:
        response = requests.get(
            url,
            params=params,
            auth=FLOWABLE_AUTH,
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
    url = f"{FLOWABLE_BASE_URL}/service/runtime/tasks/{task_id}/variables"
        
    try:
        response = requests.get(
            url,
            auth=FLOWABLE_AUTH,
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
                print("variables name ======= ", var.get('name'), " =====value===== ", var.get('value'))
                task_info['variables'][var.get('name')] = var.get('value')
        
        return task_info
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Flowable get task failed: {str(e)}")


def complete_contract_task(*, task_id, action, variables = None):
    """
    Complete a task with action and optional variables
    """
    url = f"{FLOWABLE_BASE_URL}/service/runtime/tasks/{task_id}"
        
    # Prepare completion variables
    task_variables = [
        {"name": "action", "value": action}
    ]
        
    # Add counter offer variables if provided
    if variables:
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
        
    payload = {
        "action": "complete",
        "variables": task_variables
    }
        
    try:
        response = requests.post(
            url,
            json=payload,
            auth=FLOWABLE_AUTH,
            timeout=10
        )
        response.raise_for_status()
        
        return True
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Flowable task completion failed: {str(e)}")