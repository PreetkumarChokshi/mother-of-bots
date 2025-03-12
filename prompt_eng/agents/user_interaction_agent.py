import asyncio
import json
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from clients import bootstrap_client_and_model

@dataclass
class BotIntent:
    primary_intent: str
    model_requirements: str = ""
    functionality: List[str] = None
    integrations: List[str] = None
    
    def __post_init__(self):
        self.functionality = self.functionality or []
        self.integrations = self.integrations or []

@dataclass
class APIRecommendation:
    name: str
    description: str
    complexity: str  # Low, Medium, High
    documentation_url: str = ""
    alternatives: List[str] = None
    
    def __post_init__(self):
        self.alternatives = self.alternatives or []

@dataclass
class ConversationContext:
    bot_type: str = ""
    features: list = None
    data_source: str = ""
    ui_preferences: Dict = None
    conversation_history: list = None
    intent: Optional[BotIntent] = None
    api_recommendations: List[APIRecommendation] = None
    
    def __post_init__(self):
        self.features = self.features or []
        self.ui_preferences = self.ui_preferences or {}
        self.conversation_history = self.conversation_history or []
        self.api_recommendations = self.api_recommendations or []
    
    def to_json(self) -> Dict:
        return {
            "bot_type": self.bot_type,
            "features": self.features,
            "data_source": self.data_source,
            "ui_preferences": self.ui_preferences,
            "intent": {
                "primary": self.intent.primary_intent if self.intent else "",
                "model": self.intent.model_requirements if self.intent else "",
                "functionality": self.intent.functionality if self.intent else [],
                "integrations": self.intent.integrations if self.intent else []
            },
            "api_recommendations": [
                {
                    "name": api.name,
                    "complexity": api.complexity,
                    "alternatives": api.alternatives
                } for api in self.api_recommendations
            ]
        }

class UserInteractionAgent:
    def __init__(self):
        self.context = ConversationContext()
        self._clarifying_questions = {
            "bot_type": "What type of bot would you like to create?",
            "features": "What features should your bot have?",
            "data_source": "What data source should the bot use?",
            "ui_preferences": "Do you have any specific UI preferences?"
        }
        # Initialize client and model once during initialization
        self.client, self.model = bootstrap_client_and_model(
            # Prefer models optimized for conversation/analysis
            preferred_model="qwen2"  # Will fall back to available model if not found
        )
    
    async def get_user_input(self) -> str:
        """Main entry point for user interaction"""
        print("Please describe the bot you want to create:")
        loop = asyncio.get_event_loop()
        raw_input = await loop.run_in_executor(None, input)
        
        # Use the initialized client and model
        # Extract intent and entities
        intent = await self._recognize_intent(raw_input)
        self.context.intent = intent
        
        # Start multi-turn conversation to refine requirements
        refined_context = await self._conduct_conversation(raw_input)
        
        # Analyze API requirements
        await self._analyze_apis(refined_context)
        
        # Convert to structured format
        structured_output = await self._structure_requirements(refined_context)
        
        return json.dumps(structured_output, indent=2)

    async def _recognize_intent(self, user_input: str) -> BotIntent:
        """Extract intents and entities using configured model"""
        system_prompt = """You are an expert in intent recognition and NER. Analyze the user's request 
        and extract the primary intent, required AI models, functionalities, and integrations. 
        Respond in JSON format."""
        
        self.client.set_system_prompt(system_prompt)
        
        _, intent_json = self.client.chat_completion(user_input, self.model, None)
        
        try:
            intent_data = json.loads(intent_json)
            return BotIntent(
                primary_intent=intent_data.get("intent", ""),
                model_requirements=intent_data.get("model", ""),
                functionality=intent_data.get("functionality", []),
                integrations=intent_data.get("integration", [])
            )
        except json.JSONDecodeError:
            return BotIntent(primary_intent="Create Bot")

    async def _analyze_apis(self, context: ConversationContext):
        """Analyze and recommend APIs based on bot requirements"""
        system_prompt = """You are an API recommendation expert. Based on the bot requirements,
        suggest appropriate APIs and assess their integration complexity. Include alternatives
        where applicable. Respond in JSON format."""
        
        self.client.set_system_prompt(system_prompt)
        
        analysis_input = {
            "bot_type": context.bot_type,
            "features": context.features,
            "intent": context.intent.to_json() if context.intent else {}
        }
        
        _, api_json = self.client.chat_completion(
            json.dumps(analysis_input), 
            self.model, 
            None
        )
        
        try:
            api_data = json.loads(api_json)
            for api in api_data.get("recommended_apis", []):
                recommendation = APIRecommendation(
                    name=api.get("name", ""),
                    description=api.get("description", ""),
                    complexity=api.get("complexity", "Medium"),
                    alternatives=api.get("alternatives", [])
                )
                context.api_recommendations.append(recommendation)
        except json.JSONDecodeError:
            pass

    async def _conduct_conversation(self, initial_input: str) -> ConversationContext:
        """Conduct multi-turn conversation to refine requirements"""
        # Add initial input to conversation history
        self.context.conversation_history.append({"role": "user", "content": initial_input})
        
        # Initial analysis prompt
        system_prompt = """You are an expert bot creation assistant. Analyze the user's request 
        and identify missing information about bot type, features, data sources, and UI preferences.
        Respond with only the most important clarifying question."""
        
        self.client.set_system_prompt(system_prompt)
        
        # Continue conversation until all required info is gathered
        while not self._is_context_complete():
            # Get next clarifying question based on missing information
            next_question = self._get_next_question()
            
            # Use configured model to generate contextually appropriate question
            _, refined_question = self.client.chat_completion(
                json.dumps(self.context.conversation_history) + f"\nNext question: {next_question}",
                self.model,
                None
            )
            
            # Get user's response
            print(refined_question)
            response = await asyncio.get_event_loop().run_in_executor(None, input)
            
            # Update context with new information
            self._update_context(next_question, response)
            
            # Add to conversation history
            self.context.conversation_history.append(
                {"role": "assistant", "content": refined_question}
            )
            self.context.conversation_history.append(
                {"role": "user", "content": response}
            )
        
        return self.context

    async def _structure_requirements(self, context: ConversationContext) -> Dict:
        """Convert conversation context into structured JSON"""
        system_prompt = """You are a requirements structuring assistant. Convert the conversation 
        history into a structured JSON format with bot_type, features, data_source, and ui_preferences."""
        
        self.client.set_system_prompt(system_prompt)
        
        # Generate structured output
        _, structured_json = self.client.chat_completion(
            json.dumps(context.conversation_history),
            self.model,
            None
        )
        
        try:
            return json.loads(structured_json)
        except json.JSONDecodeError:
            return context.to_json()

    def _is_context_complete(self) -> bool:
        """Check if we have all required information"""
        return (
            bool(self.context.bot_type) and
            bool(self.context.features) and
            bool(self.context.data_source)
        )

    def _get_next_question(self) -> str:
        """Get next clarifying question based on missing information"""
        if not self.context.bot_type:
            return self._clarifying_questions["bot_type"]
        elif not self.context.features:
            return self._clarifying_questions["features"]
        elif not self.context.data_source:
            return self._clarifying_questions["data_source"]
        elif not self.context.ui_preferences:
            return self._clarifying_questions["ui_preferences"]
        return ""

    def _update_context(self, question: str, response: str):
        """Update context based on question and response"""
        if "type of bot" in question.lower():
            self.context.bot_type = response
        elif "features" in question.lower():
            self.context.features = [f.strip() for f in response.split(",")]
        elif "data source" in question.lower():
            self.context.data_source = response
        elif "ui preferences" in question.lower():
            self.context.ui_preferences = {"design": response}

# Example usage:
if __name__ == "__main__":
    async def main():
        agent = UserInteractionAgent()
        structured_requirements = await agent.get_user_input()
        print("\nStructured Requirements:")
        print(structured_requirements)
    
    asyncio.run(main()) 