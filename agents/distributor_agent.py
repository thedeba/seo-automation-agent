import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import time
import random
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
from fake_useragent import UserAgent
import re

class ContentDistributor:
    """Agent for distributing content without APIs"""
    
    def __init__(self, sites_without_auth: List[Dict], sites_with_auth: List[Dict], posting_credentials: Optional[Dict] = None):
        self.ua = UserAgent()
        self.open_sites = sites_without_auth
        self.auth_sites = sites_with_auth
        self.session = requests.Session()
        self.posting_results = []
        
        # Common WordPress credentials (user would provide these)
        self.wp_credentials = {}
        
        # Success indicators in response
        self.success_indicators = [
            'thank you', 'success', 'submitted', 'published',
            'post created', 'article submitted', 'received',
            'successfully', 'redirect'
        ]
        
    def distribute_content(self, content_path: str, 
                          posting_credentials: Optional[Dict] = None) -> Dict:
        """Main distribution method"""
        logger.info(f"Starting content distribution for: {content_path}")
        
        if not Path(content_path).exists():
            raise FileNotFoundError(f"Content file not found: {content_path}")
        
        # Load credentials if provided
        if posting_credentials:
            self.wp_credentials = posting_credentials
        
        content_type = self._detect_content_type(content_path)
        content = self._read_content(content_path, content_type)
        
        results = {
            "content_path": content_path,
            "content_type": content_type,
            "distribution_time": datetime.now().isoformat(),
            "successful_posts": [],
            "failed_posts": [],
            "partial_success": []
        }
        
        # Try posting to all available sites
        all_sites = self.open_sites + self.auth_sites
        
        for site in all_sites:
            logger.debug(f"Attempting to post to: {site.get('domain', 'Unknown')}")
            
            attempt = self._attempt_posting(site, content, content_type, content_path)
            
            if attempt['success']:
                results['successful_posts'].append(attempt)
            elif attempt.get('partial'):
                results['partial_success'].append(attempt)
            else:
                results['failed_posts'].append(attempt)
            
            time.sleep(random.uniform(3, 7))  # Rate limiting
        
        results['summary'] = self._generate_summary(results)
        return results
    
    def _detect_content_type(self, file_path: str) -> str:
        """Detect content type"""
        ext = Path(file_path).suffix.lower()
        type_map = {
            '.pdf': 'pdf', '.txt': 'text', '.md': 'markdown',
            '.html': 'html', '.doc': 'document', '.docx': 'document'
        }
        return type_map.get(ext, 'text')
    
    def _read_content(self, file_path: str, content_type: str) -> Dict:
        """Read and parse content"""
        content = {}
        
        if content_type == 'text' or content_type == 'markdown':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            content['title'] = self._extract_title(text)
            content['body'] = text
            content['format'] = 'plain'
            
        elif content_type == 'pdf':
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                content['title'] = Path(file_path).stem
                content['body'] = text
                content['format'] = 'pdf'
            except ImportError:
                logger.warning("PyPDF2 not installed, can't read PDF")
                content['title'] = Path(file_path).stem
                content['body'] = 'PDF content'
                content['format'] = 'pdf'
        
        return content
    
    def _attempt_posting(self, site: Dict, content: Dict, content_type: str, content_path: str) -> Dict:
        """Attempt to post content to a site"""
        domain = site.get('domain', 'Unknown')
        result = {
            'site': domain,
            'url': site.get('url'),
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'method_used': None,
            'response_url': None
        }
        
        # Strategy 1: Try WordPress posting if CMS is WordPress
        if site.get('cms_detected') == 'wordpress':
            wp_result = self._post_to_wordpress(site, content)
            if wp_result['success']:
                result.update(wp_result)
                return result
        
        # Strategy 2: Try form submission
        for posting_form in site.get('posting_forms', []):
            if result['success']:
                break
            
            form_url = posting_form.get('url')
            if not form_url:
                continue
            
            logger.debug(f"  Trying form: {form_url}")
            
            # Get the form page
            try:
                response = self.session.get(
                    form_url,
                    headers={'User-Agent': self.ua.random},
                    timeout=15
                )
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find form to submit
                form = soup.find('form')
                if form:
                    submit_result = self._submit_form(
                        form, form_url, content, content_type, content_path
                    )
                    if submit_result['success']:
                        result.update(submit_result)
                        break
                
            except Exception as e:
                logger.error(f"  Form error: {str(e)}")
                continue
        
        # Strategy 3: Try contact form
        if not result['success'] and site.get('has_contact_form'):
            contact_result = self._try_contact_form(site, content, content_type, content_path)
            if contact_result['success']:
                result.update(contact_result)
        
        return result
    
    def _post_to_wordpress(self, site: Dict, content: Dict) -> Dict:
        """Attempt to post to WordPress site"""
        result = {'success': False, 'method_used': 'wordpress'}
        
        wp_url = site.get('domain', '')
        
        # Try XML-RPC
        xmlrpc_url = urljoin(wp_url, '/xmlrpc.php')
        
        # Try with credentials if available
        credentials = self.wp_credentials.get(site.get('domain'))
        if credentials:
            return self._wp_xmlrpc_post(xmlrpc_url, credentials, content)
        
        # Try REST API (some sites have it open)
        rest_url = urljoin(wp_url, '/wp-json/wp/v2/posts')
        try:
            response = self.session.get(rest_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"  WordPress REST API found at {rest_url}")
                # If API is open, we could try posting
                # But usually requires authentication
        except:
            pass
        
        return result
    
    def _wp_xmlrpc_post(self, xmlrpc_url: str, credentials: Dict, content: Dict) -> Dict:
        """Post to WordPress via XML-RPC"""
        result = {'success': False, 'method_used': 'xmlrpc'}
        
        import xmlrpc.client
        
        try:
            server = xmlrpc.client.ServerProxy(xmlrpc_url)
            
            post_data = {
                'post_title': content.get('title', 'Untitled'),
                'post_content': content.get('body', ''),
                'post_status': 'draft',  # Start as draft to be safe
                'post_type': 'post'
            }
            
            post_id = server.wp.newPost(
                0,
                credentials.get('username'),
                credentials.get('password'),
                post_data
            )
            
            if post_id:
                result['success'] = True
                result['post_id'] = post_id
                logger.info(f"  Posted to WordPress, ID: {post_id}")
                
        except Exception as e:
            logger.error(f"  WordPress XML-RPC error: {str(e)}")
        
        return result

    def _get_attr_value(self, tag: Tag, attr_name: str, default: str = '') -> str:
        value = tag.get(attr_name, default)
        if isinstance(value, list):
            return str(value[0]) if value else default
        return str(value or default)
    
    def _submit_form(self, form: Tag, form_url: str, 
                    content: Dict, content_type: str, content_path: str) -> Dict:
        """Submit content through a web form with intelligent file upload logic"""
        result = {'success': False, 'method_used': 'form_submission'}
        
        # Analyze form fields
        form_data = {}
        file_fields = []
        action = self._get_attr_value(form, 'action')
        method = self._get_attr_value(form, 'method', 'post').lower()
        submit_url = urljoin(form_url, action) if action else form_url
        
        # Collect all input fields
        for input_field in form.find_all('input'):
            name = self._get_attr_value(input_field, 'name')
            field_type = self._get_attr_value(input_field, 'type', 'text').lower()
            value = self._get_attr_value(input_field, 'value')
            
            if field_type == 'file':
                file_fields.append(name)
            elif field_type == 'hidden':
                form_data[name] = value
            elif field_type == 'text' and not value:
                # Auto-fill text fields
                if any(kw in name.lower() for kw in ['title', 'subject', 'name']):
                    form_data[name] = content.get('title', '')
                elif any(kw in name.lower() for kw in ['email', 'mail']):
                    form_data[name] = 'user@example.com'  # Placeholder
                elif any(kw in name.lower() for kw in ['url', 'website']):
                    form_data[name] = 'https://example.com'  # Placeholder
            elif field_type in ['checkbox', 'radio']:
                if self._get_attr_value(input_field, 'checked'):
                    form_data[name] = value
        
        # Collect textarea fields
        for textarea in form.find_all('textarea'):
            name = self._get_attr_value(textarea, 'name')
            if any(kw in name.lower() for kw in ['content', 'body', 'message', 'description', 'comment']):
                form_data[name] = content.get('body', '')
            elif any(kw in name.lower() for kw in ['title', 'subject']):
                form_data[name] = content.get('title', '')
        
        # Collect select fields
        for select in form.find_all('select'):
            name = self._get_attr_value(select, 'name')
            selected = select.find('option', selected=True)
            if selected:
                form_data[name] = self._get_attr_value(selected, 'value', selected.get_text())
            else:
                first_option = select.find('option')
                if first_option:
                    form_data[name] = self._get_attr_value(first_option, 'value', first_option.get_text())
        
        # Submit the form with intelligent file upload logic
        try:
            headers = {'User-Agent': self.ua.random}
            
            # Determine submission strategy
            if file_fields and content_type == 'pdf':
                # PDF available and form has file upload - prioritize PDF upload
                logger.debug(f"  Found {len(file_fields)} file upload fields, submitting PDF file")
                files = {}
                
                # Try to upload PDF to file fields
                for field_name in file_fields:
                    try:
                        files[field_name] = (Path(content_path).name, open(content_path, 'rb'), 'application/pdf')
                    except Exception as e:
                        logger.warning(f"  Could not prepare PDF for field {field_name}: {str(e)}")
                
                if files:
                    response = self.session.post(
                        submit_url,
                        data=form_data,
                        files=files,
                        headers=headers,
                        timeout=20,
                        allow_redirects=True
                    )
                    # Close file handles
                    for field_name, file_tuple in files.items():
                        if hasattr(file_tuple[1], 'close'):
                            file_tuple[1].close()
                else:
                    # Fallback to text-only submission
                    response = self.session.post(
                        submit_url,
                        data=form_data,
                        headers=headers,
                        timeout=20,
                        allow_redirects=True
                    )
                    
            elif file_fields and content_type in ['text', 'markdown']:
                # Text content but form has file upload - create text file
                logger.debug(f"  Found {len(file_fields)} file upload fields, creating text file for upload")
                files = {}
                
                # Create temporary text file
                temp_text_path = content_path.replace(Path(content_path).suffix, '_temp.txt')
                try:
                    with open(temp_text_path, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {content.get('title', '')}\n\n")
                        f.write(f"Content:\n{content.get('body', '')}")
                    
                    for field_name in file_fields:
                        files[field_name] = (Path(temp_text_path).name, open(temp_text_path, 'rb'), 'text/plain')
                    
                    response = self.session.post(
                        submit_url,
                        data=form_data,
                        files=files,
                        headers=headers,
                        timeout=20,
                        allow_redirects=True
                    )
                    
                    # Close file handles and cleanup
                    for field_name, file_tuple in files.items():
                        if hasattr(file_tuple[1], 'close'):
                            file_tuple[1].close()
                    Path(temp_text_path).unlink(missing_ok=True)
                    
                except Exception as e:
                    logger.warning(f"  Could not create text file for upload: {str(e)}")
                    # Fallback to text-only submission
                    response = self.session.post(
                        submit_url,
                        data=form_data,
                        headers=headers,
                        timeout=20,
                        allow_redirects=True
                    )
            else:
                # No file upload fields or not applicable - submit as text
                logger.debug(f"  No file upload fields available, submitting as text")
                if method == 'post':
                    response = self.session.post(
                        submit_url,
                        data=form_data,
                        headers=headers,
                        timeout=20,
                        allow_redirects=True
                    )
                else:
                    response = self.session.get(
                        submit_url,
                        params=form_data,
                        headers=headers,
                        timeout=20,
                        allow_redirects=True
                    )
            
            # Check for success
            if self._check_success(response):
                result['success'] = True
                result['response_url'] = response.url
                result['status_code'] = response.status_code
                logger.info(f"  Form submission successful!")
            
        except Exception as e:
            logger.error(f"  Form submission error: {str(e)}")
        
        return result
    
    def _try_contact_form(self, site: Dict, content: Dict, content_type: str, content_path: str) -> Dict:
        """Try submitting through contact form"""
        result = {'success': False, 'method_used': 'contact_form'}
        
        contact_pages = site.get('possible_posting_pages', [])
        
        for page in contact_pages:
            try:
                response = self.session.get(
                    page['url'],
                    headers={'User-Agent': self.ua.random},
                    timeout=15
                )
                
                soup = BeautifulSoup(response.text, 'lxml')
                form = soup.find('form')
                
                if form:
                    form_result = self._submit_form(
                        form, page['url'], content, content_type, content_path
                    )
                    if form_result['success']:
                        result.update(form_result)
                        break
                        
            except Exception as e:
                logger.error(f"  Contact form error: {str(e)}")
                continue
        
        return result
    
    def _check_success(self, response: requests.Response) -> bool:
        """Check if posting was successful based on response"""
        response_text = response.text.lower()[:1000]  # Check first 1000 chars
        
        # Check status code
        if response.status_code in [200, 201, 302, 303]:
            # Check for success indicators in response
            for indicator in self.success_indicators:
                if indicator in response_text:
                    return True
            
            # Check if redirected to a success page
            if response.history:
                for resp in response.history:
                    if resp.status_code in [302, 303]:
                        return True
        
        return False
    
    def _extract_title(self, text: str) -> str:
        """Extract title from text"""
        lines = text.strip().split('\n')
        
        # Try markdown title
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        
        # First non-empty line
        for line in lines:
            line = line.strip()
            if line and len(line) > 3:
                return line[:200]
        
        return "Untitled"
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate distribution summary"""
        successful = len(results['successful_posts'])
        failed = len(results['failed_posts'])
        partial = len(results['partial_success'])
        
        return {
            "total_attempted": successful + failed + partial,
            "successful": successful,
            "failed": failed,
            "partial_success": partial,
            "success_rate": f"{(successful / max(1, successful + failed + partial)) * 100:.1f}%"
        }
    
    def save_results(self, output_path: str = "data/output/posting_results.json"):
        """Save distribution results"""
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.posting_results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")