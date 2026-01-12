"""
Third Party API Service
Replace with your actual 3rd party API implementation
"""
import requests
import logging

logger = logging.getLogger(__name__)


class ThirdPartyService:
    """Service to interact with 3rd party contract API"""
    
    def __init__(self):
        # Configure these based on your 3rd party API
        self.base_url = "https://api.thirdparty.com"  # Replace with actual URL
        self.api_key = "your_api_key"  # Replace with actual API key
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
    
    def update_contract_status(self, external_id: str, status: str) -> dict:
        """
        Update contract status in 3rd party system
        
        Args:
            external_id: The contract ID in 3rd party system
            status: New status to set
        
        Returns:
            Response from 3rd party API
        
        Raises:
            Exception if update fails
        """
        url = f"{self.base_url}/contracts/{external_id}/status"
        
        payload = {
            'status': status
        }
        
        try:
            # Replace this with your actual API call
            response = requests.put(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully updated contract {external_id} to status: {status}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update 3rd party contract status: {str(e)}")
            raise Exception(f"3rd party API update failed: {str(e)}")


# Singleton instance
third_party_service = ThirdPartyService()