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
        # Basic code templates for fallback
        self.templates = {
            "weather": {
                "bot.py": '''
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.default_location = "New York"
        
    async def get_weather(self, location=None):
        """Get current weather for a location"""
        location = location or self.default_location
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": location,
                    "appid": self.api_key,
                    "units": "metric"
                }
                url = f"{self.base_url}/weather"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_weather(data, location)
                    else:
                        logger.error(f"API error: {response.status}")
                        return f"Sorry, I couldn't get weather data for {location}."
        except Exception as e:
            logger.error(f"Error getting weather: {str(e)}")
            return f"Sorry, there was a problem retrieving weather for {location}."
    
    async def get_alerts(self, location=None):
        """Get weather alerts for a location"""
        location = location or self.default_location
        try:
            # In a real implementation, this would use the weather API
            return f"No active weather alerts for {location}."
        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            return f"Sorry, I couldn't check alerts for {location}."
    
    def _format_weather(self, data, location):
        """Format weather data into a readable response"""
        temp = data["main"]["temp"]
        condition = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        
        return f"Weather in {location}: {condition}, {temp}°C, humidity {humidity}%, wind speed {wind} m/s"
    
    def update_location(self, new_location):
        """Update the default location"""
        self.default_location = new_location
        return f"Location updated to {new_location}"

# Example usage
async def main():
    bot = WeatherBot("YOUR_API_KEY")
    weather = await bot.get_weather("London")
    print(weather)
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
''',
                "config.py": '''
# Weather Bot Configuration

# API Settings
WEATHER_API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.openweathermap.org/data/2.5"

# Bot Settings
DEFAULT_LOCATION = "New York"
UNITS = "metric"  # Options: metric, imperial
LANGUAGE = "en"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "weather_bot.log"

# Cache Settings
CACHE_ENABLED = True
CACHE_TIMEOUT = 600  # 10 minutes

# User Preferences
MAX_SAVED_LOCATIONS = 5
ENABLE_ALERTS = True
'''
            },
            "customer_service": {
                "bot.py": '''
import aiohttp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerServiceBot:
    def __init__(self, crm_api_url, api_key):
        self.crm_api_url = crm_api_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
    async def create_ticket(self, user_id, issue_description, category="general"):
        """Create a support ticket"""
        try:
            ticket_data = {
                "user_id": user_id,
                "description": issue_description,
                "category": category,
                "created_at": datetime.now().isoformat(),
                "status": "open"
            }
            
            # In a real implementation, this would call the CRM API
            ticket_id = f"TKT-{hash(issue_description) % 10000:04d}"
            
            logger.info(f"Created ticket {ticket_id} for user {user_id}")
            return f"I've created ticket #{ticket_id} for you. A support agent will follow up soon."
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            return "Sorry, I couldn't create a ticket right now. Please try again later."
    
    async def check_ticket_status(self, ticket_id):
        """Check the status of an existing ticket"""
        try:
            # In a real implementation, this would call the CRM API
            statuses = ["open", "in progress", "pending customer response", "resolved"]
            import random
            status = random.choice(statuses)
            
            return f"Ticket #{ticket_id} status: {status}"
        except Exception as e:
            logger.error(f"Error checking ticket status: {str(e)}")
            return f"Sorry, I couldn't retrieve the status for ticket #{ticket_id}."
    
    async def get_faq(self, topic):
        """Get FAQ information about a topic"""
        faqs = {
            "returns": "You can return items within 30 days of purchase with the original receipt.",
            "shipping": "Standard shipping takes 3-5 business days. Express shipping is 1-2 business days.",
            "payment": "We accept all major credit cards, PayPal, and Apple Pay.",
            "hours": "Our customer service hours are Monday-Friday, 9am-6pm EST."
        }
        
        # Try to find an exact match
        if topic.lower() in faqs:
            return faqs[topic.lower()]
        
        # Look for partial matches
        for key, value in faqs.items():
            if key in topic.lower() or topic.lower() in key:
                return value
        
        return "I don't have information about that topic. Would you like me to create a ticket for you?"
    
    async def transfer_to_agent(self, user_id, reason=None):
        """Transfer the conversation to a human agent"""
        try:
            # In a real implementation, this would call the agent queue system
            return "I'm transferring you to a human agent. Please wait a moment while I connect you."
        except Exception as e:
            logger.error(f"Error transferring to agent: {str(e)}")
            return "Sorry, all our agents are currently busy. Can I create a ticket instead?"

# Example usage
async def main():
    bot = CustomerServiceBot("https://api.example.com/crm", "your-api-key")
    response = await bot.create_ticket("user123", "My order hasn't arrived yet")
    print(response)
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
''',
                "config.py": '''
# Customer Service Bot Configuration

# API Settings
CRM_API_URL = "https://api.example.com/crm"
API_KEY = "YOUR_API_KEY"

# Bot Settings
DEFAULT_CATEGORY = "general"
AUTO_ESCALATION_THRESHOLD = 3  # Number of messages before offering human agent

# Ticket Settings
URGENT_KEYWORDS = ["urgent", "emergency", "immediately", "asap"]
PRIORITY_CATEGORIES = ["billing", "technical", "account"]

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "customer_service_bot.log"

# Agent Transfer
MIN_WAIT_TIME = 30  # seconds
MAX_QUEUE_SIZE = 10
'''
            },
            "ecommerce": {
                "bot.py": '''
import aiohttp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcommerceBot:
    def __init__(self, store_api_url, api_key):
        self.store_api_url = store_api_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
    async def search_products(self, query, category=None, max_results=5):
        """Search for products matching the query"""
        try:
            # In a real implementation, this would call the store API
            sample_products = [
                {"id": "P1001", "name": "Smartphone X", "price": 799.99, "category": "electronics"},
                {"id": "P1002", "name": "Wireless Headphones", "price": 149.99, "category": "electronics"},
                {"id": "P1003", "name": "Running Shoes", "price": 89.99, "category": "footwear"},
                {"id": "P1004", "name": "Laptop Pro", "price": 1299.99, "category": "electronics"},
                {"id": "P1005", "name": "Coffee Maker", "price": 79.99, "category": "home"},
            ]
            
            # Filter by query
            results = [p for p in sample_products if query.lower() in p["name"].lower()]
            
            # Filter by category if specified
            if category:
                results = [p for p in results if p["category"] == category]
            
            # Limit results
            results = results[:max_results]
            
            if not results:
                return f"I couldn't find any products matching '{query}'. Would you like to try a different search?"
            
            # Format results
            formatted_results = "\n".join([f"{p['name']} - ${p['price']}" for p in results])
            return f"Here are products matching '{query}':\n{formatted_results}"
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return f"Sorry, I couldn't search for '{query}' right now. Please try again later."
    
    async def check_price(self, product_id=None, product_name=None):
        """Check the price of a product"""
        try:
            # In a real implementation, this would call the store API
            sample_products = {
                "P1001": {"name": "Smartphone X", "price": 799.99},
                "P1002": {"name": "Wireless Headphones", "price": 149.99},
                "P1003": {"name": "Running Shoes", "price": 89.99},
                "P1004": {"name": "Laptop Pro", "price": 1299.99},
                "P1005": {"name": "Coffee Maker", "price": 79.99},
            }
            
            if product_id and product_id in sample_products:
                product = sample_products[product_id]
                return f"{product['name']} costs ${product['price']}"
            
            if product_name:
                for pid, p in sample_products.items():
                    if product_name.lower() in p["name"].lower():
                        return f"{p['name']} costs ${p['price']}"
            
            return "I couldn't find that product. Could you try a different product name or ID?"
        except Exception as e:
            logger.error(f"Error checking price: {str(e)}")
            return "Sorry, I couldn't check the price right now. Please try again later."
    
    async def check_availability(self, product_id=None, product_name=None):
        """Check if a product is in stock"""
        try:
            # In a real implementation, this would call the store API
            import random
            in_stock = random.choice([True, False])
            stock_level = random.randint(0, 20) if in_stock else 0
            
            product_info = await self.check_price(product_id, product_name)
            product_name = product_info.split(" costs")[0] if " costs" in product_info else product_name or product_id
            
            if in_stock:
                return f"{product_name} is in stock. We currently have {stock_level} units available."
            else:
                return f"{product_name} is currently out of stock. Would you like to be notified when it's available?"
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return "Sorry, I couldn't check availability right now. Please try again later."
    
    async def track_order(self, order_id):
        """Track the status of an order"""
        try:
            # In a real implementation, this would call the store API
            statuses = ["processing", "shipped", "out for delivery", "delivered"]
            import random
            status = random.choice(statuses)
            
            return f"Order #{order_id} is currently {status}."
        except Exception as e:
            logger.error(f"Error tracking order: {str(e)}")
            return f"Sorry, I couldn't retrieve the status for order #{order_id}."

# Example usage
async def main():
    bot = EcommerceBot("https://api.example.com/store", "your-api-key")
    response = await bot.search_products("headphones")
    print(response)
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
''',
                "config.py": '''
# E-commerce Bot Configuration

# API Settings
STORE_API_URL = "https://api.example.com/store"
API_KEY = "YOUR_API_KEY"

# Bot Settings
DEFAULT_SEARCH_LIMIT = 5
FEATURED_CATEGORIES = ["electronics", "clothing", "home", "beauty"]

# Product Settings
SHOW_RATINGS = True
ENABLE_RECOMMENDATIONS = True
CURRENCY = "USD"

# Order Settings
TRACK_ORDER_ENABLED = True
CANCEL_ORDER_ENABLED = True

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "ecommerce_bot.log"

# User Preferences
SAVE_SEARCH_HISTORY = True
MAX_SEARCH_HISTORY = 10
'''
            }
        }
    
    async def generate(self, requirements: Dict, flow: Dict, rules: List[Dict], ui_design: Optional[Dict] = None) -> Dict[str, str]:
        """Generate bot code based on requirements, flow and rules"""
        try:
            code = {}
            
            # Try to generate bot code
            bot_code = await self._generate_bot_code(requirements, flow, rules)
            config_code = await self._generate_config(requirements)
            
            # Check if we got valid responses
            if "import" not in bot_code.lower() or len(bot_code) < 100:
                logger.warning("Generated bot code doesn't look valid, using fallback template")
                code = self._get_fallback_code(requirements)
            else:
                code = {
                    f"bot.{requirements.get('language', 'py').lower()}": bot_code,
                    "config.py": config_code
                }
                
                # Add API utilities if needed
                if requirements.get("apis"):
                    api_utils = await self._generate_api_utils(requirements["apis"])
                    if "import" in api_utils.lower() and len(api_utils) > 50:
                        code["api_utils.py"] = api_utils
                
                # Add database utilities if needed
                if requirements.get("database"):
                    db_utils = await self._generate_db_utils(requirements["database"])
                    if "import" in db_utils.lower() and len(db_utils) > 50:
                        code["db_utils.py"] = db_utils
            
            # Add UI code if provided
            if ui_design:
                code["ui.jsx"] = ui_design.get("ui_code", "")
            
            return code
        except Exception as e:
            logger.error(f"Failed to generate code: {str(e)}")
            return self._get_fallback_code(requirements)
    
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
            logger.error(f"Failed to generate bot code: {str(e)}")
            return ""
    
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
            logger.error(f"Failed to generate config: {str(e)}")
            return ""
    
    async def _generate_api_utils(self, apis: List[Dict]) -> str:
        try:
            # Generate prompt for API utilities
            prompt = f"""Generate utility code for interacting with these APIs:
            {json.dumps(apis, indent=2)}
            
            Generate the API utilities."""
            
            # Get response from LLM
            _, api_utils_str = await self.client.chat_completion(prompt, self.model)
            
            return api_utils_str
        except Exception as e:
            logger.error(f"Failed to generate API utilities: {str(e)}")
            return ""
    
    async def _generate_db_utils(self, database: str) -> str:
        try:
            # Generate prompt for database utilities
            prompt = f"""Generate utility code for interacting with a {database} database for a chatbot.
            
            Generate the database utilities."""
            
            # Get response from LLM
            _, db_utils_str = await self.client.chat_completion(prompt, self.model)
            
            return db_utils_str
        except Exception as e:
            logger.error(f"Failed to generate database utilities: {str(e)}")
            return ""
            
    def _get_fallback_code(self, requirements: Dict) -> Dict[str, str]:
        """Get fallback code templates based on bot type"""
        bot_type = requirements.get("type", "").lower()
        
        # Determine the best template to use
        if "weather" in bot_type:
            template = self.templates["weather"]
        elif any(term in bot_type for term in ["customer", "service", "support", "ticket"]):
            template = self.templates["customer_service"]
        elif any(term in bot_type for term in ["ecommerce", "shop", "store", "commerce"]):
            template = self.templates["ecommerce"]
        else:
            # Default to customer service if unknown
            template = self.templates["customer_service"]
        
        logger.info(f"Using fallback code template for {bot_type} bot")
        return template

class FlowDesigner:
    def __init__(self):
        self.client = None
        self.model = None
        # Templates for fallback when API fails
        self.templates = {
            "weather": {
                "intents": [
                    {"name": "get_weather", "patterns": ["weather in *", "forecast for *", "how's the weather in *"]},
                    {"name": "get_alerts", "patterns": ["alerts in *", "warnings for *", "any severe weather in *"]},
                    {"name": "change_location", "patterns": ["change location to *", "switch to *", "I'm in *"]}
                ],
                "responses": {
                    "get_weather": ["Here's the weather for {location}: {weather_data}", "Current conditions in {location}: {weather_data}"],
                    "get_alerts": ["Current alerts for {location}: {alerts}", "Here are the weather warnings for {location}: {alerts}"],
                    "change_location": ["Location changed to {location}", "I'll show weather for {location} now"]
                },
                "fallbacks": ["I didn't understand that. Could you rephrase?", "I'm not sure what you're asking for."],
                "context_rules": {
                    "location_required": ["get_weather", "get_alerts"],
                    "data_required": ["get_weather"]
                }
            },
            "customer_service": {
                "intents": [
                    {"name": "create_ticket", "patterns": ["create ticket", "new issue", "report problem *"]},
                    {"name": "check_status", "patterns": ["ticket status *", "update on ticket *", "what's happening with *"]},
                    {"name": "faq", "patterns": ["how do I *", "question about *", "help with *"]},
                    {"name": "contact_agent", "patterns": ["speak to agent", "talk to human", "need assistance"]}
                ],
                "responses": {
                    "create_ticket": ["I've created ticket #{ticket_id} for you", "Your issue has been logged with ID #{ticket_id}"],
                    "check_status": ["Ticket #{ticket_id} status: {status}", "Your ticket is currently {status}"],
                    "faq": ["Here's information about {topic}: {info}", "Regarding {topic}: {info}"],
                    "contact_agent": ["Connecting you with an agent...", "I'll transfer you to a human agent now"]
                },
                "fallbacks": ["I'm not sure I understand. Could you try rephrasing that?", "Sorry, I didn't catch that."],
                "context_rules": {
                    "ticket_id_required": ["check_status"],
                    "topic_required": ["faq"],
                    "user_info_required": ["create_ticket"]
                }
            },
            "ecommerce": {
                "intents": [
                    {"name": "search_products", "patterns": ["find *", "search for *", "looking for *"]},
                    {"name": "check_price", "patterns": ["price of *", "how much is *", "cost of *"]},
                    {"name": "check_availability", "patterns": ["is * in stock", "do you have *", "availability of *"]},
                    {"name": "track_order", "patterns": ["track order *", "where is my order *", "shipping status *"]}
                ],
                "responses": {
                    "search_products": ["Here are products matching {query}: {results}", "I found these items for {query}: {results}"],
                    "check_price": ["{product} costs ${price}", "The price of {product} is ${price}"],
                    "check_availability": ["{product} is {availability}", "We {availability_text} {product} in stock"],
                    "track_order": ["Your order #{order_id} is {status}", "Order #{order_id}: {status}"]
                },
                "fallbacks": ["I couldn't find what you're looking for. Could you be more specific?", "I'm not sure I understand what you want."],
                "context_rules": {
                    "product_required": ["check_price", "check_availability"],
                    "order_id_required": ["track_order"],
                    "query_required": ["search_products"]
                }
            }
        }
    
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
                flow = json.loads(flow_str) if isinstance(flow_str, str) else flow_str
                # Basic validation of the flow format
                if not isinstance(flow, dict) or not flow.get("intents"):
                    logger.warning("Flow response missing required fields, using fallback template")
                    return self._get_fallback_template(requirements)
                return flow
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode flow JSON: {str(e)}")
                logger.error(f"Raw flow string: {flow_str}")
                # Use fallback template instead of raising
                return self._get_fallback_template(requirements)
        except Exception as e:
            logger.error(f"Failed to design conversation flow: {str(e)}")
            # Use fallback template instead of raising
            return self._get_fallback_template(requirements)
    
    def _get_fallback_template(self, requirements: Dict) -> Dict:
        """Get a fallback template based on the bot type"""
        bot_type = requirements.get("type", "").lower()
        
        # Determine the best template to use
        if "weather" in bot_type:
            template = self.templates["weather"]
        elif any(term in bot_type for term in ["customer", "service", "support", "ticket"]):
            template = self.templates["customer_service"]
        elif any(term in bot_type for term in ["ecommerce", "shop", "store", "commerce"]):
            template = self.templates["ecommerce"]
        else:
            # Default to customer service if unknown
            template = self.templates["customer_service"]
        
        # Customize template with bot name
        bot_name = requirements.get("name", "Bot")
        customized_template = {**template}
        
        # Add message about using a template
        logger.info(f"Using fallback template for {bot_type} bot named {bot_name}")
        
        return customized_template

class RuleEngine:
    def __init__(self):
        self.client = None
        self.model = None
        # Templates for fallback when API fails
        self.templates = {
            "weather": [
                {"if": "location_not_found", "then": "prompt_for_location", "description": "Ask user for a valid location"},
                {"if": "api_error", "then": "show_error_message", "description": "Display friendly error if weather API fails"},
                {"if": "alerts_exist", "then": "show_alerts_first", "description": "Prioritize alerts in the display"},
                {"if": "location_changed", "then": "clear_previous_data", "description": "Clear previous weather data when location changes"}
            ],
            "customer_service": [
                {"if": "issue_unclear", "then": "ask_clarification", "description": "Ask for more details if issue is unclear"},
                {"if": "high_priority", "then": "escalate_to_agent", "description": "Escalate to human agent for urgent issues"},
                {"if": "faq_match_found", "then": "show_faq", "description": "Show FAQ answer when available"},
                {"if": "similar_issues_exist", "then": "suggest_solutions", "description": "Suggest solutions from similar resolved issues"}
            ],
            "ecommerce": [
                {"if": "product_not_found", "then": "suggest_alternatives", "description": "Suggest alternative products"},
                {"if": "out_of_stock", "then": "offer_notification", "description": "Offer to notify when back in stock"},
                {"if": "cart_abandoned", "then": "send_reminder", "description": "Send reminder for abandoned cart"},
                {"if": "frequent_customer", "then": "apply_discount", "description": "Apply discount for repeat customers"}
            ]
        }
    
    async def generate_rules(self, requirements: Dict) -> List[Dict]:
        """Generate business rules based on requirements"""
        try:
            # Generate prompt for business rules
            prompt = f"""Generate business rules for a bot with these requirements:
            {json.dumps(requirements, indent=2)}
            
            Design the business rules."""
            
            # Get response from LLM
            _, rules_str = await self.client.chat_completion(prompt, self.model)
            
            logger.debug(f"Rules response: {rules_str}")
            
            try:
                rules = json.loads(rules_str) if isinstance(rules_str, str) else rules_str
                # Basic validation
                if not isinstance(rules, (list, dict)) or (isinstance(rules, dict) and not rules.get("conditions")):
                    logger.warning("Rules response missing required fields, using fallback template")
                    return self._get_fallback_template(requirements)
                
                # Handle different formats
                if isinstance(rules, dict) and "conditions" in rules:
                    return rules["conditions"]
                return rules
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode rules JSON: {str(e)}")
                logger.error(f"Raw rules string: {rules_str}")
                # Use fallback template instead of raising
                return self._get_fallback_template(requirements)
        except Exception as e:
            logger.error(f"Failed to generate business rules: {str(e)}")
            # Use fallback template instead of raising
            return self._get_fallback_template(requirements)
    
    def _get_fallback_template(self, requirements: Dict) -> List[Dict]:
        """Get a fallback template based on the bot type"""
        bot_type = requirements.get("type", "").lower()
        
        # Determine the best template to use
        if "weather" in bot_type:
            template = self.templates["weather"]
        elif any(term in bot_type for term in ["customer", "service", "support", "ticket"]):
            template = self.templates["customer_service"]
        elif any(term in bot_type for term in ["ecommerce", "shop", "store", "commerce"]):
            template = self.templates["ecommerce"]
        else:
            # Default to customer service if unknown
            template = self.templates["customer_service"]
        
        logger.info(f"Using fallback template for {bot_type} business rules")
        return template

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