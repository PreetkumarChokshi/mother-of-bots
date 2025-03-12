from dataclasses import dataclass
from typing import Optional

@dataclass
class AIModel:
    """Represents an AI model with its capabilities"""
    id: str
    name: Optional[str] = None
    parameter_size: Optional[str] = None

@dataclass
class ModelOptions:
    """Options for model inference"""
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    seed: Optional[int] = None
    context_window_size: Optional[int] = None
    
    def validate(self):
        """Validate the options"""
        if self.temperature is not None and (self.temperature < 0 or self.temperature > 1):
            raise ValueError("Temperature must be between 0 and 1")
        if self.top_p is not None and (self.top_p < 0 or self.top_p > 1):
            raise ValueError("Top P must be between 0 and 1")
        if self.top_k is not None and self.top_k < 0:
            raise ValueError("Top K must be positive")
        if self.max_tokens is not None and self.max_tokens < 0:
            raise ValueError("Max tokens must be positive")
        if self.context_window_size is not None and self.context_window_size < 0:
            raise ValueError("Context window size must be positive") 