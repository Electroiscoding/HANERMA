
# How users can deploy custom personas

## Configuration Schema

A builder persona is defined by a `JSON` blob.

```json
{
  "name": "CryptoTrader",
  "system_prompt": "You are a pessimistic trader...",
  "tools": ["web_search", "binance_api"],
  "memory_type": "ephemeral",
  "model": "local-llama3"
}
```

## Loading via API

POST `/v1/agents/builder` with the JSON.

## Python Integration
Use `PersonaParser` to load safely:

```python
from hanerma.agents.builder_personas.persona_parser import PersonaParser

agent_cls = PersonaParser.create_dynamic_agent("TraderBot", config)
agent = agent_cls(tenant_id="user_123")
await agent.process("Should I buy BTC?")
```
