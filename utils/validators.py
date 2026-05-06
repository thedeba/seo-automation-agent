import os
from pathlib import Path
from typing import List, Union
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def validate_keywords(keywords: Union[str, List[str]]) -> List[str]:
    """Validate and clean keywords list"""
    if isinstance(keywords, str):
        # If comma or newline separated string
        if ',' in keywords:
            keywords = [k.strip() for k in keywords.split(',')]
        elif '\n' in keywords:
            keywords = [k.strip() for k in keywords.split('\n')]
        else:
            keywords = [keywords.strip()]
    
    # Filter out empty keywords
    keywords = [k for k in keywords if k and len(k) >= 2]
    
    if not keywords:
        raise ValueError("No valid keywords provided")
    
    return keywords

def validate_file_path(file_path: str, must_exist: bool = True) -> bool:
    """Validate file path"""
    if must_exist:
        return os.path.isfile(file_path)
    
    # Check if directory is writable
    directory = os.path.dirname(file_path)
    return os.access(directory, os.W_OK)

def validate_config(config: dict) -> bool:
    """Validate configuration dictionary"""
    required_keys = ['serpapi']
    
    for key in required_keys:
        if key not in config:
            return False
    
    if 'api_key' not in config.get('serpapi', {}):
        return False
    
    return True

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove potentially dangerous characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:195] + ext
    
    return filename