import pandas as pd
from typing import List, Dict
from urllib.parse import urlparse
import time
import random
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from loguru import logger
import requests
from bs4 import BeautifulSoup
from googlesearch import search as google_search
from ddgs import DDGS

class WebsiteDiscoveryAgent:
    """Agent for discovering websites without APIs"""
    
    def __init__(self):
        self.discovered_sites = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
    def search_websites_by_keywords(
        self, 
        keywords: List[str], 
        num_results: int = 50,
        search_engines: List[str] = ['google', 'duckduckgo', 'bing']
    ) -> pd.DataFrame:
        """Find websites using free search methods"""
        all_results = []
        
        for keyword in keywords:
            logger.info(f"Searching for keyword: {keyword}")
            
            for engine in search_engines:
                try:
                    if engine == 'google':
                        results = self._search_google(keyword, num_results)
                    elif engine == 'duckduckgo':
                        results = self._search_duckduckgo(keyword, num_results)
                    elif engine == 'bing':
                        results = self._search_bing(keyword, num_results)
                    else:
                        continue
                    
                    all_results.extend(results)
                    logger.info(f"  {engine}: Found {len(results)} results")
                    
                    # Filter for recently updated sites
                    if results:
                        logger.debug(f"  Before filtering: {len(results)} results")
                        filtered_results = self._filter_recent_sites(results)
                        logger.debug(f"  After filtering: {len(filtered_results)} results")
                        # Replace results with filtered ones
                        all_results[-len(results):] = filtered_results
                    
                    time.sleep(random.uniform(2, 5))  # Avoid rate limiting
                    
                except Exception as e:
                    logger.error(f"  {engine} search failed: {str(e)}")
            
            time.sleep(random.uniform(3, 7))
        
        # Remove duplicates and save
        unique_sites = self._deduplicate_sites(all_results)
        self.discovered_sites = unique_sites
        logger.info(f"Total unique sites discovered: {len(unique_sites)}")
        
        return pd.DataFrame(unique_sites)
    
    def _search_google(self, keyword: str, num_results: int) -> List[Dict]:
        """Search using Google (free method)"""
        results = []
        
        try:
            logger.debug(f"  Searching Google for: {keyword}")
            rank = 1
            search_results = list(google_search(
                keyword,
                num_results=num_results,
                sleep_interval=int(random.uniform(2, 4))
            ))
            logger.debug(f"  Google search returned {len(search_results)} raw results")
            
            for result in search_results:
                url = str(result)
                logger.debug(f"  Processing result: {url}")
                site_data = self._create_site_entry(url, keyword, 'Google')
                site_data['rank'] = rank
                results.append(site_data)
                rank += 1
                
        except Exception as e:
            logger.error(f"Google search error: {e}")
            
        return results
    
    def _search_duckduckgo(self, keyword: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo (free, no API key needed)"""
        results = []
        
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    keyword,
                    max_results=num_results
                )
                
                rank = 1
                for result in search_results:
                    url = self._normalize_attr(result.get('href') or result.get('link'))
                    if url:
                        site_data = {
                            "keyword": keyword,
                            "title": self._normalize_attr(result.get('title'), ''),
                            "url": url,
                            "domain": self._extract_domain(url),
                            "snippet": self._normalize_attr(result.get('body'), ''),
                            "source": "DuckDuckGo",
                            "rank": rank,
                            "last_modified": None
                        }
                        results.append(site_data)
                        rank += 1
                        
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            
        return results
    
    def _search_bing(self, keyword: str, num_results: int) -> List[Dict]:
        """Search using Bing (web scraping method)"""
        results = []
        
        try:
            search_url = f"https://www.bing.com/search?q={keyword}&count={num_results}"
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find search results
            rank = 1
            for result in soup.find_all('li', class_='b_algo'):
                link = result.find('a', href=True)
                if link:
                    url = self._normalize_attr(link.get('href'))
                    title_tag = result.find('h2')
                    title = title_tag.get_text() if title_tag else ''
                    
                    site_data = {
                        "keyword": keyword,
                        "title": title,
                        "url": url,
                        "domain": self._extract_domain(url),
                        "snippet": '',
                        "source": "Bing",
                        "rank": rank,
                        "last_modified": None
                    }
                    results.append(site_data)
                    rank += 1
                    
        except Exception as e:
            logger.error(f"Bing search error: {e}")
            
        return results
    
    def find_websites_by_directory_scraping(self, directory_url: str) -> List[Dict]:
        """Scrape website directories and listing sites"""
        results = []
        
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(directory_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract all external links
            for link in soup.find_all('a', href=True):
                url = self._normalize_attr(link.get('href'))
                if url.startswith(('http://', 'https://')):
                    site_data = {
                        "keyword": "directory_scraping",
                        "title": link.get_text().strip(),
                        "url": url,
                        "domain": self._extract_domain(url),
                        "snippet": '',
                        "source": "Directory",
                        "rank": 999,
                        "last_modified": None
                    }
                    results.append(site_data)
                    
        except Exception as e:
            logger.error(f"Directory scraping error: {e}")
            
        return results
    
    def _create_site_entry(self, url: str, keyword: str, source: str) -> Dict:
        """Create standardized site entry"""
        title, _ = self._fetch_title_and_modified(url)
        return {
            "keyword": keyword,
            "title": title,
            "url": url,
            "domain": self._extract_domain(url),
            "snippet": '',
            "source": source,
            "rank": 999,  # Default high rank for non-search sources
            "last_modified": None
        }
    
    def _fetch_title_and_modified(self, url: str) -> tuple[str, None]:
        """Fetch webpage title"""
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'lxml')
            title = soup.find('title')
            return title.get_text().strip() if title else '', None
        except Exception:
            return '', None
    
    def _normalize_attr(self, value, default='') -> str:
        """Normalize BeautifulSoup attribute values"""
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip()
        if hasattr(value, 'get_text'):
            return value.get_text().strip()
        return str(value).strip()
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except:
            return url

    def _filter_recent_sites(self, sites: List[Dict]) -> List[Dict]:
        """Filter sites to prioritize those updated in the last 24 hours"""
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        filtered = []
        
        for site in sites:
            url = site.get('url')
            if not url:
                continue
            
            # If already checked during site creation, use that
            if site.get('last_modified'):
                last_modified = site['last_modified']
                if last_modified >= cutoff:
                    filtered.append(site)
                    logger.debug(f"  Site {url} already checked, updated recently")
                else:
                    logger.debug(f"  Site {url} already checked, too old - skipping")
                continue
                
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                response = requests.head(url, headers=headers, timeout=5)
                last_modified_header = response.headers.get('last-modified')
                
                if last_modified_header:
                    try:
                        last_modified = parsedate_to_datetime(last_modified_header)
                        if last_modified.tzinfo is None:
                            last_modified = last_modified.replace(tzinfo=timezone.utc)
                        
                        if last_modified >= cutoff:
                            site['last_modified'] = last_modified
                            filtered.append(site)
                            logger.debug(f"  Site {url} updated recently: {last_modified}")
                        else:
                            logger.debug(f"  Site {url} too old: {last_modified} - skipping")
                    except Exception as e:
                        logger.debug(f"  Could not parse date for {url}: {e}")
                        # Include sites where we can't parse the date
                        filtered.append(site)
                else:
                    # Include sites without Last-Modified header
                    logger.debug(f"  No Last-Modified header for {url} - including")
                    filtered.append(site)
                    
            except Exception as e:
                logger.debug(f"  Error checking {url}: {e}")
                # Include sites we can't check
                filtered.append(site)
        
        logger.info(f"  Filtered to {len(filtered)} sites (prioritizing recent updates) out of {len(sites)}")
        return filtered
    
    def _deduplicate_sites(self, sites: List[Dict]) -> List[Dict]:
        """Remove duplicate sites, keeping the most recent or highest ranked"""
        seen = {}
        for site in sites:
            domain = site["domain"]
            current_site = seen.get(domain)
            if current_site is None:
                seen[domain] = site
                continue
            
            # Prefer site with last_modified
            if site.get('last_modified') and not current_site.get('last_modified'):
                seen[domain] = site
            elif not site.get('last_modified') and current_site.get('last_modified'):
                continue
            elif site.get('last_modified') and current_site.get('last_modified'):
                # Both have last_modified, keep the more recent
                if site['last_modified'] > current_site['last_modified']:
                    seen[domain] = site
                elif site['last_modified'] == current_site['last_modified']:
                    # Same date, keep lower rank
                    if site.get('rank', 999) < current_site.get('rank', 999):
                        seen[domain] = site
            else:
                # Neither has last_modified, keep lower rank
                if site.get('rank', 999) < current_site.get('rank', 999):
                    seen[domain] = site
        
        unique_sites = list(seen.values())
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        def sort_key(site):
            lm = site.get('last_modified')
            if lm is None:
                return (1, 0, site.get('rank', 999))  # No date goes last

            if lm.tzinfo is None:
                lm = lm.replace(tzinfo=timezone.utc)

            recent_flag = 0 if lm >= cutoff else 1
            return (recent_flag, -lm.timestamp(), site.get('rank', 999))

        unique_sites.sort(key=sort_key)
        return unique_sites
    
    def discover_by_related_sites(self, seed_urls: List[str], depth: int = 1) -> List[Dict]:
        """Discover websites by crawling related sites"""
        discovered = []
        visited = set()
        
        def crawl(url: str, current_depth: int):
            if current_depth > depth or url in visited:
                return
            
            visited.add(url)
            
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Extract all external links
                for link in soup.find_all('a', href=True):
                    href = self._normalize_attr(link.get('href'))
                    if href.startswith(('http://', 'https://')):
                        domain = self._extract_domain(href)
                        
                        if domain not in visited:
                            site_data = {
                                "keyword": "related_discovery",
                                "title": link.get_text().strip(),
                                "url": href,
                                "domain": domain,
                                "snippet": '',
                                "source": f"Related_to_{url}",
                                "rank": 999,
                                "last_modified": None
                            }
                            discovered.append(site_data)
                            
                            if current_depth < depth:
                                crawl(href, current_depth + 1)
                                
            except Exception as e:
                logger.error(f"Crawl error for {url}: {e}")
        
        for seed in seed_urls:
            crawl(seed, 0)
        
        return discovered
    
    def discover_using_sitemaps(self, website_url: str) -> List[Dict]:
        """Extract URLs from sitemap"""
        results = []
        sitemap_urls = [
            f"{website_url}/sitemap.xml",
            f"{website_url}/sitemap_index.xml",
            f"{website_url}/sitemap.php"
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                response = requests.get(sitemap_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'xml')
                    
                    # Parse XML sitemap
                    for url_tag in soup.find_all('url'):
                        loc = url_tag.find('loc')
                        if loc and loc.text:
                            results.append({
                                "keyword": "sitemap_discovery",
                                "title": "",
                                "url": loc.text,
                                "domain": self._extract_domain(loc.text),
                                "snippet": '',
                                "source": f"Sitemap_{website_url}",
                                "rank": 999,
                                "last_modified": None
                            })
                            
            except Exception as e:
                logger.error(f"Sitemap error for {sitemap_url}: {e}")
        
        return results
    
    def export_to_csv(self, filename: str = "discovered_sites.csv"):
        """Export discovered sites to CSV"""
        df = pd.DataFrame(self.discovered_sites)
        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(df)} sites to {filename}")