from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
from models import AIModel, ModelOptions

class ChatbotClient(ABC):
    """Abstract base class defining the interface for chatbot clients."""
    
    def __init__(self):
        self._system_prompt: str = ""
    
    @abstractmethod
    def get_models(self) -> List[AIModel]:
        """Get the list of available models from the server.
        
        Returns:
            List[AIModel]: List of available AI models
        """
        pass

    @abstractmethod
    def chat_completion(self, message: str, model: AIModel, options: ModelOptions | None) -> Tuple[int, str]:
        """Send a message to an LLM and get the response.
        
        Args:
            message (str): The input message to send to the model
            model (AIModel): The AI model to use
            options (ModelOptions | None): Optional model parameters
            
        Returns:
            Tuple[int, str]: (time taken in milliseconds, model response)
        """
        pass

    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt for the chat session.
        
        Args:
            prompt (str): The system prompt to set
        """
        if prompt:
            self._system_prompt = prompt

    def _generate_system_message(self) -> Dict[str, str]:
        """Generate a system message dictionary for the API request.
        
        Returns:
            Dict[str, str]: System message in the format {"role": "system", "content": prompt}
                           or empty dict if no system prompt is set
        """
        if self._system_prompt:
            return {"role": "system", "content": self._system_prompt}
        else:
            return {} 