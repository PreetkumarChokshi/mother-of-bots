from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

@dataclass
class GeneratedBot:
    name: str
    code: Dict[str, str]  # filename -> code content
    conversation_flow: Dict
    business_rules: List[Dict]

class CodeGenerator:
    def __init__(self):
        self.client = None
        self.model = None
    
    async def generate(self, requirements: Dict, flow: Dict, rules: List[Dict], ui_design: Optional[Dict] = None) -> Dict[str, str]:
        """Generate bot code based on requirements, flow and rules"""
        try:
            code = {
                f"bot.{requirements.get('language', 'py')}": await self._generate_bot_code(requirements, flow, rules),
                "config.py": await self._generate_config(requirements)
            }
            
            # Add API utilities if needed
            if requirements.get("apis"):
                code["api_utils.py"] = await self._generate_api_utils(requirements["apis"])
            
            # Add database utilities if needed
            if requirements.get("database"):
                code["db_utils.py"] = await self._generate_db_utils(requirements["database"])
            
            # Add UI code if provided
            if ui_design:
                code["ui.jsx"] = ui_design.get("ui_code", "")
            
            return code
        except Exception as e:
            raise Exception(f"Failed to generate code: {str(e)}")
    
    async def _generate_bot_code(self, requirements: Dict, flow: Dict, rules: List[Dict]) -> str:
        try:
            # Generate prompt for bot code
            prompt = f"""Generate a complete {requirements.get('language', 'Python')} bot implementation based on:
            1. User requirements: {json.dumps(requirements, indent=2)}
            2. Conversation flow: {json.dumps(flow, indent=2)}
            3. Business rules: {json.dumps(rules, indent=2)}
            
            Generate the bot code."""
            
            # Get response from LLM
            _, code_str = await self.client.chat_completion(prompt, self.model)
            
            return code_str
        except Exception as e:
            raise Exception(f"Failed to generate bot code: {str(e)}")
    
    async def _generate_config(self, requirements: Dict) -> str:
        try:
            # Generate prompt for config code
            prompt = f"""Generate configuration code for a bot with these requirements:
            {json.dumps(requirements, indent=2)}
            
            Generate the config code."""
            
            # Get response from LLM
            _, config_str = await self.client.chat_completion(prompt, self.model)
            
            return config_str
        except Exception as e:
            raise Exception(f"Failed to generate config: {str(e)}")
    
    async def _generate_api_utils(self, apis: List[Dict]) -> str:
        try:
            # Generate prompt for API utilities code
            prompt = f"""Generate API utilities code for these APIs:
            {json.dumps(apis, indent=2)}
            
            Generate the API utilities code."""
            
            # Get response from LLM
            _, utils_str = await self.client.chat_completion(prompt, self.model)
            
            return utils_str
        except Exception as e:
            raise Exception(f"Failed to generate API utilities: {str(e)}")
    
    async def _generate_db_utils(self, database: str) -> str:
        try:
            # Generate prompt for database utilities code
            prompt = f"""Generate database utilities code for {database} database:
            
            Generate the database utilities code."""
            
            # Get response from LLM
            _, utils_str = await self.client.chat_completion(prompt, self.model)
            
            return utils_str
        except Exception as e:
            raise Exception(f"Failed to generate database utilities: {str(e)}")

class FlowDesigner:
    def __init__(self):
        self.client = None
        self.model = None
    
    async def design(self, requirements: Dict) -> Dict:
        """Design conversation flow based on requirements"""
        try:
            # Generate prompt for conversation flow
            prompt = f"""Design a conversation flow for a bot with these requirements:
            {json.dumps(requirements, indent=2)}
            
            Design the conversation flow."""
            
            # Get response from LLM
            _, flow_str = await self.client.chat_completion(prompt, self.model)
            
            logger.debug(f"Flow response: {flow_str}")
            
            try:
                return json.loads(flow_str) if isinstance(flow_str, str) else flow_str
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode flow JSON: {str(e)}")
                logger.error(f"Raw flow string: {flow_str}")
                raise
        except Exception as e:
            raise Exception(f"Failed to design conversation flow: {str(e)}")

class RuleEngine:
    def __init__(self):
        self.client = None
        self.model = None
    
    async def generate_rules(self, requirements: Dict) -> List[Dict]:
        """Generate business rules based on requirements"""
        try:
            # Generate prompt for business rules
            prompt = f"""Generate business rules for a bot with these requirements:
            {json.dumps(requirements, indent=2)}
            
            Generate the business rules."""
            
            # Get response from LLM
            _, rules_str = await self.client.chat_completion(prompt, self.model)
            
            try:
                return json.loads(rules_str) if isinstance(rules_str, str) else rules_str
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode rules JSON: {str(e)}")
                logger.error(f"Raw rules string: {rules_str}")
                raise
        except Exception as e:
            raise Exception(f"Failed to generate business rules: {str(e)}")

class DynamicBotGenerator:
    def __init__(self, preferred_model: Optional[str] = None):
        self.preferred_model = preferred_model
        self.code_generator = CodeGenerator()
        self.flow_designer = FlowDesigner()
        self.rule_engine = RuleEngine()
        self.client = None
        self.model = None
    
    async def initialize(self):
        """Initialize the client and model if not already initialized"""
        if self.client is None:
            # Import bootstrap_client_and_model here to avoid circular dependencies
            from ..clients import bootstrap_client_and_model
            
            # Initialize client and model
            self.client, self.model = await bootstrap_client_and_model(self.preferred_model)
            
            # Set client and model for components
            self.code_generator.client = self.client
            self.code_generator.model = self.model
            self.flow_designer.client = self.client
            self.flow_designer.model = self.model
            self.rule_engine.client = self.client
            self.rule_engine.model = self.model
    
    async def generate_bot(self, requirements: Dict) -> GeneratedBot:
        """Generate a complete bot based on requirements"""
        try:
            # Initialize client with preferred model
            await self.initialize()
            
            # Design conversation flow
            flow = await self.flow_designer.design(requirements)
            
            # Generate business rules
            rules = await self.rule_engine.generate_rules(requirements)
            
            # Generate code
            code = await self.code_generator.generate(requirements, flow, rules)
            
            return GeneratedBot(
                name=requirements["name"],
                code=code,
                conversation_flow=flow,
                business_rules=rules
            )
        except Exception as e:
            raise Exception(f"Failed to generate bot: {str(e)}")

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        generator = DynamicBotGenerator()
        await generator.initialize()
        requirements = {
            "name": "WeatherBot",
            "type": "weather",
            "features": ["daily_forecast", "location_based"],
            "platform": "web",
            "apis": [{"name": "OpenWeatherMap", "version": "2.5"}],
            "language": "python",
            "async_support": True
        }
        bot = await generator.generate_bot(requirements)
        print(f"Generated bot: {bot.name}")
        print("Code files:", list(bot.code.keys()))
        print("\nAPI integrations:", requirements["apis"])
    
    asyncio.run(test()) 