"""
HANERMA — Model Agnosticism Final Diagnostics.

Proves the framework is completely decoupled from any single vendor
by sequentially testing Local (Ollama), HuggingFace, and OpenRouter.
"""

import os
from dotenv import load_dotenv

from hanerma.models.local_llm import LocalLLMAdapter
from hanerma.models.cloud_llm import OpenRouterAdapter, HuggingFaceAdapter

# Load the local .env file securely
load_dotenv()

TEST_PROMPT = "Explain the concept of Atomic Reasoning in one sentence."
SYSTEM_PROMPT = "You are a strict, concise AI architect."


def run_final_diagnostics():
    print("=" * 56)
    print("  HANERMA FINAL DIAGNOSTICS: MODEL AGNOSTICISM")
    print("=" * 56)

    # ---- 1. Test 100% Local (Ollama) ----
    try:
        print("\n--- Testing Local Offline (Ollama) ---")
        local_bot = LocalLLMAdapter(model_name="llama3")
        print(local_bot.generate(TEST_PROMPT, SYSTEM_PROMPT))
    except Exception as e:
        print(f"Local Test Failed: Is Ollama running?  Error: {e}")

    # ---- 2. Test Hugging Face Serverless ----
    try:
        print("\n--- Testing Hugging Face Serverless ---")
        hf_bot = HuggingFaceAdapter(
            model_name="meta-llama/Meta-Llama-3-8B-Instruct"
        )
        print(hf_bot.generate(TEST_PROMPT, SYSTEM_PROMPT))
    except Exception as e:
        print(f"Hugging Face Test Failed: Check your HF_TOKEN.  Error: {e}")

    # ---- 3. Test OpenRouter (Aggregator) ----
    try:
        print("\n--- Testing OpenRouter (Aggregator) ---")
        or_bot = OpenRouterAdapter(model_name="anthropic/claude-3-haiku")
        print(or_bot.generate(TEST_PROMPT, SYSTEM_PROMPT))
    except Exception as e:
        print(
            f"OpenRouter Test Failed: Check OPENROUTER_API_KEY.  Error: {e}"
        )

    print("\n" + "=" * 56)
    print("  DIAGNOSTICS COMPLETE")
    print("=" * 56)


if __name__ == "__main__":
    run_final_diagnostics()
