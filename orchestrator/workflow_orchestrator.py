import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
from tqdm import tqdm
import pandas as pd
import time
import random

from agents.discovery_agent import WebsiteDiscoveryAgent
from agents.extractor_agent import PostingLinkExtractor
from agents.classifier_agent import AuthClassifier
from agents.distributor_agent import ContentDistributor

class SEOAutomationAgent:
    """Main orchestrator - No API keys required"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self._setup_logging()
        
        self.discovery = WebsiteDiscoveryAgent()
        self.extractor = PostingLinkExtractor()
        self.classifier = AuthClassifier()
        self.distributor = None
        
        self.discovered_sites = []
        self.extracted_data = []
        self.classified_data = {}
        self.distribution_results = {}
    
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'extraction': {
                'max_sites_to_process': 30,
                'crawl_depth': 1
            },
            'distribution': {
                'rate_limit_delay': 3,
                'timeout': 30,
                'max_retries': 3
            },
            'output': {
                'directory': 'data/output',
                'save_intermediate': True
            },
            'search_engines': ['google', 'duckduckgo']
        }
    
    def _setup_logging(self):
        """Setup logging"""
        log_dir = Path("data/output/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_dir / f"automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            rotation="100 MB",
            level="INFO"
        )
    
    def run(self, keywords: List[str], content_path: str, 
            credentials: Dict = None) -> Dict:
        """Execute the complete workflow"""
        logger.info("🚀 Starting SEO Automation (API-Free)")
        
        start_time = datetime.now()
        
        try:
            # Phase 1: Discovery
            logger.info("Phase 1/4: Website Discovery")
            self.discovered_sites = self._phase_discovery(keywords)
            
            if self.discovered_sites.empty:
                logger.warning("No sites discovered!")
                return {"error": "No sites found"}
            
            # Phase 2: Extraction
            logger.info("Phase 2/4: Extracting Posting Links")
            self.extracted_data = self._phase_extraction()
            
            # Phase 3: Classification
            logger.info("Phase 3/4: Classifying Sites")
            self.classified_data = self._phase_classification()
            
            # Phase 4: Distribution
            logger.info("Phase 4/4: Distributing Content")
            self.distribution_results = self._phase_distribution(
                content_path, credentials
            )
            
            self._generate_report(start_time)
            return self.distribution_results
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise
    
    def run_from_urls(self, seed_urls: List[str], content_path: str,
                     credentials: Dict = None) -> Dict:
        """Run workflow starting from specific URLs"""
        logger.info(f"Starting from {len(seed_urls)} seed URLs")
        
        # Discover related sites
        all_sites = []
        for url in seed_urls:
            related = self.discovery.discover_by_related_sites(
                [url], 
                depth=self.config['extraction']['crawl_depth']
            )
            all_sites.extend(related)
            time.sleep(random.uniform(2, 4))
        
        # Also try sitemaps
        for url in seed_urls:
            sitemap_sites = self.discovery.discover_using_sitemaps(url)
            all_sites.extend(sitemap_sites)
        
        # Deduplicate
        self.discovered_sites = pd.DataFrame(all_sites).drop_duplicates(subset=['domain'])
        
        logger.info(f"Discovered {len(self.discovered_sites)} sites from {len(seed_urls)} seed URLs")
        
        # Continue with rest of workflow
        self.extracted_data = self._phase_extraction()
        self.classified_data = self._phase_classification()
        self.distribution_results = self._phase_distribution(content_path, credentials)
        
        return self.distribution_results
    
    def _phase_discovery(self, keywords: List[str]) -> pd.DataFrame:
        """Discover websites"""
        engines = self.config.get('search_engines', ['google', 'duckduckgo'])
        max_results = self.config['extraction'].get('max_sites_to_process', 30)
        
        return self.discovery.search_websites_by_keywords(
            keywords=keywords,
            num_results=max_results,
            search_engines=engines
        )
    
    def _phase_extraction(self) -> List[Dict]:
        """Extract posting links"""
        domains = self.discovered_sites['domain'].tolist()
        max_sites = min(
            len(domains), 
            self.config['extraction'].get('max_sites_to_process', 30)
        )
        
        extracted = []
        for domain in tqdm(domains[:max_sites], desc="Extracting"):
            site_info = self.extractor.find_posting_links(domain)
            extracted.append(site_info)
            time.sleep(random.uniform(1, 3))
        
        return extracted
    
    def _phase_classification(self) -> Dict:
        """Classify sites"""
        no_auth, auth, uncertain = self.classifier.classify_sites(self.extracted_data)
        
        self.classifier.export_classifications(
            self.config['output']['directory']
        )
        
        return {
            'no_auth': no_auth,
            'auth_required': auth,
            'uncertain': uncertain,
            'statistics': self.classifier.get_statistics()
        }
    
    def _phase_distribution(self, content_path: str, 
                           credentials: Dict = None) -> Dict:
        """Distribute content"""
        self.distributor = ContentDistributor(
            sites_without_auth=self.classified_data.get('no_auth', []),
            sites_with_auth=self.classified_data.get('auth_required', [])
        )
        
        results = self.distributor.distribute_content(
            content_path, 
            posting_credentials=credentials
        )
        
        output_dir = self.config['output']['directory']
        self.distributor.save_results(f"{output_dir}/posting_results.json")
        
        return results
    
    def _generate_report(self, start_time: datetime):
        """Generate final report"""
        duration = (datetime.now() - start_time).total_seconds()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration_minutes": f"{duration/60:.1f}",
            "sites_discovered": len(self.discovered_sites),
            "sites_analyzed": len(self.extracted_data),
            "classification": self.classified_data.get('statistics', {}),
            "distribution_summary": self.distribution_results.get('summary', {})
        }
        
        output_dir = Path(self.config['output']['directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / 'report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report saved to {output_dir}/report.json")