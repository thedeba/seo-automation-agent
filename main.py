#!/usr/bin/env python3
"""
API-Free SEO Automation Agent
No API keys required - Uses direct web scraping and free search methods
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
import json

from orchestrator.workflow_orchestrator import SEOAutomationAgent
from utils.validators import validate_keywords, validate_file_path

# Setup clean logging format
logger.remove()
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="API-Free SEO Automation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect default files (keywords.txt + content_to_post.txt/pdf)
  python main.py
  
  # Basic usage with keywords
  python main.py -k "guest post,write for us,submit article" -c content.txt
  
  # Use keywords file
  python main.py -f keywords.txt -c article.pdf
  
  # Discover from specific URLs
  python main.py -u "https://example.com" -c content.txt
  
  # Multiple search engines
  python main.py -k "tech blog" -c content.txt --engines google,duckduckgo,bing
        """
    )
    
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('-k', '--keywords', type=str,
                            help='Comma-separated keywords')
    input_group.add_argument('-f', '--keywords-file', type=str,
                            help='File with keywords (one per line)')
    input_group.add_argument('-u', '--urls', type=str,
                            help='Comma-separated seed URLs for discovery')
    
    parser.add_argument('-c', '--content', type=str,
                       help='Content file to distribute')
    parser.add_argument('--engines', type=str, default='duckduckgo',
                       help='Search engines to use (default: duckduckgo)')
    parser.add_argument('--max-sites', type=int, default=50,
                       help='Max sites to process (default: 30)')
    parser.add_argument('--depth', type=int, default=1,
                       help='Crawl depth for related sites (default: 1)')
    parser.add_argument('--delay', type=float, default=3.0,
                       help='Delay between requests (default: 3.0)')
    parser.add_argument('--output', type=str, default='data/output',
                       help='Output directory (default: data/output)')
    parser.add_argument('--credentials', type=str,
                       help='JSON file with site credentials')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    return parser.parse_args()

def load_credentials(cred_file: str) -> dict:
    """Load posting credentials from JSON file"""
    if cred_file and os.path.exists(cred_file):
        with open(cred_file, 'r') as f:
            return json.load(f)
    return {}

def main():
    """Main execution"""
    print("""
    ╔══════════════════════════════════════╗
    ║   SEO Automation Agent (API-Free)    ║
    ║   No API Keys Required!              ║
    ╚══════════════════════════════════════╝
    """)
    
    args = parse_arguments()
    
    # Auto-detect default files if no arguments provided
    if not args.content and not args.keywords and not args.keywords_file and not args.urls:
        logger.info("No arguments provided, using default files...")
        
        # Default content file preference: .txt > .pdf
        default_content_files = [
            "data/input/content_to_post.txt",
            "data/input/content_to_post.pdf"
        ]
        
        for content_file in default_content_files:
            if validate_file_path(content_file):
                args.content = content_file
                logger.info(f"Auto-detected content file: {content_file}")
                break
        
        # Default keywords file
        default_keywords_file = "data/input/keywords.txt"
        if validate_file_path(default_keywords_file):
            args.keywords_file = default_keywords_file
            logger.info(f"Auto-detected keywords file: {default_keywords_file}")
    
    # Auto-detect content if keywords provided but no content
    if not args.content and (args.keywords or args.keywords_file or args.urls):
        default_content_files = [
            "data/input/content_to_post.txt",
            "data/input/content_to_post.pdf"
        ]
        
        for content_file in default_content_files:
            if validate_file_path(content_file):
                args.content = content_file
                logger.info(f"Auto-detected content file: {content_file}")
                break
        
        if not args.content:
            logger.error("No content file found in data/input/ directory")
            sys.exit(1)
    
    # Validate files
    if args.content and not validate_file_path(args.content):
        logger.error(f"Content file not found: {args.content}")
        sys.exit(1)
    
    if args.keywords_file and not validate_file_path(args.keywords_file):
        logger.error(f"Keywords file not found: {args.keywords_file}")
        sys.exit(1)
    
    # Setup logging
    if args.verbose:
        logger.remove()
        logger.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="DEBUG"
        )
    
    try:
        # Get search inputs
        keywords = []
        seed_urls = []
        
        if args.keywords:
            keywords = validate_keywords(args.keywords)
            logger.info(f"Using {len(keywords)} keywords")
        
        elif args.keywords_file:
            with open(args.keywords_file, 'r') as f:
                keywords = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(keywords)} keywords from file")
        
        elif args.urls:
            seed_urls = [u.strip() for u in args.urls.split(',')]
            logger.info(f"Using {len(seed_urls)} seed URLs")
        
        # Parse search engines
        search_engines = [e.strip() for e in args.engines.split(',')]
        
        # Load credentials if provided
        credentials = load_credentials(args.credentials)
        if credentials:
            logger.info(f"Loaded credentials for {len(credentials)} sites")
        
        # Initialize agent
        agent = SEOAutomationAgent()
        
        # Configure
        agent.config.update({
            'extraction': {
                'max_sites_to_process': args.max_sites,
                'crawl_depth': args.depth
            },
            'distribution': {
                'rate_limit_delay': args.delay
            },
            'output': {
                'directory': args.output
            },
            'search_engines': search_engines
        })
        
        # Run workflow
        results = {}
        if keywords:
            results = agent.run(keywords, args.content, credentials)
        elif seed_urls:
            results = agent.run_from_urls(seed_urls, args.content, credentials)
        else:
            logger.error("No keywords or seed URLs were provided to run the workflow.")
            sys.exit(1)
        
        # Print results
        print("\n" + "="*60)
        print("📊 RESULTS")
        print("="*60)
        
        if results and results.get('summary'):
            s = results['summary']
            print(f"🎯 Sites Attempted: {s.get('total_attempted', 0)}")
            print(f"✅ Successful: {s.get('successful', 0)}")
            print(f"⚠️  Partial Success: {s.get('partial_success', 0)}")
            print(f"❌ Failed: {s.get('failed', 0)}")
            print(f"📈 Success Rate: {s.get('success_rate', '0%')}")
        
        print(f"\n📁 Full results: {args.output}/")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()