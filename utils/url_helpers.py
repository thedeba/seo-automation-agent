from urllib.parse import urlparse, urljoin
from typing import Optional
import re

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except:
        return url

def normalize_url(url: str) -> str:
    """Normalize URL (remove trailing slash, lowercase scheme/host)"""
    try:
        parsed = urlparse(url)
        normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path}"
        return normalized.rstrip('/')
    except:
        return url

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def join_url_paths(base_url: str, path: str) -> str:
    """Join base URL with path"""
    return urljoin(base_url, path)

def remove_query_params(url: str) -> str:
    """Remove query parameters from URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def get_base_url(url: str) -> str:
    """Get base URL (scheme + domain)"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to same domain"""
    domain1 = extract_domain(url1)
    domain2 = extract_domain(url2)
    return domain1 == domain2

def extract_urls_from_text(text: str) -> list:
    """Extract all URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)