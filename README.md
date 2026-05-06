# 🚀 SEO Automation Agent (API-Free)

A powerful, API-free SEO automation tool that discovers relevant websites, extracts posting opportunities, and distributes content across multiple platforms without requiring any API keys.

## ✨ Key Features

- **🔍 Website Discovery**: Find relevant websites using multiple search engines (Google, DuckDuckGo, Bing)
- **📝 Content Extraction**: Automatically identify submission forms, guest posting opportunities, and content submission endpoints
- **🔐 Smart Classification**: Categorize sites by authentication requirements (login vs. open platforms)
- **📤 Content Distribution**: Post PDFs, text files, and other content formats to appropriate platforms
- **📊 Comprehensive Analytics**: Track success rates, failed attempts, and detailed performance metrics
- **⚙️ Highly Configurable**: Customize behavior through YAML configuration and command-line options
- **🌐 Multi-Engine Support**: Leverage multiple search engines for broader discovery
- **🛡️ Rate Limiting**: Built-in delays and retry mechanisms to avoid IP blocking

## 📋 Prerequisites

- **Python 3.8+** - Core runtime requirement
- **Modern Web Browser** - For Selenium-based automation (Chrome/Firefox recommended)
- **Git** - Optional, for cloning the repository

## 🚀 Quick Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd seo-automation-agent
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Browser Drivers (Optional but Recommended)

```bash
# Install Playwright browsers (automated browser control)
playwright install

# Or for Selenium, download ChromeDriver manually if needed
```

## 🎯 Usage Examples

### Basic Usage with Keywords

```bash
# Search for guest posting opportunities and distribute content
python main.py -k "guest post,write for us,submit article" -c content.txt

# Use keywords from file
python main.py -f keywords.txt -c article.pdf

# Discover from specific seed URLs
python main.py -u "https://example.com,https://techblog.com" -c content.txt
```

### Advanced Usage

```bash
# Use multiple search engines with custom settings
python main.py -k "tech blog" -c content.txt \
  --engines google,duckduckgo,bing \
  --max-sites 50 \
  --depth 2 \
  --delay 5.0 \
  --verbose

# Use credentials for authenticated sites
python main.py -k "guest post" -c content.txt \
  --credentials credentials.json
```

## 📁 Project Structure

```
seo-automation-agent/
├── agents/                 # Core automation agents
│   ├── discovery_agent.py  # Website discovery engine
│   ├── extractor_agent.py  # Posting link extraction
│   ├── classifier_agent.py # Authentication classification
│   └── distributor_agent.py# Content distribution
├── data/                   # Data storage
│   ├── input/             # Content and keywords
│   └── output/            # Results and logs
├── models/                # Data models and schemas
├── orchestrator/          # Workflow coordination
├── utils/                 # Utility functions
├── scripts/               # Helper scripts
├── tests/                 # Test suite
├── config.yaml           # Configuration file
├── main.py               # Entry point
└── requirements.txt       # Dependencies
```

## ⚙️ Configuration

### YAML Configuration (config.yaml)

```yaml
serpapi:
  max_results_per_keyword: 50
  country: "us"
  language: "en"

extraction:
  max_posting_links_per_site: 20
  patterns:
    posting:
      - "*/submit*"
      - "*/post*"
      - "*/publish*"
    article:
      - "*/blog/*"
      - "*/article/*"

distribution:
  rate_limit_delay: 2  # seconds between requests
  max_retries: 3
  timeout: 30

content:
  accepted_formats:
    - ".pdf"
    - ".txt"
    - ".md"
  max_file_size_mb: 10
```

### Environment Variables

Create a `.env` file for additional configuration:

```env
# Optional: User agent rotation settings
USER_AGENT_ROTATION=true

# Optional: Proxy settings
HTTP_PROXY=
HTTPS_PROXY=

# Optional: Custom headers
CUSTOM_HEADERS=
```

## 📊 Output & Results

The agent generates comprehensive output in the `data/output/` directory:

- `discovered_sites.csv` - List of discovered websites
- `classified_sites.json` - Sites categorized by authentication type
- `auth_sites.json` - Sites requiring credentials
- `logs/` - Detailed execution logs
- Summary report with success rates and statistics

### Example Output Summary

```
📊 RESULTS
════════════════════════════════════════════════════════════════════════
🎯 Sites Attempted: 45
✅ Successful: 23
⚠️  Partial Success: 8
❌ Failed: 14
📈 Success Rate: 51.1%
```

## 🔧 Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-k, --keywords` | Comma-separated keywords | - |
| `-f, --keywords-file` | File with keywords (one per line) | - |
| `-u, --urls` | Comma-separated seed URLs | - |
| `-c, --content` | Content file to distribute | **Required** |
| `--engines` | Search engines to use | `google,duckduckgo` |
| `--max-sites` | Max sites to process | `30` |
| `--depth` | Crawl depth for related sites | `1` |
| `--delay` | Delay between requests (seconds) | `3.0` |
| `--output` | Output directory | `data/output` |
| `--credentials` | JSON file with site credentials | - |
| `-v, --verbose` | Enable verbose logging | `False` |

## 🔐 Authentication Support

For sites requiring login, create a `credentials.json` file:

```json
{
  "https://example.com/login": {
    "username": "your_username",
    "password": "your_password",
    "login_field": "username",
    "password_field": "password"
  },
  "https://blogsite.com/wp-admin": {
    "username": "admin",
    "password": "secure_password"
  }
}
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_discovery_agent.py

# Run with coverage
python -m pytest tests/ --cov=agents
```

## 🚨 Important Notes

- **Rate Limiting**: Built-in delays prevent IP blocking (default: 3 seconds)
- **Browser Requirements**: Some sites may require JavaScript execution
- **Legal Compliance**: Ensure you have permission to post content on target sites
- **Respect robots.txt**: The agent respects website crawling policies
- **No API Keys**: This tool uses web scraping, not paid APIs

## 🛠️ Troubleshooting

### Common Issues

1. **Browser Driver Issues**
   ```bash
   # Reinstall Playwright browsers
   playwright install --force
   ```

2. **Permission Denied Errors**
   - Check file permissions on content files
   - Ensure output directory is writable

3. **Network Timeouts**
   ```bash
   # Increase timeout and delay
   python main.py -k "guest post" -c content.txt --delay 10 --timeout 60
   ```

4. **Memory Issues**
   - Reduce `--max-sites` parameter
   - Monitor system resources

## 📈 Performance Tips

- **Use Specific Keywords**: More targeted keywords yield better results
- **Adjust Delays**: Increase delays for stricter rate limiting
- **Monitor Logs**: Use `--verbose` flag for detailed debugging
- **Batch Processing**: Process multiple content files in separate runs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review the logs in `data/output/logs/`
- Open an issue on the repository

---

**⚡ Built with Python, BeautifulSoup, Selenium, and modern web automation tools**