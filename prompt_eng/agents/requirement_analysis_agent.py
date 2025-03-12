from typing import Dict
from analysis.context_builder import ContextBuilder
from clients import bootstrap_client_and_model

class RequirementAnalysisAgent:
    def __init__(self):
        self.context_builder = ContextBuilder()
        # Initialize client and model once
        self.client, self.model = bootstrap_client_and_model(
            preferred_model="qwen2"  # Use available model from config
        )
    
    async def analyze(self, user_description: str) -> Dict:
        """Analyze requirements and provide comprehensive analysis"""
        try:
            # Set up system prompt
            system_prompt = """Analyze the bot requirements and extract:
            1. Primary intent/purpose
            2. Required features
            3. Integration needs
            4. Complexity level
            Respond in JSON format."""
            
            self.client.set_system_prompt(system_prompt)
            
            # Get analysis from model
            _, analysis_json = self.client.chat_completion(
                user_description,
                self.model,
                None
            )
            
            # Build context using the analysis
            bot_context = self.context_builder.build(user_description)
            
            return {
                "requirements": bot_context.requirements,
                "analysis": analysis_json
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "requirements": self.context_builder.build(user_description).requirements
            }

# Example usage:
if __name__ == "__main__":
    agent = RequirementAnalysisAgent()
    sample_description = "I want a weather bot that is playful and provides daily summaries."
    requirements = agent.analyze(sample_description)
    print("Extracted requirements:", requirements) 