from hanerma.interface.minimalist import quick_flow, create_agent

# 1. Define tools (simple Python functions)
def get_weather(city: str):
    return f"The weather in {city} is 72°F and sunny."

def get_news(topic: str):
    return f"Latest news on {topic}: HANERMA Apex released!"

# 2. Setup Agents in ONE line
weather_bot = create_agent("WeatherBot", role="Weather Expert", tools=[get_weather])
news_bot = create_agent("NewsBot", role="News Anchor", tools=[get_news])

# 3. Run the flow - Zero Friction
print("--- HANERMA Apex Demo ---")
response = quick_flow(
    prompt="Check the weather in NYC and find news about HANERMA.",
    agents=[weather_bot, news_bot]
)

print(f"\nRESULT:\n{response}")
print("\n--- Full Trace Saved to Transactional Bus (Recoverable in <2s) ---")
