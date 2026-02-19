
"""
Example 01: Simple Input -> Optimized Output
Demonstrates how the AutoPrompt Enhancer transforms a vague request.
"""
import asyncio
from hanerma.autoprompt.enhancer import AutoPromptEnhancer

async def main():
    enhancer = AutoPromptEnhancer()
    
    # User Input
    user_prompt = "Write me a function to sort a list in python"
    print(f"Original: {user_prompt}\n")
    
    # Enhanced Output
    enhanced_prompt = await enhancer.enhance(user_prompt)
    print(f"Enhanced:\n{enhanced_prompt}")

if __name__ == "__main__":
    asyncio.run(main())
