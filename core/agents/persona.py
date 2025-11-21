"""
Dynamic Persona Engine
Manages agent personas and role switching.
"""
from typing import Dict, Optional
from pydantic import BaseModel

class Persona(BaseModel):
    name: str
    description: str
    system_prompt: str

# Pre-defined personas
PERSONAS = {
    "default": Persona(
        name="Default Agent",
        description="A general purpose AI assistant.",
        system_prompt="You are a helpful AI assistant."
    ),
    "coder": Persona(
        name="Senior Software Engineer",
        description="Expert in Python, Architecture, and Debugging.",
        system_prompt="You are a Senior Software Engineer. You write clean, efficient, and well-documented code. You always verify your code with tests."
    ),
    "researcher": Persona(
        name="Research Analyst",
        description="Expert in finding and summarizing information.",
        system_prompt="You are a Research Analyst. You are skeptical, thorough, and cite your sources. You use web search to find the latest information."
    ),
    "product_manager": Persona(
        name="Product Manager",
        description="Focuses on user value, requirements, and prioritization.",
        system_prompt="You are a Product Manager. You focus on the 'Why' and 'What'. You prioritize features based on user value and business impact."
    )
}

class PersonaEngine:
    def __init__(self):
        self.current_persona = PERSONAS["default"]
        
    def get_persona(self, name: str) -> Optional[Persona]:
        return PERSONAS.get(name)
        
    def switch_persona(self, name: str) -> bool:
        """Switches the current persona"""
        if name in PERSONAS:
            self.current_persona = PERSONAS[name]
            return True
        return False
        
    def get_system_prompt(self) -> str:
        """Returns the current system prompt"""
        return self.current_persona.system_prompt

    def register_persona(self, name: str, description: str, system_prompt: str):
        """Dynamically registers a new persona"""
        PERSONAS[name] = Persona(
            name=name,
            description=description,
            system_prompt=system_prompt
        )
