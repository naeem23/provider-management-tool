import requests

FLOWABLE_BASE_URL = "http://localhost:8080/flowable-rest"
FLOWABLE_AUTH = ("rest-admin", "test")


def create_group(group_id, group_name):
    """Create a group in Flowable"""
    url = f"{FLOWABLE_BASE_URL}/service/identity/groups"
    payload = {
        "id": group_id,
        "name": group_name,
        "type": "assignment"
    }
    response = requests.post(url, auth=FLOWABLE_AUTH, json=payload)
    if response.status_code == 201:
        print(f"✓ Group '{group_id}' created successfully")
    elif response.status_code == 409:
        print(f"⚠ Group '{group_id}' already exists")
    else:
        print(f"✗ Failed to create group '{group_id}': {response.text}")
    return response


def create_user(user_id, first_name, last_name, email, password):
    """Create a user in Flowable"""
    url = f"{FLOWABLE_BASE_URL}/service/identity/users"
    payload = {
        "id": user_id,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "password": password
    }
    response = requests.post(url, auth=FLOWABLE_AUTH, json=payload)
    if response.status_code == 201:
        print(f"✓ User '{user_id}' created successfully")
    elif response.status_code == 409:
        print(f"⚠ User '{user_id}' already exists")
    else:
        print(f"✗ Failed to create user '{user_id}': {response.text}")
    return response


def add_user_to_group(user_id, group_id):
    """Add a user to a group"""
    url = f"{FLOWABLE_BASE_URL}/service/identity/groups/{group_id}/members"
    payload = {"userId": user_id}
    response = requests.post(url, auth=FLOWABLE_AUTH, json=payload)
    if response.status_code == 201:
        print(f"✓ User '{user_id}' added to group '{group_id}'")
    elif response.status_code == 409:
        print(f"⚠ User '{user_id}' already in group '{group_id}'")
    else:
        print(f"✗ Failed to add user '{user_id}' to group '{group_id}': {response.text}")
    return response


def setup_flowable_users_and_groups():
    """Complete setup for the service request bidding process"""
    
    print("\n=== Creating Groups ===")
    create_group("supplier_rep", "Supplier Representatives")
    create_group("internal_pm", "Internal Project Managers")
    
    print("\n=== Creating Users ===")
    create_user("supplier1", "John", "Supplier", "supplier1@example.com", "password123")
    create_user("supplier2", "Jane", "Provider", "supplier2@example.com", "password123")
    create_user("pm1", "Mike", "Manager", "pm1@example.com", "password123")
    
    print("\n=== Adding Users to Groups ===")
    add_user_to_group("supplier1", "supplier_rep")
    add_user_to_group("supplier2", "supplier_rep")
    add_user_to_group("pm1", "internal_pm")
    
    print("\n=== Setup Complete ===")
    print("\nYou can now login to Flowable Task App with:")
    print("  - Username: supplier1, Password: password123")
    print("  - Username: supplier2, Password: password123")
    print("  - Username: pm1, Password: password123")


def check_active_tasks():
    """Check for active tasks in the system"""
    url = f"{FLOWABLE_BASE_URL}/service/runtime/tasks"
    response = requests.get(url, auth=FLOWABLE_AUTH)
    
    if response.status_code == 200:
        tasks = response.json().get('data', [])
        print(f"\n=== Active Tasks: {len(tasks)} ===")
        for task in tasks:
            print(f"Task: {task['name']} (ID: {task['id']})")
            print(f"  Assignee: {task.get('assignee', 'None')}")
            print(f"  Candidate Groups: {task.get('candidateGroups', [])}")
            print()
    else:
        print(f"Failed to fetch tasks: {response.text}")


def check_process_instances():
    """Check for active process instances"""
    url = f"{FLOWABLE_BASE_URL}/service/runtime/process-instances"
    response = requests.get(url, auth=FLOWABLE_AUTH)
    
    if response.status_code == 200:
        instances = response.json().get('data', [])
        print(f"\n=== Active Process Instances: {len(instances)} ===")
        for instance in instances:
            print(f"Process: {instance['processDefinitionName']} (ID: {instance['id']})")
            print(f"  Started: {instance['startTime']}")
            print()
    else:
        print(f"Failed to fetch process instances: {response.text}")


if __name__ == "__main__":
    print("Starting Flowable Setup...")
    setup_flowable_users_and_groups()
    
    print("\n" + "="*50)
    check_process_instances()
    check_active_tasks()