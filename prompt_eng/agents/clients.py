import os
import requests
from typing import List, Tuple, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from .models import AIModel, ModelOptions
import logging
import json
from ..config import config_factory
from ..base import ChatbotClient
from ..rag import RAGPipeline

logger = logging.getLogger(__name__)

# interface for chatbot clients
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

    # this format is currently the same for both APIS, consider overriding if your client has different requirements.
    def _generate_system_message(self) -> Dict[str,str]:
        if self._system_prompt:
            return {"role": "system", "content": self._system_prompt}
        else:
            return {}


# instead of trying to make all the decisions in the client, we can use a factory to create the appropriate client based on the configuration.
# this reduces the complexity of the client and makes it easier to add new clients in the future.
class ChatbotClientFactory():
    @classmethod
    def create_client(cls, config: Dict[str,str]) -> ChatbotClient:
        client_type = cls._detect_client_type(config)
        host = config["chatbot_api_host"]
        # TODO : We'll simply decide using the FAU host, and consider anything else to be
        # ollama client for now.
        if client_type == "openwebui":
            return OpenWebUIClient(host=host, bearer=config["bearer"])
        elif client_type == "ollama":
            return OllamaClient(host=host)
        else:
            raise ValueError(f"Unknown client type: {client_type}")
    
    @classmethod
    def _detect_client_type(cls, config: Dict[str, str]):
        # try ollama
        if "ollama" in config["chatbot_api_host"].lower():
            return "ollama"
        # try openwebui
        if "fau" in config["chatbot_api_host"].lower():
            return "openwebui"
        # default to ollama
        return "ollama"
        

                  
class OpenWebUIClient(ChatbotClient):
    def __init__(self, host: str, bearer: str):
        super().__init__()
        self.host = host
        self.bearer = bearer

    def get_models(self) -> List[AIModel]:
        """Get available models from OpenWebUI"""
        try:
            response = requests.get(f"{self.host}/api/models")
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                raise Exception(f"Failed to get models: {response.status_code}")
        except Exception as e:
            logger.debug(f"Failed to get models: {e}")
            return []

    def chat_completion(self, message: str, model: AIModel, options: ModelOptions | None = None) -> Tuple[int, str]:
        """Send chat completion request to OpenWebUI"""
        try:
            data = {
                "model": model.id,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            }
            logger.debug(f"Request to {self.host}/api/chat/completions: {data}")
            response = requests.post(f"{self.host}/api/chat/completions", json=data)
            if response.status_code == 200:
                result = response.json()
                return 200, result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Chat completion failed: {response.status_code}")
        except Exception as e:
            logger.debug(f"Chat completion failed: {e}")
            return 500, str(e)

class OllamaClient(ChatbotClient):
    def __init__(self, host: str):
        super().__init__()
        self.host = host

    def chat_completion(self, message: str, model: AIModel, options: ModelOptions | None = None) -> Tuple[int, str]:
        """Send chat completion request to Ollama"""
        try:
            data = {
                "model": model.id,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            }
            logger.debug(f"Request to {self.host}/api/chat/completions: {data}")
            response = requests.post(f"{self.host}/api/chat/completions", json=data)
            if response.status_code == 200:
                result = response.json()
                return 200, result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Chat completion failed: {response.status_code}")
        except Exception as e:
            logger.debug(f"Chat completion failed: {e}")
            return 500, str(e)
    
    def get_models(self) -> List[AIModel]:
        """Get available models from Ollama"""
        try:
            response = requests.get(f"{self.host}/api/models")
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                raise Exception(f"Failed to get models: {response.status_code}")
        except Exception as e:
            logger.debug(f"Failed to get models: {e}")
            return []

    def set_system_prompt(self, prompt):
        if prompt:
            self._system_prompt = prompt
        

def _select_model_by_rules(prompt: str, available_models: List[AIModel]) -> AIModel:
    """
    Select the most appropriate model based on prompt characteristics and rules.
    Returns the recommended model for the given prompt.
    """
    prompt_lower = prompt.lower()
    
    # Convert models to a dict for easier lookup
    model_dict = {model.name.lower(): model for model in available_models}
    
    # Rule 1: Code-related tasks
    if any(keyword in prompt_lower for keyword in ['code', 'programming', 'debug', 'function', 'algorithm']):
        code_models = ['codellama', 'deepseek-coder', 'wizard-coder']
        for model_name in code_models:
            if any(model_name in m.lower() for m in model_dict.keys()):
                return model_dict[next(m for m in model_dict.keys() if model_name in m.lower())]
    
    # Rule 2: Creative writing tasks
    if any(keyword in prompt_lower for keyword in ['story', 'creative', 'write', 'poem', 'novel']):
        creative_models = ['mistral', 'llama2']
        for model_name in creative_models:
            if any(model_name in m.lower() for m in model_dict.keys()):
                return model_dict[next(m for m in model_dict.keys() if model_name in m.lower())]
    
    # Rule 3: Mathematical or analytical tasks
    if any(keyword in prompt_lower for keyword in ['math', 'calculate', 'solve', 'equation', 'analysis']):
        math_models = ['qwen', 'deepseek', 'mixtral']
        for model_name in math_models:
            if any(model_name in m.lower() for m in model_dict.keys()):
                return model_dict[next(m for m in model_dict.keys() if model_name in m.lower())]
    
    # Rule 4: Large context tasks
    if len(prompt.split()) > 500:
        large_context_models = ['claude', 'mixtral', 'qwen']
        for model_name in large_context_models:
            if any(model_name in m.lower() for m in model_dict.keys()):
                return model_dict[next(m for m in model_dict.keys() if model_name in m.lower())]
    
    # Default to the smallest model if no rules match or preferred models aren't available
    return _get_smallest_model(available_models)

def bootstrap_client_and_model(preferred_model: str = "", prompt: str = "") -> Tuple[ChatbotClient, AIModel]:
    """
    Generic bootstrapper to load config, create client with factory, and provide a model.
    If a preferred model is provided (and found) it is used. Otherwise, if a prompt is provided a
    rule-based selection is used; if not, the smallest model is selected.
    """
    config = config_factory()
    client = ChatbotClientFactory.create_client(config)
    models = client.get_models()

    if not models:
        raise ValueError(
            "No available models were retrieved from the API endpoint. "
            "Please check your 'chatbot_api_host' configuration and ensure the server is returning models."
        )

    picked_model = None
    if preferred_model:
        picked_model = next((model for model in models if model.name == preferred_model), None)
        if not picked_model:
            logger.warning(f"Model {preferred_model} not found. Using rule-based selection instead.")
    if not picked_model:
        if prompt:
            picked_model = _select_model_by_rules(prompt, models)
            logger.info(f"Rule-based selection chose model: {picked_model.name}")
        else:
            picked_model = _get_smallest_model(models)
            logger.info(f"No prompt provided, using smallest model: {picked_model.name}")

    return client, picked_model

def _get_smallest_model(models: List[AIModel]) -> AIModel:
    """
    Get the smallest model in the list of models by parameter size.
    Raises a descriptive error if the list is empty.
    """
    if not models:
        raise ValueError(
            "No available models were found to select from. "
            "Please verify your server's model list."
        )

    valid_models = []
    for model in models:
        try:
            size = float(model.parameter_size.strip("B"))
            valid_models.append((size, model))
        except ValueError:
            continue

    if valid_models:
        return min(valid_models, key=lambda x: x[0])[1]

    # Fallback: if sizes are not parseable, return the first model.
    return models[0]

def config_factory():
    config_path = os.path.join(os.path.dirname(__file__), 'config.cfg')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key.strip()] = value.strip()

    return config

def bootstrap_rag_client(preferred_model: str = "", docs: List[str] = []) -> Tuple[RAGPipeline, AIModel]:
    """Bootstrap a client with RAG capabilities"""
    config = config_factory()
    client = ChatbotClientFactory.create_client(config)
    models = client.get_models()
    
    # Model selection logic (existing)
    picked_model = _select_model_by_rules("document analysis", models)
    
    # Initialize RAG pipeline
    rag = RAGPipeline(client, picked_model)
    
    if docs:
        rag.ingest_documents(docs)
    
    return rag, picked_model
