
"""
Safe and Advanced Web Search for HANERMA.
Utilizes the ddgs library for robust search retrieval.
"""
from duckduckgo_search import DDGS
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any

class SafeWebSearch:
    """
    Production-grade web search and scraping engine.
    Uses DDGS for search and httpx with smart extraction for scraping.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Executes a robust search using the ddgs library.
        """
        results = []
        print(f"[SafeWebSearch] Requesting DDGS: {query}")
        try:
            # DDGS uses primp/httpx internally and is very resilient.
            with DDGS() as ddgs:
                ddgs_results = list(ddgs.text(query, max_results=limit))
                for r in ddgs_results:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "No snippet available.")
                    })
        except Exception as e:
            print(f"[SafeWebSearch Error] Search failed: {e}")
        
        return results

    async def scrape_page(self, url: str) -> str:
        """
        Extracts clean text from a target URL.
        """
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                resp = await client.get(url, timeout=10.0)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    # Strip script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text = soup.get_text(separator=' ')
                    # Clean up whitespace
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    return clean_text[:5000] # Limit context size
                return f"Error: Failed to load page (Status {resp.status_code})"
            except Exception as e:
                return f"Scrape Error: {str(e)}"
