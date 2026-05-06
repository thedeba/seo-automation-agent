import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Set, Optional
import time
import random
from loguru import logger
from fake_useragent import UserAgent

class PostingLinkExtractor:
    """Agent for extracting posting links from websites"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.posting_patterns = [
            r'.*/(submit|post|create|new|add|publish|write|contribute)(-.*)?(/.*)?$',
            r'.*/(guest-post|guest-post-submission|write-for-us)(/.*)?$',
            r'.*/(submission|submit-post|submit-article|submit-content)(/.*)?$',
            r'.*/(contact|contact-us|about|contribute)(/.*)?$'
        ]
        
        self.article_patterns = [
            r'.*/(blog|article|post|news|story|press)/.*',
            r'.*/20\d{2}/\d{2}/.*',
            r'.*/\d{4}/\d{2}/\d{2}/.*'
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
    def find_posting_links(self, website_url: str, timeout: int = 10) -> Dict:
        """Extract all posting-related URLs from a website"""
        logger.info(f"Extracting posting links from: {website_url}")
        
        try:
            html_content = self._fetch_page(website_url, timeout)
            if not html_content:
                return self._empty_result(website_url, "Failed to fetch page")
                
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract all links
            all_links = self._extract_all_links(soup, website_url)
            
            # Classify links
            posting_links = self._classify_posting_links(all_links, soup)
            article_links = self._classify_article_links(all_links)
            form_links = self._extract_forms(soup, website_url)
            
            # Check authentication requirements
            auth_info = self._check_auth_required(soup, html_content)
            
            # Detect CMS
            cms = self._detect_cms(soup, html_content)
            
            result = {
                "domain": self._extract_domain(website_url),
                "url": website_url,
                "posting_forms": posting_links + form_links,
                "article_urls": article_links[:20],
                "all_links_count": len(all_links),
                "login_required": auth_info,
                "cms_detected": cms,
                "has_contact_form": len(form_links) > 0,
                "possible_posting_pages": self._find_possible_posting_pages(soup, website_url)
            }
            
            logger.info(f"Found {len(posting_links)} posting links on {website_url}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing {website_url}: {str(e)}")
            return self._empty_result(website_url, str(e))
    
    def _fetch_page(self, url: str, timeout: int) -> Optional[str]:
        """Fetch webpage content with retry"""
        headers = {'User-Agent': self.ua.random}
        
        for attempt in range(3):
            try:
                response = self.session.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == 2:
                    logger.error(f"Failed to fetch {url}: {e}")
                    return None
                time.sleep(random.uniform(1, 3))
        
        return None
    
    def _extract_all_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract all links from the page"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            
            # Skip empty, javascript, and mailto links
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
            
            full_url = urljoin(base_url, href)
            text = link.get_text().strip()
            
            links.append({
                'url': full_url,
                'text': text,
                'internal': self._is_internal_url(full_url, base_url),
                'title_attr': link.get('title', ''),
                'class': ' '.join(link.get('class', []))
            })
        
        return links
    
    def _classify_posting_links(self, links: List[Dict], soup: BeautifulSoup) -> List[Dict]:
        """Classify which links are posting/submission links"""
        posting_keywords = [
            'submit', 'post', 'publish', 'write', 'contribute',
            'guest post', 'write for us', 'submit article', 'create',
            'add new', 'upload', 'share', 'send', 'contact'
        ]
        
        posting_links = []
        
        for link in links:
            url_lower = link['url'].lower()
            text_lower = link['text'].lower()
            title_lower = link['title_attr'].lower()
            class_lower = link['class'].lower()
            
            combined_text = f"{text_lower} {title_lower} {class_lower}"
            
            # Check URL patterns
            url_match = any(re.match(pattern, link['url'], re.IGNORECASE) 
                          for pattern in self.posting_patterns)
            
            # Check text keywords
            text_match = any(keyword in combined_text 
                           for keyword in posting_keywords)
            
            if url_match or text_match:
                link['posting_probability'] = 'high' if (url_match and text_match) else 'medium'
                posting_links.append(link)
        
        # Also look for posting-related sections
        for section in soup.find_all(['div', 'section', 'nav']):
            section_text = section.get_text().lower()
            if any(keyword in section_text for keyword in ['submit', 'contribute', 'write for us']):
                for link in section.find_all('a', href=True):
                    full_url = urljoin(link.get('href', ''), '')
                    if full_url not in [pl['url'] for pl in posting_links]:
                        posting_links.append({
                            'url': full_url,
                            'text': link.get_text().strip(),
                            'posting_probability': 'low'
                        })
        
        return posting_links
    
    def _classify_article_links(self, links: List[Dict]) -> List[str]:
        """Identify article/blog post URLs"""
        article_urls = []
        
        for link in links:
            url = link['url']
            
            for pattern in self.article_patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    article_urls.append(url)
                    break
        
        return list(set(article_urls))
    
    def _extract_forms(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract all forms from the page"""
        forms = []
        
        for i, form in enumerate(soup.find_all('form')):
            form_info = {
                'url': urljoin(base_url, form.get('action', '')),
                'method': form.get('method', 'get').upper(),
                'type': 'form',
                'form_id': form.get('id', f'form_{i}'),
                'form_class': ' '.join(form.get('class', [])),
                'has_file_upload': False,
                'fields': []
            }
            
            # Analyze form fields
            for input_field in form.find_all('input'):
                field_type = input_field.get('type', 'text').lower()
                field_name = input_field.get('name', '')
                
                if field_type == 'file':
                    form_info['has_file_upload'] = True
                
                form_info['fields'].append({
                    'name': field_name,
                    'type': field_type,
                    'placeholder': input_field.get('placeholder', '')
                })
            
            for textarea in form.find_all('textarea'):
                form_info['fields'].append({
                    'name': textarea.get('name', ''),
                    'type': 'textarea',
                    'placeholder': textarea.get('placeholder', '')
                })
            
            forms.append(form_info)
        
        return forms
    
    def _check_auth_required(self, soup: BeautifulSoup, html: str) -> Dict:
        """Comprehensive authentication check"""
        html_lower = html.lower()
        
        auth_info = {
            'has_login_form': False,
            'has_register_form': False,
            'has_login_link': False,
            'has_register_link': False,
            'has_wp_admin': 'wp-admin' in html_lower or 'wp-login' in html_lower,
            'indicators': []
        }
        
        # Check forms for login/register
        for form in soup.find_all('form'):
            form_text = str(form).lower()
            form_id = form.get('id', '').lower()
            form_class = ' '.join(form.get('class', [])).lower()
            
            if any(word in form_text for word in ['password', 'username', 'user_login']):
                if 'register' in form_text or 'signup' in form_text or 'sign up' in form_text:
                    auth_info['has_register_form'] = True
                    auth_info['indicators'].append('register_form')
                else:
                    auth_info['has_login_form'] = True
                    auth_info['indicators'].append('login_form')
        
        # Check links
        for link in soup.find_all('a', href=True):
            text = link.get_text().lower()
            href = link['href'].lower()
            
            if any(word in text for word in ['login', 'sign in', 'log in']):
                auth_info['has_login_link'] = True
                auth_info['indicators'].append('login_link')
            
            if any(word in text for word in ['register', 'sign up', 'create account']):
                auth_info['has_register_link'] = True
                auth_info['indicators'].append('register_link')
        
        return auth_info
    
    def _detect_cms(self, soup: BeautifulSoup, html: str) -> str:
        """Detect content management system"""
        html_lower = html.lower()
        
        # WordPress
        if 'wp-content' in html_lower or 'wp-includes' in html_lower:
            return 'wordpress'
        if soup.find('meta', {'name': 'generator', 'content': re.compile(r'WordPress', re.I)}):
            return 'wordpress'
        
        # Drupal
        if 'drupal' in html_lower:
            return 'drupal'
        
        # Joomla
        if 'joomla' in html_lower:
            return 'joomla'
        
        # Ghost
        if 'ghost' in html_lower:
            return 'ghost'
        
        # Medium
        if 'medium.com' in html_lower:
            return 'medium'
        
        # Blogger
        if 'blogger' in html_lower:
            return 'blogger'
        
        return 'unknown'
    
    def _find_possible_posting_pages(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Find pages that might accept posts based on common patterns"""
        possible_pages = []
        
        # Common page slugs for posting
        posting_slugs = [
            '/write-for-us', '/guest-post', '/contribute', '/submit-article',
            '/submit-post', '/submit-guest-post', '/become-contributor',
            '/write', '/publish', '/create-post', '/new-post'
        ]
        
        # Check existing links
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            for slug in posting_slugs:
                if slug in href:
                    possible_pages.append({
                        'url': urljoin(base_url, link['href']),
                        'text': link.get_text().strip(),
                        'slug': slug
                    })
        
        # Try common WordPress posting URLs
        if self._detect_cms(soup, '') == 'wordpress':
            wp_posting_url = urljoin(base_url, '/wp-admin/post-new.php')
            possible_pages.append({
                'url': wp_posting_url,
                'text': 'WordPress New Post',
                'slug': '/wp-admin/post-new.php'
            })
        
        return possible_pages
    
    def _is_internal_url(self, url: str, base_url: str) -> bool:
        """Check if URL is internal to the website"""
        try:
            url_domain = urlparse(url).netloc
            base_domain = urlparse(base_url).netloc
            return url_domain == base_domain or url_domain == ''
        except:
            return False
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _empty_result(self, url: str, error: str) -> Dict:
        """Return empty result structure"""
        return {
            "domain": self._extract_domain(url),
            "url": url,
            "posting_forms": [],
            "article_urls": [],
            "all_links_count": 0,
            "login_required": {},
            "cms_detected": "unknown",
            "has_contact_form": False,
            "possible_posting_pages": [],
            "error": error
        }
    
    def bulk_extract(self, urls: List[str]) -> List[Dict]:
        """Extract posting links from multiple URLs"""
        results = []
        for url in urls:
            result = self.find_posting_links(url)
            results.append(result)
            time.sleep(random.uniform(1, 3))  # Rate limiting
        return results