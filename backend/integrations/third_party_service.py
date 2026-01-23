"""
Third Party API Service
Replace with your actual 3rd party API implementation
"""
import requests
# import logging

# logger = logging.getLogger(__name__)


class ThirdPartyService:
    """Service to interact with 3rd party contract API"""
    
    def call_api(self, url, payload):
        headers = {
            'content-type': 'application/json'
        }

        try:
            # Send the POST request to the 3rd party API
            try:
                print('.................... try ..........................')
                response = requests.post(url, json=payload, headers=headers)
            except Exception as e:
                print(str(e))
            
            # If the request was successful (status code 200)
            print('.......response........', response)
            if response.status_code in [201, 200]:
                print('.......response........200')
                return True
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return False


# Singleton instance
third_party_service = ThirdPartyService()