from dataclasses import dataclass
from typing import Optional, List

@dataclass
class PostingLink:
    """Model representing a posting link/form"""
    url: str
    method: str = "GET"
    link_type: str = "link"  # link, form, text_link
    text: str = ""
    form_id: Optional[str] = None
    matched_pattern: Optional[str] = None
    
    # Content support
    supports_pdf: bool = False
    supports_text: bool = True
    supports_images: bool = False
    
    def is_form(self) -> bool:
        return self.link_type == "form"
    
    def is_viable(self) -> bool:
        return bool(self.url and self.url.startswith(('http://', 'https://')))