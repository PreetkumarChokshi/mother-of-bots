from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
from models import AIModel, ModelOptions

class ChatbotClient(ABC):
    def __init__(self):
        self._system_prompt: str = ""
    
    @abstractmethod
    def get_models(self) -> List[AIModel]:
        pass

    @abstractmethod
    def chat_completion(self, message: str, model: AIModel, options: ModelOptions | None) -> Tuple[int, str]:
        pass

    def set_system_prompt(self, prompt: str) -> None:
        if prompt:
            self._system_prompt = prompt

    def _generate_system_message(self) -> Dict[str,str]:
        if self._system_prompt:
            return {"role": "system", "content": self._system_prompt}
        else:
            return {} 