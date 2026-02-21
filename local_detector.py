import asyncio
import httpx
import os

async def detect_local_providers():
    """Detects running local providers and sets defaults without requiring .env files."""
    ollama_running = False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                ollama_running = True
                print("[HANERMA] Ollama detected at localhost:11434. Setting as default provider.")
                os.environ["HANERMA_DEFAULT_PROVIDER"] = "ollama"
    except httpx.RequestError:
        print("[HANERMA] Ollama not accessible at localhost:11434.")
    
    if not ollama_running:
        print("[HANERMA] No local providers detected. Using cloud defaults.")
        os.environ["HANERMA_DEFAULT_PROVIDER"] = "cloud"

if __name__ == "__main__":
    asyncio.run(detect_local_providers())
