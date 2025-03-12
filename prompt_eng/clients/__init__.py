from typing import Tuple, Dict, Any, List, Optional
import logging
import json
import aiohttp
from .models import AIModel, ModelOptions
from ..config import config_factory
import re
import asyncio
import os

logger = logging.getLogger(__name__)

async def bootstrap_client_and_model(preferred_model: str = None) -> Tuple[Any, AIModel]:
    """Initialize a client and select a model based on configuration"""
    config = config_factory.load_config()
    
    # For testing, use mock client
    if config["chatbot_api_host"] == "mock" or os.environ.get("TEST_MODE") == "true":
        logger.info("Using MockChatbotClient for testing")
        client = MockChatbotClient("mock")
        return client, AIModel(id="mock")
    
    # Initialize appropriate client based on configuration
    try:
        client = ChatbotClientFactory.create_client(config)
        
        # Get available models
        models = await client.get_models()
        
        # If preferred model is specified, try to find it
        if preferred_model:
            for model in models:
                model_id = model.id if hasattr(model, 'id') else model.name
                if model_id.lower() == preferred_model.lower():
                    return client, model
        
        # Otherwise, return the first available model
        if models:
            return client, models[0]
        
        # If no models available, fall back to mock
        logger.warning("No models available, falling back to mock client")
        client = MockChatbotClient("mock")
        return client, AIModel(id="mock")
    except Exception as e:
        logger.error(f"Error initializing client: {str(e)}, falling back to mock client")
        client = MockChatbotClient("mock")
        return client, AIModel(id="mock")

class ChatbotClient:
    def __init__(self):
        self._system_prompt: str = ""
    
    async def get_models(self) -> List[AIModel]:
        pass

    async def chat_completion(self, message: str, model: AIModel, options: Optional[ModelOptions] = None) -> Tuple[int, str]:
        pass

    def set_system_prompt(self, prompt: str) -> None:
        if prompt:
            self._system_prompt = prompt

    def _generate_system_message(self) -> Dict[str, str]:
        if self._system_prompt:
            return {"role": "system", "content": self._system_prompt}
        else:
            return {}

class ChatbotClientFactory:
    @classmethod
    def create_client(cls, config: Dict[str, str]) -> ChatbotClient:
        client_type = cls._detect_client_type(config)
        host = config["chatbot_api_host"]
        
        if client_type == "openwebui":
            return OpenWebUIClient(host=host, bearer=config["bearer"])
        elif client_type == "ollama":
            return OllamaClient(host=host)
        else:
            raise ValueError(f"Unknown client type: {client_type}")
    
    @classmethod
    def _detect_client_type(cls, config: Dict[str, str]):
        # check if host is explicitly specified
        host = config["chatbot_api_host"].lower()
        
        # try openwebui first
        if "fau" in host or "chat.hpc" in host or "openwebui" in host:
            logger.info("Detected OpenWebUI client from host: " + host)
            return "openwebui"
        
        # try ollama
        if "ollama" in host or "localhost" in host:
            logger.info("Detected Ollama client from host: " + host)
            return "ollama"
        
        # default to openwebui if bearer token is provided
        if config.get("bearer"):
            logger.info("Defaulting to OpenWebUI client based on bearer token")
            return "openwebui"
            
        # default to ollama
        logger.info("Defaulting to Ollama client")
        return "ollama"

class OpenWebUIClient(ChatbotClient):
    def __init__(self, host: str, bearer: str):
        super().__init__()
        # Ensure the host has a scheme
        if not host.startswith(('http://', 'https://')):
            self.host = f"https://{host}"
        else:
            self.host = host
        self.bearer = bearer
        self.max_retries = 3
        self.timeout = 60  # Increase timeout to 60 seconds
    
    async def get_models(self) -> List[AIModel]:
        """Get available models from OpenWebUI"""
        try:
            headers = {"Authorization": f"Bearer {self.bearer}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.host}/api/models", headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched models from {self.host}")
                        return [AIModel(id=model["id"]) for model in data.get("data", [])]
                    else:
                        logger.error(f"Failed to get models: {response.status}")
                        raise Exception(f"Failed to get models: {response.status}")
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []
    
    async def chat_completion(self, message: str, model: AIModel, options: Optional[ModelOptions] = None) -> Tuple[int, str]:
        """Send chat completion request to OpenWebUI with retry logic"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                headers = {
                    "Authorization": f"Bearer {self.bearer}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": model.id,
                    "messages": [{"role": "user", "content": message}],
                    "stream": False
                }
                
                # Add system prompt if available
                if self._system_prompt:
                    data["messages"].insert(0, {"role": "system", "content": self._system_prompt})
                
                logger.debug(f"Request to {self.host}/api/chat/completions: {data}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.host}/api/chat/completions", 
                        json=data, 
                        headers=headers,
                        timeout=self.timeout
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return 200, result["choices"][0]["message"]["content"]
                        elif response.status in [502, 503, 504]:  # Gateway errors
                            retry_count += 1
                            logger.warning(f"Gateway error {response.status}, retrying ({retry_count}/{self.max_retries})...")
                            await asyncio.sleep(2 * retry_count)  # Exponential backoff
                            continue
                        else:
                            logger.error(f"Chat completion failed: {response.status}")
                            raise Exception(f"Chat completion failed: {response.status}")
            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(f"Request timed out, retrying ({retry_count}/{self.max_retries})...")
                await asyncio.sleep(2 * retry_count)  # Exponential backoff
                continue
            except Exception as e:
                logger.error(f"Chat completion failed: {e}")
                return 500, str(e)
        
        # If we've exhausted all retries, fall back to mock response
        logger.warning("Exhausted all retries, falling back to mock response")
        mock_client = MockChatbotClient()
        if self._system_prompt:
            mock_client.set_system_prompt(self._system_prompt)
        return await mock_client.chat_completion(message, model, options)

class OllamaClient(ChatbotClient):
    def __init__(self, host: str):
        super().__init__()
        self.host = host
    
    async def chat_completion(self, message: str, model: AIModel, options: Optional[ModelOptions] = None) -> Tuple[int, str]:
        """Send chat completion request to Ollama"""
        try:
            data = {
                "model": model.id,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            }
            logger.debug(f"Request to {self.host}/api/chat/completions: {data}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.host}/api/chat/completions", json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return 200, result["choices"][0]["message"]["content"]
                    else:
                        raise Exception(f"Chat completion failed: {response.status}")
        except Exception as e:
            logger.debug(f"Chat completion failed: {e}")
            return 500, str(e)
    
    async def get_models(self) -> List[AIModel]:
        """Get available models from Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.host}/api/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [AIModel(id=model["id"]) for model in data["models"]]
                    else:
                        raise Exception(f"Failed to get models: {response.status}")
        except Exception as e:
            logger.debug(f"Failed to get models: {e}")
            return []

class MockChatbotClient:
    def __init__(self, model_name: str = "mock"):
        self.model_name = model_name
        self._system_prompt = ""

    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt for the chat session"""
        if prompt:
            self._system_prompt = prompt

    async def chat_completion(self, message: str, model: AIModel, options: Optional[ModelOptions] = None) -> Tuple[int, str]:
        prompt = message
        
        # If this is a Master Bot LLM prompt (check for specific format markers)
        if "INTENT:" in prompt or "Based on this context and the user's message" in prompt:
            return await self._handle_master_bot_prompt(prompt)
        
        # Handle other types of prompts for bot generation
        if "conversation flow" in prompt.lower():
            response = {
                "intents": [
                    {"name": "get_weather", "patterns": ["weather in *", "forecast for *"]},
                    {"name": "get_alerts", "patterns": ["alerts in *", "warnings for *"]},
                    {"name": "change_location", "patterns": ["change location to *", "switch to *"]}
                ],
                "responses": {
                    "get_weather": ["Here's the weather for {location}: {weather_data}"],
                    "get_alerts": ["Current alerts for {location}: {alerts}"],
                    "change_location": ["Location changed to {location}"]
                },
                "fallbacks": ["I didn't understand that. Could you rephrase?"],
                "context_rules": {
                    "location_required": ["get_weather", "get_alerts"],
                    "data_required": ["get_weather"]
                }
            }
        elif "business rules" in prompt.lower():
            response = {
                "conditions": [
                    {"if": "location_not_found", "then": "prompt_for_location"},
                    {"if": "api_error", "then": "show_error_message"},
                    {"if": "alerts_exist", "then": "show_alerts_first"}
                ],
                "actions": {
                    "prompt_for_location": "Ask user to provide location",
                    "show_error_message": "Display API error to user",
                    "show_alerts_first": "Prioritize alerts in display"
                }
            }
        elif "bot implementation" in prompt.lower():
            response = {
                "imports": ["aiohttp", "sqlite3", "json"],
                "classes": ["WeatherBot", "APIClient", "Database"],
                "methods": {
                    "WeatherBot": ["get_weather", "get_alerts", "update_location"],
                    "APIClient": ["fetch_weather", "fetch_alerts"],
                    "Database": ["store_preferences", "get_history"]
                },
                "implementation": {
                    "language": "python",
                    "async": True,
                    "error_handling": True,
                    "database": "sqlite"
                }
            }
        else:
            response = {"error": "Unknown prompt type"}

        return 200, json.dumps(response)
    
    async def _handle_master_bot_prompt(self, prompt: str) -> Tuple[int, str]:
        """Handle prompts for the Master Bot LLM integration"""
        # Extract the user message from the prompt
        user_message = ""
        message_match = re.search(r'user\'s message: "([^"]+)"', prompt)
        if message_match:
            user_message = message_match.group(1).lower()
        
        # Extract available bots if present
        available_bots = []
        try:
            context_match = re.search(r'Current context: ({.+})', prompt, re.DOTALL)
            if context_match:
                context_json = json.loads(context_match.group(1))
                if "available_bots" in context_json:
                    available_bots = context_json["available_bots"]
        except:
            pass
        
        # Generate mock LLM responses based on the user message
        if "create" in user_message and "bot" in user_message:
            # Handle bot creation intent
            bot_type = None
            if "weather" in user_message:
                bot_type = "weather"
            elif "customer" in user_message or "service" in user_message:
                bot_type = "customer_service"  
            elif "commerce" in user_message or "shop" in user_message:
                bot_type = "ecommerce"
            
            # Extract bot name if present
            bot_name = None
            name_match = re.search(r"(called|named)\s+(\w+)", user_message)
            if name_match:
                bot_name = name_match.group(2)
            
            # Formulate response based on available information
            entities = {"intent": "create_bot"}
            if bot_type:
                entities["bot_type"] = bot_type
            if bot_name:
                entities["bot_name"] = bot_name
                
            response = f"""
INTENT: Create a new bot
ENTITIES: {json.dumps(entities)}
ACTION: create_bot
RESPONSE: I'd be happy to help you create a {bot_type or 'new'} bot{f' called {bot_name}' if bot_name else ''}. What type of bot would you like to create?
"""
            
        elif "list" in user_message and "bot" in user_message:
            # Handle list bots intent
            if available_bots:
                bot_list = ", ".join(available_bots)
                response = f"""
INTENT: List all available bots
ENTITIES: {{"intent": "list_bots"}}
ACTION: list_bots
RESPONSE: Here are all your available bots: {bot_list}
"""
            else:
                response = """
INTENT: List all available bots
ENTITIES: {"intent": "list_bots"}
ACTION: list_bots
RESPONSE: You don't have any bots yet. Would you like to create one?
"""
                
        elif any(bot_name in user_message for bot_name in available_bots):
            # Handle bot details/update/delete intent
            matching_bot = next((bot for bot in available_bots if bot in user_message), None)
            
            if "delete" in user_message or "remove" in user_message:
                response = f"""
INTENT: Delete a bot
ENTITIES: {{"intent": "delete_bot", "bot_name": "{matching_bot}"}}
ACTION: delete_bot
RESPONSE: Are you sure you want to delete the bot named '{matching_bot}'? This action cannot be undone.
"""
            elif "update" in user_message or "change" in user_message or "modify" in user_message:
                response = f"""
INTENT: Update a bot
ENTITIES: {{"intent": "update_bot", "bot_name": "{matching_bot}"}}
ACTION: update_bot
RESPONSE: What would you like to update about the '{matching_bot}' bot? You can add new features or change existing ones.
"""
            else:
                response = f"""
INTENT: Get bot details
ENTITIES: {{"intent": "get_bot_details", "bot_name": "{matching_bot}"}}
ACTION: get_bot_details
RESPONSE: Here are the details for bot '{matching_bot}'. It includes several intents and business rules. What would you like to know specifically?
"""
                
        elif "help" in user_message:
            # Handle help intent
            response = """
INTENT: Request help or information
ENTITIES: {"intent": "help"}
ACTION: help
RESPONSE: I'm a Master Bot that can help you create and manage bots. You can ask me to create new bots, list your existing bots, get details about a specific bot, update bots, or delete bots you no longer need. What would you like to do?
"""
        else:
            # Default response
            response = """
INTENT: Unclear intent
ENTITIES: {"intent": "unknown"}
ACTION: provide_help
RESPONSE: I'm not sure what you're asking for. I can help you create and manage bots. Would you like to create a new bot, list your existing bots, or get help?
"""
            
        return 200, response

    async def get_models(self):
        return [AIModel(id=self.model_name)] 