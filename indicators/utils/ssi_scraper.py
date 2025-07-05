"""Web scraping module for investing.com articles with robust content extraction."""

import sys
import random
import time
from datetime import datetime
from typing import List, Dict, Any

import requests
import trafilatura


class InvestingScraper:
    """Robust web scraper for investing.com articles with content extraction."""
    
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self._setup_session()
    
    def _setup_session(self):
        """Initialize session with investing.com homepage visit for cookies."""
        try:
            print("   🔗 Visiting investing.com homepage for cookies...", file=sys.stderr)
            initial_headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br, identity',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            self.session.get('https://www.investing.com/', headers=initial_headers, timeout=15)
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            print(f"   ⚠️  Homepage visit failed: {e}", file=sys.stderr)
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate realistic browser headers."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, identity',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.investing.com/',
            'DNT': '1',
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"macOS"',
        }
    
    def _decode_content(self, response: requests.Response) -> str:
        """Handle different content encodings properly."""
        content_encoding = response.headers.get('content-encoding', '').lower()
        
        if content_encoding == 'gzip':
            print(f"   🔄 Detected gzip encoding, decompressing...", file=sys.stderr)
            try:
                import gzip
                return gzip.decompress(response.content).decode('utf-8')
            except Exception as e:
                print(f"   ❌ Gzip decompression failed: {e}", file=sys.stderr)
                return response.text
                
        elif content_encoding == 'deflate':
            print(f"   🔄 Detected deflate encoding, using requests default handling", file=sys.stderr)
            return response.text
            
        elif content_encoding == 'br':
            print(f"   🔄 Detected brotli encoding, using requests auto-decompression", file=sys.stderr)
            # Requests automatically handles brotli decompression, so just use .text
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
        else:
            # Standard handling
            response.encoding = response.apparent_encoding or 'utf-8'
            downloaded = response.text
            
            # Check if content still looks like binary data
            if len(downloaded) > 100:
                sample = downloaded[:100]
                printable_chars = sum(1 for c in sample if c.isprintable() or c.isspace())
                if printable_chars < len(sample) * 0.8:  # Less than 80% printable
                    print(f"   ⚠️  Content appears binary, trying UTF-8 decode", file=sys.stderr)
                    try:
                        return response.content.decode('utf-8', errors='ignore')
                    except:
                        print(f"   ❌ Failed to decode content properly", file=sys.stderr)
                        return downloaded
            return downloaded
    
    def _extract_with_trafilatura(self, html_content: str) -> str:
        """Extract content using trafilatura."""
        full_text = trafilatura.extract(
            html_content, 
            include_comments=False, 
            include_tables=True,
            include_formatting=True, 
            favor_precision=False
        )
        
        if full_text and len(full_text.strip()) >= 100:
            print(f"   ✓ Trafilatura extracted {len(full_text)} characters", file=sys.stderr)
            return full_text
        else:
            if full_text:
                print(f"   ⚠️  Trafilatura extracted only {len(full_text)} chars", file=sys.stderr)
            else:
                print(f"   ⚠️  Trafilatura failed to extract content", file=sys.stderr)
            return None
    
    
    def _download_page(self, url: str, max_retries: int = 2) -> str:
        """Download a single page with retries."""
        for attempt in range(max_retries):
            try:
                headers = self._get_headers()
                response = self.session.get(url, headers=headers, timeout=30, allow_redirects=True)
                
                if response.status_code == 200:
                    downloaded = self._decode_content(response)
                    print(f"   📊 Got {len(downloaded)} bytes, status {response.status_code}", file=sys.stderr)
                    return downloaded
                else:
                    print(f"   ⚠️  Attempt {attempt + 1}: HTTP {response.status_code}", file=sys.stderr)
                
                if attempt < max_retries - 1:
                    wait_time = random.uniform(2, 4)
                    print(f"   ⏱️  Waiting {wait_time:.1f}s before retry...", file=sys.stderr)
                    time.sleep(wait_time)
                    
            except Exception as fetch_exc:
                print(f"   🔄 Attempt {attempt + 1} error: {fetch_exc}", file=sys.stderr)
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
        
        return None
    
    def scrape_articles(self, search_results: List[Dict[str, Any]], max_articles: int = 10) -> List[Dict[str, Any]]:
        """Scrape full article content from search results."""
        scraped_articles = []
        successful_scrapes = 0
        failed_scrapes = 0
        
        print("📄 Using requests fallback with enhanced headers...", file=sys.stderr)
        
        for i, result in enumerate(search_results[:max_articles], 1):
            url = result.get("link", "")
            title = result.get("title", "")
            date_info = result.get("date", "")
            
            if not url:
                print(f"   ⚠️  Article {i}: No URL, skipping", file=sys.stderr)
                failed_scrapes += 1
                continue
            
            try:
                print(f"   📖 Article {i}: {title[:50]}...", file=sys.stderr)
                
                # Random delay before each request (reduced for speed)
                delay = random.uniform(1, 3)
                print(f"   ⏱️  Waiting {delay:.1f}s...", file=sys.stderr)
                time.sleep(delay)
                
                # Download the page
                downloaded = self._download_page(url)
                
                if not downloaded or len(downloaded) < 1000:
                    print(f"   ⚠️  Failed to download content: {len(downloaded) if downloaded else 0} bytes", file=sys.stderr)
                    failed_scrapes += 1
                    continue
                
                # Save HTML debug for first article to logs folder
                if i == 1:
                    import os
                    log_dir = "logs"
                    os.makedirs(log_dir, exist_ok=True)
                    debug_snippet = downloaded[:5000] if downloaded else ""
                    debug_file = f"{log_dir}/html_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(debug_file, 'w') as f:
                        f.write(f"URL: {url}\n")
                        f.write(f"HTML Length: {len(downloaded)}\n")
                        f.write(f"First 5000 chars:\n{debug_snippet}")
                    print(f"   🐛 HTML debug saved to {debug_file}", file=sys.stderr)
                
                # Extract content using trafilatura
                full_text = self._extract_with_trafilatura(downloaded)
                
                if full_text and len(full_text.strip()) > 100:
                    scraped_articles.append({
                        "title": title,
                        "date": date_info,
                        "link": url,
                        "full_text": full_text,
                        "text_length": len(full_text),
                        "extraction_success": True
                    })
                    successful_scrapes += 1
                else:
                    print(f"   ⚠️  Content extraction failed", file=sys.stderr)
                    failed_scrapes += 1
                    
            except Exception as exc:
                print(f"   ⚠️  Scraping error: {exc}", file=sys.stderr)
                failed_scrapes += 1
        
        print(f"📊 Scraping complete: {successful_scrapes} successful, {failed_scrapes} failed", file=sys.stderr)
        return scraped_articles