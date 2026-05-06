import os
from pathlib import Path
from typing import Optional, Dict, Union
import mimetypes
from datetime import datetime

def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """Read file content"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """Write content to file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False

def detect_file_type(file_path: str) -> str:
    """Detect file type based on extension and MIME type"""
    extension = Path(file_path).suffix.lower()
    
    type_map = {
        '.pdf': 'pdf',
        '.txt': 'text',
        '.md': 'markdown',
        '.csv': 'csv',
        '.json': 'json',
        '.xml': 'xml',
        '.html': 'html',
        '.htm': 'html',
        '.doc': 'document',
        '.docx': 'document',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.mp4': 'video',
        '.zip': 'archive'
    }
    
    if extension in type_map:
        return type_map[extension]
    
    # Try MIME type detection
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        main_type = mime_type.split('/')[0]
        return main_type
    
    return 'unknown'

def get_file_info(file_path: str) -> Dict:
    """Get file information"""
    path = Path(file_path)
    
    if not path.exists():
        return {"exists": False}
    
    stat = path.stat()
    
    return {
        "exists": True,
        "name": path.name,
        "extension": path.suffix,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "type": detect_file_type(file_path),
        "path": str(path.absolute())
    }

def ensure_directory(directory_path: str) -> bool:
    """Ensure directory exists, create if not"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def list_files(directory_path: str, pattern: str = "*") -> list:
    """List files in directory matching pattern"""
    path = Path(directory_path)
    if not path.exists():
        return []
    return list(path.glob(pattern))