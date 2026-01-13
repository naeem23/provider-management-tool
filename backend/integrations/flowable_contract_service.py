"""
Flowable Service for Contract Negotiation
Handles all interactions with Flowable REST API
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FlowableContractService:
    """Service class to interact with Flowable REST API"""
    
    def __init__(self):
        self.base_url = "http://localhost:8080/flowable-rest/service"
        self.auth = HTTPBasicAuth('rest-admin', 'test')
        self.process_definition_key = "contractNegotiationProcess"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def start_process(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new contract negotiation process instance
        
        Args:
            contract_data: Dictionary containing contract information
                Required keys: contract_id, title, specialist_name, proposed_rate,
                              expected_rate, valid_from, valid_till, response_deadline
        
        Returns:
            Dictionary with process instance details including id and task info
        
        Raises:
            Exception if process start fails
        """
        url = f"{self.base_url}/runtime/process-instances"
        
        # Prepare process variables
        variables = [
            {"name": "contract_id", "value": contract_data.get('id')},
            {"name": "title", "value": contract_data.get('title')},
            {"name": "specialist_name", "value": contract_data.get('specialist_name')},
            {"name": "proposed_rate", "value": contract_data.get('proposed_rate')},
            {"name": "providers_expected_rate", "value": contract_data.get('providers_expected_rate')},
            {"name": "valid_from", "value": str(contract_data.get('valid_from'))},
            {"name": "valid_till", "value": str(contract_data.get('valid_till'))},
            {"name": "response_deadline", "value": str(contract_data.get('response_deadline'))},
        ]
        
        payload = {
            "processDefinitionKey": self.process_definition_key,
            "variables": variables,
            "businessKey": f"contract_{contract_data.get('id')}"
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Process started successfully: {result.get('id')}")
            
            return {
                'process_instance_id': result.get('id'),
                'process_definition_id': result.get('processDefinitionId'),
                'business_key': result.get('businessKey')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start process: {str(e)}")
            raise Exception(f"Flowable process start failed: {str(e)}")
    
    def get_tasks_by_group(self, group_id: str = "contract_coordinator") -> List[Dict[str, Any]]:
        """
        Get all active tasks for a specific group
        
        Args:
            group_id: The candidate group identifier (default: contract_coordinator)
        
        Returns:
            List of task dictionaries with task details and variables
        """
        url = f"{self.base_url}/runtime/tasks"
        
        params = {
            'candidateGroup': group_id,
            'includeProcessVariables': 'true'
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers,
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
            
            logger.info(f"Retrieved {len(formatted_tasks)} tasks for group {group_id}")
            return formatted_tasks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get tasks: {str(e)}")
            raise Exception(f"Flowable get tasks failed: {str(e)}")
    
    def complete_task(self, task_id: str, action: str, 
                     variables: Optional[Dict[str, Any]] = None) -> bool:
        """
        Complete a task with action and optional variables
        
        Args:
            task_id: The Flowable task ID
            action: Action taken (accept/reject/counter_offer)
            variables: Additional variables (e.g., counter_rate, counter_explanation, counter_terms)
        
        Returns:
            True if task completed successfully
        
        Raises:
            Exception if task completion fails
        """
        url = f"{self.base_url}/runtime/tasks/{task_id}"
        
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
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Task {task_id} completed successfully with action: {action}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to complete task: {str(e)}")
            raise Exception(f"Flowable task completion failed: {str(e)}")
    
    def get_task_by_id(self, task_id: str) -> Dict[str, Any]:
        """
        Get details of a specific task
        
        Args:
            task_id: The Flowable task ID
        
        Returns:
            Dictionary with task details
        """
        url = f"{self.base_url}/runtime/tasks/{task_id}"
        
        params = {
            'includeProcessVariables': 'true'
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            task = response.json()
            
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
            
            return task_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get task: {str(e)}")
            raise Exception(f"Flowable get task failed: {str(e)}")


# Singleton instance
flowable_contract_service = FlowableContractService()