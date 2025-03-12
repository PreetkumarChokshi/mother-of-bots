from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class BotContext:
    intent: str
    complexity: str
    features: List[str]
    estimated_time: str
    requirements: Dict[str, any]

class ContextBuilder:
    def build(self, description: str) -> BotContext:
        """Build context from user description"""
        # Default values
        return BotContext(
            intent="general",
            complexity="Medium",
            features=[],
            estimated_time="1-2 hours",
            requirements={
                "platform": "web",
                "features": [],
                "integrations": []
            }
        ) 