from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class Website:
    """Model representing a discovered website"""
    domain: str
    url: str
    title: str = ""
    keyword: str = ""
    snippet: str = ""
    position: Optional[int] = None
    
    # Extracted data
    posting_links: List[Dict] = field(default_factory=list)
    article_urls: List[str] = field(default_factory=list)
    login_required: Dict = field(default_factory=dict)
    cms_detected: str = "unknown"
    has_sitemap: Optional[str] = None
    contact_page: List[str] = field(default_factory=list)
    
    # Classification
    requires_auth: bool = False
    classification_confidence: float = 0.0
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    last_checked: Optional[datetime] = None
    status: str = "discovered"  # discovered, analyzed, posted, failed
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "domain": self.domain,
            "url": self.url,
            "title": self.title,
            "keyword": self.keyword,
            "posting_links": self.posting_links,
            "article_urls": self.article_urls,
            "requires_auth": self.requires_auth,
            "cms_detected": self.cms_detected,
            "status": self.status
        }