
"""
Forces output formats (JSON strictness).
Uses Pydantic schemas or grammar masking.
"""

from typing import Dict, Any, Type, Optional
from pydantic import BaseModel
import json

class ConstraintInjector:
    """
    Ensures LLM output adheres to rigid structures.
    """
    
    def __init__(self, mode: str = "json"):
        self.mode = mode
        
    def generate_schema_prompt(self, model: Type[BaseModel]) -> str:
        """
        Produce a schema description for the LLM.
        """
        schema = model.model_json_schema()
        return f"\nYou must respond with JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        
    def validate(self, output: str, model: Type[BaseModel]) -> Optional[BaseModel]:
        """
        Parse and validate.
        """
        try:
            data = json.loads(output)
            return model(**data)
        except Exception:
            # Attempt repair?
            return None
