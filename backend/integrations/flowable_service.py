import requests
from django.conf import settings


class FlowableUserService:
    @staticmethod
    def create_user(username, first_name, last_name, email, password):
        """Create user in Flowable"""
        url = f"{settings.FLOWABLE_BASE_URL}/identity/users"
        payload = {
            "id": username,
            "firstName": first_name,
            "lastName": last_name,
            "email": email if email else f"{username}@gmail.com",
            "password": password
        }
        
        try:
            response = requests.post(url, json=payload, auth=settings.FLOWABLE_AUTH)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating Flowable user: {e}")
            return None
    
    @staticmethod
    def add_user_to_group(username, group_id):
        """Add user to a Flowable group"""
        url = f"{settings.FLOWABLE_BASE_URL}/identity/groups/{group_id}/members"
        payload = {
            "userId": username
        }
        
        try:
            response = requests.post(url, json=payload, auth=settings.FLOWABLE_AUTH)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error adding user to group: {e}")
            return None
    
    @staticmethod
    def create_group_if_not_exists(group_id, group_name):
        """Create group in Flowable if it doesn't exist"""
        url = f"{settings.FLOWABLE_BASE_URL}/identity/groups"
        payload = {
            "id": group_id,
            "name": group_name,
            "type": "assignment"
        }
        
        try:
            response = requests.post(url, json=payload, auth=settings.FLOWABLE_AUTH)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if "already exists" in str(e):
                return None  # Group already exists
            print(f"Error creating Flowable group: {e}")
            return None

            