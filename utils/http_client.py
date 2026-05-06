import requests
from typing import Optional, Dict, Any
from fake_useragent import UserAgent
import time
from loguru import logger

class HTTPClient:
    """HTTP client with user-agent rotation and rate limiting"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_delay = 1  # Minimum delay between requests in seconds
    
    def get_random_user_agent(self) -> str:
        """Get random user agent string"""
        return self.ua.random
    
    def get_headers(self) -> Dict[str, str]:
        """Get default headers with random user agent"""
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def get(self, url: str, params: Optional[Dict] = None, timeout: int = 30, **kwargs) -> Optional[requests.Response]:
        """Make GET request"""
        self._rate_limit()
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=self.get_headers(),
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"GET request failed for {url}: {str(e)}")
            return None
    
    def post(self, url: str, data: Optional[Dict] = None, json: Optional[Dict] = None,
             files: Optional[Dict] = None, timeout: int = 30, **kwargs) -> Optional[requests.Response]:
        """Make POST request"""
        self._rate_limit()
        
        try:
            response = self.session.post(
                url,
                data=data,
                json=json,
                files=files,
                headers=self.get_headers(),
                timeout=timeout,
                **kwargs
            )
            return response
        except requests.RequestException as e:
            logger.error(f"POST request failed for {url}: {str(e)}")
            return None

# Create global instance
http_client = HTTPClient()

def make_request(url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
    """Convenience function for making HTTP requests"""
    if method.upper() == 'GET':
        return http_client.get(url, **kwargs)
    elif method.upper() == 'POST':
        return http_client.post(url, **kwargs)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

def get_random_user_agent() -> str:
    """Get random user agent"""
    return http_client.get_random_user_agent()