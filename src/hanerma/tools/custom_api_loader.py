
"""
Allows users to connect their own REST APIs.
Dynamically maps OpenAPI specs to usable tools.
"""

import httpx
from typing import Dict, Any, List
import json
# import requests
# from openapi_spec_validator import validate_spec

class CustomAPILoader:
    """
    Parses and executes external REST API calls dynamically.
    Enables zero-config integration for user-defined endpoints.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        
    async def load_from_url(self, spec_url: str):
        """Fetch and store API blueprint."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(spec_url, timeout=10.0)
                resp.raise_for_status()
                spec = resp.json()
                # Simple extraction: map paths to tool names
                for path, methods in spec.get("paths", {}).items():
                    for method, info in methods.items():
                        name = info.get("operationId") or f"{method}_{path.replace('/', '_')}"
                        self.endpoints[name] = {
                            "base_url": spec.get("servers", [{}])[0].get("url", ""),
                            "path": path,
                            "method": method.upper()
                        }
            except Exception as e:
                print(f"[CustomAPILoader] Failed to load spec: {e}")
        
    async def call_endpoint(self, tool_name: str, args: Dict[str, Any]):
        """Executes the mapped HTTP request."""
        spec = self.endpoints.get(tool_name)
        if not spec:
            return f"Error: Tool '{tool_name}' not found in loaded API specs."
            
        url = f"{spec['base_url']}{spec['path']}"
        async with httpx.AsyncClient() as client:
            try:
                # Dynamic request mapping based on method
                if spec['method'] == "GET":
                    resp = await client.get(url, params=args, timeout=15.0)
                else:
                    resp = await client.request(spec['method'], url, json=args, timeout=15.0)
                
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                return f"[API Error] Execution failed for {tool_name}: {str(e)}"
