import requests
from typing import Dict, Any

class WebSearchTool:
    """
    Standardized connector for Google/Bing search APIs.
    Deep 3 Agents use this to fetch fresh data for context enrichment.
    """
    def __init__(self, api_key: str = "", cx: str = ""):
        self.api_key = api_key
        self.cse_id = cx
        self.endpoint = "https://www.googleapis.com/customsearch/v1"

    def execute(self, query: str) -> str:
        """
        Executes a real (or simulated) search request.
        """
        print(f"[WebSearch] Executing query: '{query}'")
        
        # If no API key configured, return dummy data to unblock users locally
        if not self.api_key:
            return f"[Simulated Output] Results for '{query}' found on StackOverflow, Docs..."
            
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query
        }
        
        try:
            resp = requests.get(self.endpoint, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            # Extract top 3 snippets only (keep context window clean)
            snippets = [item.get("snippet", "") for item in data.get("items", [])[:3]]
            return "\n".join(snippets)
            
        except Exception as e:
            return f"[Tool Error]: {str(e)}"
