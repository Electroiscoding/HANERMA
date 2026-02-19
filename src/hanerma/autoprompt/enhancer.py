class AutoPromptEnhancer:
    """
    Upgrades raw user inputs into structured, enterprise-grade prompts.
    Forces JSON-strict formatting constraints for the Deep 1 layer to parse easily.
    """
    def __init__(self):
        self.base_constraint = (
            "You are operating within the HANERMA framework. "
            "You must output your reasoning in atomic steps. "
            "Do not hallucinate. Use external tools if unsure."
        )

    def enhance(self, raw_prompt: str) -> str:
        """Applies structural templates instantly."""
        # In a full build, this might use a sub-10ms local classifier to pick the best template
        enhanced = f"{self.base_constraint}\n\n[USER INTENT]\n{raw_prompt}\n\n[REQUIRED FORMAT]\n<atomic_reasoning>...</atomic_reasoning>\n<tool_request>...</tool_request>"
        return enhanced
