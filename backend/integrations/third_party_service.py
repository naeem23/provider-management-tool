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
            response = requests.post(url, json=payload, headers=headers)
            
            # If the request was successful (status code 200)
            if response.status_code in [200, 201]:
                return response
            else:
                # Log the error
                print(f"API Error: {response.status_code} - {response.text}")
                # Raise exception so caller knows it failed
                raise Exception(f"API returned status {response.status_code}: {response.text}")
        
        except requests.exceptions.Timeout:
            print("Request timed out")
            raise Exception("Third party API request timed out")
        
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
            raise Exception(f"Failed to connect to third party API: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise Exception(f"Third party API request failed: {str(e)}")


# Singleton instance
third_party_service = ThirdPartyService()