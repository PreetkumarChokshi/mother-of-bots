from typing import Dict, Optional
from clients import bootstrap_client_and_model

class UIGeneratorAgent:
    def __init__(self):
        self.client, self.model = bootstrap_client_and_model(
            preferred_model="qwen2"
        )
    
    async def generate_ui(self, requirements: Dict) -> Dict:
        """Generate UI code based on requirements"""
        try:
            system_prompt = """Generate a modern, responsive UI using React and Tailwind CSS.
            Consider the user's design preferences and bot type.
            Return complete, functional component code."""
            
            self.client.set_system_prompt(system_prompt)
            
            design_prompt = f"""Create a UI for a {requirements.get('bot_type', 'generic')} bot with:
            Style: {requirements.get('ui_preferences', {}).get('design', 'modern')}
            Features: {requirements.get('features', [])}"""
            
            _, ui_code = self.client.chat_completion(
                design_prompt,
                self.model,
                None
            )
            
            return {
                "status": "success",
                "ui_code": ui_code
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "ui_code": self._get_default_ui()
            }
    
    def _get_default_ui(self) -> str:
        """Return default UI template"""
        return """
export default function BotUI() {
  return (
    <div className="p-4 max-w-md mx-auto bg-white rounded-xl shadow-md">
      <h1 className="text-xl font-bold">Bot Interface</h1>
      <div className="mt-4">
        <div className="space-y-4">
          <input
            type="text"
            className="w-full px-4 py-2 border rounded"
            placeholder="Type your message..."
          />
          <button className="w-full px-4 py-2 bg-blue-500 text-white rounded">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
"""

# Example usage:
if __name__ == "__main__":
    agent = UIGeneratorAgent()
    sample_requirements = {"design": "Playful, bright colors with rounded buttons"}
    print("Generated UI Code:", agent.generate_ui(sample_requirements)) 