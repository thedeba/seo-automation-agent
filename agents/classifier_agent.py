from typing import List, Dict, Tuple
import json
from loguru import logger
from models.website_model import Website

class AuthClassifier:
    """Agent for classifying websites by authentication requirements"""
    
    def __init__(self):
        self.sites_with_auth = []
        self.sites_without_auth = []
        self.uncertain_sites = []
        
    def classify_sites(self, sites_data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Separate sites into auth-required and no-auth categories"""
        logger.info(f"Classifying {len(sites_data)} sites...")
        
        for site in sites_data:
            classification = self._classify_single_site(site)
            
            if classification == 'auth_required':
                self.sites_with_auth.append(site)
            elif classification == 'no_auth':
                self.sites_without_auth.append(site)
            else:
                self.uncertain_sites.append(site)
                
        logger.info(f"Classification complete:")
        logger.info(f"  - No auth needed: {len(self.sites_without_auth)}")
        logger.info(f"  - Auth required: {len(self.sites_with_auth)}")
        logger.info(f"  - Uncertain: {len(self.uncertain_sites)}")
        
        return self.sites_without_auth, self.sites_with_auth, self.uncertain_sites
    
    def _classify_single_site(self, site: Dict) -> str:
        """Classify a single site"""
        login_info = site.get('login_required', {})
        
        # Strong indicators of auth requirement
        strong_auth_indicators = sum([
            login_info.get('login_forms', False),
            login_info.get('login_links', False),
            login_info.get('membership_indicators', False)
        ])
        
        # Check posting links for auth keywords
        posting_links = site.get('posting_forms', [])
        auth_in_posting = any(
            self._url_requires_auth(link.get('url', ''))
            for link in posting_links
        )
        
        if strong_auth_indicators >= 2 or auth_in_posting:
            return 'auth_required'
        elif strong_auth_indicators == 0 and not auth_in_posting:
            return 'no_auth'
        else:
            return 'uncertain'
    
    def _url_requires_auth(self, url: str) -> bool:
        """Check if URL pattern suggests authentication"""
        auth_patterns = [
            '/login', '/signin', '/register', '/signup',
            '/wp-admin', '/admin', '/dashboard', '/account'
        ]
        return any(pattern in url.lower() for pattern in auth_patterns)
    
    def export_classifications(self, output_dir: str = "data/output/"):
        """Export classified sites to JSON files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        files = {
            'no_auth_sites.json': self.sites_without_auth,
            'auth_sites.json': self.sites_with_auth,
            'uncertain_sites.json': self.uncertain_sites,
            'classified_sites.json': {
                'no_auth': self.sites_without_auth,
                'auth_required': self.sites_with_auth,
                'uncertain': self.uncertain_sites
            }
        }
        
        for filename, data in files.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Exported {len(data) if isinstance(data, list) else sum(len(v) for v in data.values())} items to {filepath}")
    
    def get_statistics(self) -> Dict:
        """Get classification statistics"""
        return {
            "total_sites": len(self.sites_with_auth) + len(self.sites_without_auth) + len(self.uncertain_sites),
            "no_auth_required": len(self.sites_without_auth),
            "auth_required": len(self.sites_with_auth),
            "uncertain": len(self.uncertain_sites),
            "no_auth_percentage": f"{len(self.sites_without_auth) / max(1, len(self.sites_with_auth) + len(self.sites_without_auth) + len(self.uncertain_sites)) * 100:.1f}%"
        }