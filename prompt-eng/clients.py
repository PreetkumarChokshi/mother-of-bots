import os
import requests
from typing import List, Tuple, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from models import AIModel, ModelOptions
from config import config_factory
import logging
from rag import RAGPipeline
from base import ChatbotClient

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
            raise ValueError("could not autodetect client type.")
    
    @classmethod
    def _detect_client_type(cls, config: Dict[str, str]):
        
        # try ollama
        url = f"http://{config['chatbot_api_host']}/api/tags"
        try:
            ollama_resp = requests.get(url, timeout=1)
            if ollama_resp.status_code == 200:
                logger.info("autodetected ollama client")
                return "ollama"
        except Exception:
            pass

        # try openwebui
        headers = {"Authorization": f"Bearer {config['bearer']}"}
        url = f"https://{config['chatbot_api_host']}/api/models"
        openwebui_resp = requests.get(url, headers=headers, timeout=1)
        try:
            data = openwebui_resp.json()
            logger.info("autodetected openwebui client")
            return "openwebui"
        except Exception:
            pass

        return "unknown"
        

                  
class OpenWebUIClient(ChatbotClient):
    def __init__(self, host: str, bearer: str):
        super().__init__()
        self._host = host
        self._bearer = bearer

    def get_models(self) -> List[AIModel]:
        """Get the list of available models from the server."""
        data = self._get_models()
        models = []
        for model_info in data.get("data", []):
            # If available, use the nested details; otherwise default to "Unknown"
            model = AIModel(
                name=model_info.get("name"),
                parameter_size=model_info.get("ollama", {}).get("details", {}).get("parameter_size", "Unknown")
            )
            models.append(model)
        return models

    def chat_completion(self, message: str, model: AIModel, options: ModelOptions | None = None) -> Tuple[int, str]:
        """Send a message to an LLM of your choice and get the response."""
        
        start_time = datetime.now(timezone.utc)
        response_json = self._chat(message, model.name, options)
        end_time = datetime.now(timezone.utc)
        time_elapsed_in_milliseconds = int((end_time - start_time).total_seconds() * 1000)
        
        # return first choice
        for choice in response_json["choices"]:
            try:
                return time_elapsed_in_milliseconds, choice["message"]["content"]
            except Exception as exc:
                return -1, str(exc)

    def _chat(self, message: str, model_name: str, options: ModelOptions | None = None):
        """Send a chat request to the API and get the response."""
        headers = {
            "Authorization": f"Bearer {self._bearer}",
            "Content-Type": "application/json"
        }
        url = f"https://{self._host}/api/chat/completions"
        
        post_body = {
            "model": model_name,
            "messages": [{"role": "user", "content": message}],
            "stream": False
        }
        
        if self._system_prompt:
            post_body["messages"].insert(0, {
                "role": "system",
                "content": self._system_prompt
            })
        
        if options:
            post_body.update(self._parse_options(options))
        
        logger.debug(f"Request to {url}: {post_body}")
        response = requests.post(url, json=post_body, headers=headers)
        
        if response.status_code != 200:
            error_msg = f"API Error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        return response.json()

    # TODO : Maybe considering making options a type, that way it can be validated and consistent
    # between client implementations.
    def _parse_options(self, options: ModelOptions) -> Dict[str, Any]:
        """Parse the generic options type into params for the specific API"""
        options.validate()
        mapping = {
            "num_ctx": options.context_window_size,
            "max_tokens": options.max_tokens,
            "top_k": options.top_k,
            "top_p": options.top_p,
            "temperature": options.temperature,
            "seed": options.seed
        }
        # Only include options that are not None
        return {k: v for k, v in mapping.items() if v is not None}

    def _get_models(self) -> Dict[str, Any]:
        """Get the list of available models from the server."""
        url = f"https://{self._host}/api/models"
        headers = {
            "Authorization": f"Bearer {self._bearer}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
class OllamaClient(ChatbotClient):
    def __init__(self, host: str):
        super().__init__()
        self._host = host

    def chat_completion(self, message: str, model: AIModel, options: ModelOptions | None = None) -> Tuple[int, str]:
        """Send a chat request to the API and get the response."""
        start_time = datetime.now(timezone.utc)
        response = self._chat(message, model.name, options)
        end_time = datetime.now(timezone.utc)
        time_taken_in_ms = (end_time - start_time).total_seconds() * 1000
        return time_taken_in_ms, response["message"]["content"]


    def _chat(self, message: str, model_name: str, options: ModelOptions | None = None) -> Dict[str,str]:
        """Send a chat request to the API and get the response."""
        url = f"http://{self._host}/api/chat"
        post_body = {
            "model": model_name,
            "messages": [
                {
                "role": "user",
                "content": message
                }
            ],
            "stream": False
        }
        post_body.update(self._parse_options(options) if options else {})
        if self._system_prompt:
            post_body["messages"] = [self._generate_system_message()] + post_body["messages"]
        response = requests.post(url, json=post_body, timeout=600)
        response.raise_for_status()
        return response.json()

    # reference https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
    def _parse_options(self, options: ModelOptions) -> None:
        """Converts generic options into API specfic options"""
        nested_options: Dict[str, Any] = {}
        options.validate()

        if options.max_tokens:
            nested_options["num_predict"] = options.max_tokens
        if options.temperature:
            nested_options["temperature"] = options.temperature
        if options.top_p:
            nested_options["top_p"] = options.top_p
        if options.seed:
            nested_options["seed"] = options.seed
        if options.top_k:
            nested_options["top_k"] = options.top_k
        if options.context_window_size:
            nested_options["num_ctx"] = options.context_window_size
        if nested_options:
            return {"options": nested_options}

        return {}
   
    def get_models(self) -> List[AIModel]:  
        """Get a list of available models. API CALL"""
        data = self._get_models()
        models = []
        for model_info in data["models"]:
            # Extract size from model name if not in details
            size = "Unknown"
            if "details" in model_info and "parameter_size" in model_info["details"]:
                size = model_info["details"]["parameter_size"]
            else:
                # Try to extract size from name
                name_lower = model_info["name"].lower()
                if "3b" in name_lower:
                    size = "3B"
                elif "7b" in name_lower:
                    size = "7B"
                elif "11b" in name_lower:
                    size = "11B"
                elif "13b" in name_lower:
                    size = "13B"
                elif "27b" in name_lower:
                    size = "27B"
                elif "70b" in name_lower:
                    size = "70B"
            
            model = AIModel(
                name=model_info["name"],
                parameter_size=size
            )
            models.append(model)
        return models

    def _get_models(self):
        """Get a list of available models."""
        url = f"http://{self._host}/api/tags"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
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
