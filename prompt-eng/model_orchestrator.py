from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import re
import asyncio
import logging
from clients import bootstrap_client_and_model
from models import ModelOptions

logger = logging.getLogger(__name__)

@dataclass
class Context:
    """Represents a context with attributes and matching logic"""
    attributes: Dict[str, Any]

    def __contains__(self, other: 'Context') -> bool:
        """Implements context matching logic"""
        for key, value in other.attributes.items():
            if key not in self.attributes:
                return False
            if isinstance(value, str) and isinstance(self.attributes[key], str):
                # String pattern matching
                if not re.search(value, self.attributes[key], re.IGNORECASE):
                    return False
            elif self.attributes[key] != value:
                return False
        return True

@dataclass
class ModelAction:
    """Defines how to execute a model"""
    model_name: str
    parameters: Dict[str, Any]

    async def execute(self, prompt: str) -> str:
        """Execute the model with given prompt"""
        try:
            # This would integrate with your existing client system
            client, model = bootstrap_client_and_model(preferred_model=self.model_name)
            options = ModelOptions(**self.parameters)
            time_taken, response = client.chat_completion(prompt, model, options)
            return response
        except Exception as e:
            logger.error(f"Model execution error: {str(e)}")
            return f"Error: {str(e)}"

@dataclass
class ModelDescription:
    """Describes when and how to use a model"""
    context: Context
    action: ModelAction

class ModelBase:
    """Repository of model descriptions with context matching"""
    def __init__(self):
        self.models: List[ModelDescription] = []

    def add(self, model_desc: ModelDescription):
        self.models.append(model_desc)

    def __iadd__(self, model_desc: ModelDescription):
        self.add(model_desc)
        return self

    def find_matching_models(self, query_context: Context) -> List[ModelDescription]:
        """Find all models matching the query context"""
        return [model for model in self.models if query_context in model.context]

class ModelOrchestrator:
    """Orchestrates model selection and execution based on context"""
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.model_base = ModelBase()
        self.context = context or {}
        self.current_model = None  # Track the currently selected model

    async def process(self, ctx: Dict[str, Any]) -> str:
        """Process a context and execute appropriate model"""
        logger.debug(f"Processing context: {ctx}")
        
        # Check for user-selected model or chat command
        if "selected_model" in ctx:
            self.current_model = ModelAction(ctx["selected_model"], {"temperature": 0.7})
            return await self.current_model.execute(ctx.get("prompt", ""))
        elif ctx.get("command") == "!chat" and self.current_model:
            return await self.current_model.execute(ctx.get("prompt", ""))
        else:
            return "Error: No model selected. Please select a model first."

    # Remove or comment out unused methods
    # def _initialize_models(self):
    # def _build_query_context(self):
    # def _detect_task_type(self):
    # def _assess_complexity(self):
    # def _assess_creativity_needs(self):
    # def _execute_default_model(self):

# Remove or comment out these lines at the bottom of the file
# async def main():
#     orchestrator = ModelOrchestrator()
#     ctx = {
#         "workflow/id": "code_review",
#         "prompt": "Debug this Python function that calculates fibonacci numbers",
#         "workflow/input": "Original prompt here"
#     }
#     result = await orchestrator.process(ctx)

# asyncio.run(main())

