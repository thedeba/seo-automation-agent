from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime

@dataclass
class DistributionResult:
    """Model representing content distribution results"""
    content_path: str
    content_type: str
    distribution_date: datetime = field(default_factory=datetime.now)
    
    successful_posts: List[Dict] = field(default_factory=list)
    failed_posts: List[Dict] = field(default_factory=list)
    skipped_sites: List[Dict] = field(default_factory=list)
    
    total_sites_attempted: int = 0
    success_rate: float = 0.0
    
    def calculate_success_rate(self):
        """Calculate the success rate"""
        if self.total_sites_attempted > 0:
            self.success_rate = (len(self.successful_posts) / self.total_sites_attempted) * 100
        return self.success_rate
    
    def to_summary(self) -> Dict:
        """Generate a summary of results"""
        return {
            "content_type": self.content_type,
            "total_attempted": self.total_sites_attempted,
            "successful": len(self.successful_posts),
            "failed": len(self.failed_posts),
            "skipped": len(self.skipped_sites),
            "success_rate": f"{self.success_rate:.1f}%"
        }