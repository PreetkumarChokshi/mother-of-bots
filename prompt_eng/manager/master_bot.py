import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
import logging
import re
from difflib import get_close_matches

from .bot_manager import BotManager
from .requirements_collector import RequirementsCollector
from ..generator import GeneratedBot
from ..agents.models import AIModel, ModelOptions

logger = logging.getLogger(__name__)

class MasterBot:
    """
    Master Bot that serves as the main interface for users to create and manage bots.
    This is the primary class users will interact with to create and manage their bots.
    """
    def __init__(self, storage_dir: str = "generated_bots", use_llm: bool = True):
        self.bot_manager = BotManager(storage_dir)
        self.requirements_collector = RequirementsCollector()
        self.current_conversation = []
        self.initialized = False
        self.conversation_context = {
            "current_action": None,
            "bot_type": None,
            "bot_name": None,
            "features": [],
            "waiting_for": None
        }
        self.use_llm = use_llm
        self.llm_client = None
        self.llm_model = None
        self.system_prompt = """
You are Mother Bot, a master bot creation assistant designed to help users create and manage specialized bots.

Your main capabilities are:
1. Creating new bots based on templates (weather, customer service, e-commerce)
2. Listing existing bots that have been created
3. Providing details about specific bots
4. Updating bots with new features
5. Deleting bots that are no longer needed

When helping users create bots:
- Guide them through the process step by step
- Ask for the type of bot they want to create
- Ask for a name for their bot
- Suggest relevant features based on the bot type
- Confirm before creating the bot

You should maintain context throughout conversations, remembering what stage of creation the user is in.
You should be able to extract meaning from natural language, even if users don't use exact command phrases.
You should be helpful, friendly, and focused on completing the user's task.

Always extract relevant information from user messages and update the conversation context accordingly.
"""
    
    async def initialize(self):
        """Initialize the master bot"""
        if not self.initialized:
            await self.bot_manager.initialize()
            
            # Initialize LLM client if enabled
            if self.use_llm:
                await self._initialize_llm_client()
                
            self.initialized = True
    
    async def _initialize_llm_client(self):
        """Initialize the LLM client for enhanced natural language processing"""
        try:
            # Import here to avoid circular imports
            from ..agents.clients import bootstrap_client_and_model
            
            self.llm_client, self.llm_model = await bootstrap_client_and_model("", "bot management")
            
            # Set system prompt if client supports it
            if hasattr(self.llm_client, 'set_system_prompt'):
                self.llm_client.set_system_prompt(self.system_prompt)
                
            logger.info(f"LLM client initialized with model: {self.llm_model.name if hasattr(self.llm_model, 'name') else self.llm_model.id}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}")
            self.use_llm = False
    
    async def process_message(self, message: str) -> str:
        """
        Process a user message and return a response.
        This is the main entry point for user interaction.
        """
        # Initialize if not already initialized
        if not self.initialized:
            await self.initialize()
        
        # Add message to conversation history
        self.current_conversation.append({"role": "user", "content": message})
        
        # Choose processing method based on LLM availability
        if self.use_llm and self.llm_client:
            response = await self._process_with_llm(message)
        else:
            # Fallback to rule-based processing
            response = await self._process_in_context(message)
        
        # Add response to conversation history
        self.current_conversation.append({"role": "assistant", "content": response})
        
        return response
    
    async def _process_with_llm(self, message: str) -> str:
        """Process the message using LLM for natural language understanding"""
        try:
            # Create a context object with available bots and conversation state
            context = {
                "available_bots": self.bot_manager.list_bots(),
                "current_conversation_context": self.conversation_context,
                "last_messages": self.current_conversation[-min(5, len(self.current_conversation)):],
                "available_actions": [
                    "create_bot", "list_bots", "get_bot_details", 
                    "update_bot", "delete_bot", "help"
                ]
            }
            
            # Create a prompt that includes context and the user's message
            prompt = f"""
Current context: {json.dumps(context, indent=2)}

Based on this context and the user's message: "{message}"

1. Determine the user's intent
2. Extract any relevant entities (bot names, features, etc.)
3. Decide what action to take

Please respond in this format:
INTENT: [detected intent]
ENTITIES: [extracted entities as JSON]
ACTION: [action to take]
RESPONSE: [your final response to the user]
"""
            
            # Get LLM response
            _, llm_response = await self.llm_client.chat_completion(prompt, self.llm_model)
            
            # Extract action and response from LLM output
            action = None
            entities = {}
            response = llm_response
            
            # Parse the LLM response to extract structured information
            try:
                intent_match = re.search(r"INTENT:\s*(.+)", llm_response)
                entities_match = re.search(r"ENTITIES:\s*(\{.+\})", llm_response, re.DOTALL)
                action_match = re.search(r"ACTION:\s*(.+)", llm_response)
                response_match = re.search(r"RESPONSE:\s*(.+)", llm_response, re.DOTALL)
                
                if intent_match:
                    intent = intent_match.group(1).strip()
                    
                    # Update conversation context based on intent
                    if "create" in intent.lower() and "bot" in intent.lower():
                        self.conversation_context["current_action"] = "create_bot"
                    
                if entities_match:
                    try:
                        entities = json.loads(entities_match.group(1))
                        
                        # Update conversation context with extracted entities
                        if "bot_type" in entities:
                            self.conversation_context["bot_type"] = entities["bot_type"]
                        if "bot_name" in entities:
                            self.conversation_context["bot_name"] = entities["bot_name"]
                        if "features" in entities and isinstance(entities["features"], list):
                            self.conversation_context["features"] = entities["features"]
                        if "waiting_for" in entities:
                            self.conversation_context["waiting_for"] = entities["waiting_for"]
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse entities from LLM response")
                
                if action_match:
                    action = action_match.group(1).strip()
                
                if response_match:
                    response = response_match.group(1).strip()
            except Exception as e:
                logger.error(f"Error parsing LLM response: {str(e)}")
            
            # Execute the appropriate action if one was determined
            if action:
                if action == "create_bot" and self.conversation_context.get("bot_name") and self.conversation_context.get("bot_type"):
                    try:
                        creation_result = await self._create_bot_from_context()
                        # Only use the creation result if it's successful
                        if "I've created" in creation_result:
                            return creation_result
                    except Exception as e:
                        logger.error(f"Error executing create_bot action: {str(e)}")
                
                elif action == "list_bots":
                    return self._handle_list_bots()
                
                elif action == "get_bot_details" and "bot_name" in entities:
                    return self._handle_bot_details(entities["bot_name"])
                
                elif action == "delete_bot" and "bot_name" in entities:
                    return await self._handle_bot_deletion(entities["bot_name"])
                
                elif action == "update_bot" and "bot_name" in entities:
                    return await self._handle_bot_update(message, entities["bot_name"])
                
                elif action == "help":
                    return self._handle_help()
                
                # Continue with contextual conversation
                elif self.conversation_context["waiting_for"] == "bot_type":
                    return await self._handle_bot_type_selection(message)
                elif self.conversation_context["waiting_for"] == "bot_name":
                    return await self._handle_bot_name_selection(message)
                elif self.conversation_context["waiting_for"] == "features":
                    return await self._handle_features_selection(message)
                elif self.conversation_context["waiting_for"] == "confirmation":
                    return await self._handle_bot_creation_confirmation(message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message with LLM: {str(e)}")
            # Fallback to rule-based processing
            return await self._process_in_context(message)
    
    async def _process_in_context(self, message: str) -> str:
        """Process the message in the context of the current conversation"""
        message_lower = message.lower()
        
        # Check if we're waiting for specific input
        if self.conversation_context["waiting_for"] == "bot_type":
            return await self._handle_bot_type_selection(message)
        elif self.conversation_context["waiting_for"] == "bot_name":
            return await self._handle_bot_name_selection(message)
        elif self.conversation_context["waiting_for"] == "features":
            return await self._handle_features_selection(message)
        elif self.conversation_context["waiting_for"] == "confirmation":
            return await self._handle_bot_creation_confirmation(message)
        
        # Otherwise, detect intent from message
        return await self._handle_user_request(message)
    
    async def _handle_user_request(self, message: str) -> str:
        """Handle a user request based on intent detection"""
        message_lower = message.lower()
        
        # Intent detection with more flexible matching
        
        # Create bot intent
        create_patterns = ["create", "make", "build", "generate", "new"]
        if any(pattern in message_lower for pattern in create_patterns) and "bot" in message_lower:
            # Reset conversation context
            self.conversation_context = {
                "current_action": "create_bot",
                "bot_type": None,
                "bot_name": None,
                "features": [],
                "waiting_for": None
            }
            
            # Check if message contains bot type
            bot_types = ["weather", "customer service", "ecommerce", "shopping"]
            for bot_type in bot_types:
                if bot_type in message_lower:
                    self.conversation_context["bot_type"] = bot_type.replace("shopping", "ecommerce")
                    
                    # Check if message contains bot name
                    name_match = re.search(r"(?:called|named)\s+(\w+)", message_lower)
                    if name_match:
                        self.conversation_context["bot_name"] = name_match.group(1)
                    
                    # Check for features
                    features_match = re.search(r"with\s+([\w\s,]+)(?:\s+features?)?", message_lower)
                    if features_match:
                        features = [f.strip() for f in features_match.group(1).split(',')]
                        self.conversation_context["features"] = features
                    
                    # If we have all information, create the bot
                    if self.conversation_context["bot_name"]:
                        return await self._create_bot_from_context()
                    else:
                        self.conversation_context["waiting_for"] = "bot_name"
                        return f"Great! Let's create a {bot_type} bot. What would you like to call it?"
                    
            # If no bot type found, ask for it
            self.conversation_context["waiting_for"] = "bot_type"
            return """I'd be happy to create a bot for you! What type of bot would you like?

1. Weather Bot - for weather forecasts and alerts
2. Customer Service Bot - for handling customer inquiries and support
3. E-commerce Bot - for product searches and recommendations

You can say something like "Weather bot" or just "1" for the first option."""
        
        # List bots intent
        list_patterns = ["list", "show", "display", "get"]
        if any(pattern in message_lower for pattern in list_patterns) and (
           "bot" in message_lower or "all" in message_lower):
            return self._handle_list_bots()
        
        # Bot details intent
        details_patterns = ["details", "info", "about", "tell me about"]
        if any(pattern in message_lower for pattern in details_patterns) and "bot" in message_lower:
            # Try to extract bot name
            bot_name = self._extract_bot_name_from_message(message)
            if bot_name:
                return self._handle_bot_details(bot_name)
            else:
                return "Which bot would you like details about? Please provide the name."
        
        # Delete bot intent
        delete_patterns = ["delete", "remove", "destroy"]
        if any(pattern in message_lower for pattern in delete_patterns) and "bot" in message_lower:
            bot_name = self._extract_bot_name_from_message(message)
            if bot_name:
                return await self._handle_bot_deletion(bot_name)
            else:
                return "Which bot would you like to delete? Please provide the name."
        
        # Update bot intent
        update_patterns = ["update", "modify", "change", "upgrade"]
        if any(pattern in message_lower for pattern in update_patterns) and "bot" in message_lower:
            bot_name = self._extract_bot_name_from_message(message)
            if bot_name:
                return await self._handle_bot_update(message, bot_name)
            else:
                return "Which bot would you like to update? Please provide the name."
        
        # Help intent
        help_patterns = ["help", "guide", "info", "how to"]
        if any(pattern in message_lower for pattern in help_patterns):
            return self._handle_help()
        
        # Check if the message might be a response to a previous question
        if self.current_conversation and len(self.current_conversation) >= 2:
            previous_response = self.current_conversation[-2]["content"].lower()
            if "what type of bot" in previous_response:
                return await self._handle_bot_type_selection(message)
            elif "what would you like to call" in previous_response:
                return await self._handle_bot_name_selection(message)
        
        # Default response with more helpful suggestions
        return self._handle_default(message)
    
    def _extract_bot_name_from_message(self, message: str) -> Optional[str]:
        """Extract a bot name from the message"""
        message_lower = message.lower()
        
        # Try different regex patterns
        patterns = [
            r"(?:bot|for)\s+(?:named|called)?\s*[\"']?([a-zA-Z0-9_]+)[\"']?",
            r"(?:named|called)\s+[\"']?([a-zA-Z0-9_]+)[\"']?",
            r"[\"']([a-zA-Z0-9_]+)[\"']\s+bot",
            r"details\s+(?:for|about)\s+[\"']?([a-zA-Z0-9_]+)[\"']?",
            r"(?:delete|remove|update|modify)\s+[\"']?([a-zA-Z0-9_]+)[\"']?"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1)
        
        # If no match found, check if any bot name is in the message
        bot_names = self.bot_manager.list_bots()
        for name in bot_names:
            if name.lower() in message_lower:
                return name
        
        return None
    
    async def _handle_bot_type_selection(self, message: str) -> str:
        """Handle bot type selection"""
        message_lower = message.strip().lower()
        
        # Handle numeric selection
        if message_lower in ["1", "one", "first"]:
            self.conversation_context["bot_type"] = "weather"
        elif message_lower in ["2", "two", "second"]:
            self.conversation_context["bot_type"] = "customer_service"
        elif message_lower in ["3", "three", "third"]:
            self.conversation_context["bot_type"] = "ecommerce"
        # Handle text selection
        elif "weather" in message_lower:
            self.conversation_context["bot_type"] = "weather"
        elif "customer" in message_lower or "service" in message_lower or "support" in message_lower:
            self.conversation_context["bot_type"] = "customer_service"
        elif "ecommerce" in message_lower or "shop" in message_lower or "store" in message_lower:
            self.conversation_context["bot_type"] = "ecommerce"
        else:
            # Try to find closest match
            options = ["weather", "customer service", "ecommerce"]
            matches = get_close_matches(message_lower, options, n=1, cutoff=0.6)
            if matches:
                self.conversation_context["bot_type"] = matches[0]
            else:
                return """I didn't recognize that bot type. Please choose one of the following:

1. Weather Bot
2. Customer Service Bot
3. E-commerce Bot

Or just say "Weather" for example."""
        
        # Ask for the bot name
        self.conversation_context["waiting_for"] = "bot_name"
        return f"Great! Let's create a {self.conversation_context['bot_type']} bot. What would you like to call it?"
    
    async def _handle_bot_name_selection(self, message: str) -> str:
        """Handle bot name selection"""
        name = message.strip()
        if not name:
            return "Please provide a name for your bot."
        
        self.conversation_context["bot_name"] = name
        
        # Ask about features if none were provided initially
        if not self.conversation_context["features"]:
            self.conversation_context["waiting_for"] = "features"
            bot_type = self.conversation_context["bot_type"]
            
            if bot_type == "weather":
                return f"Would you like to add any special features to your {name} weather bot? For example: historical data, severe weather alerts, or hourly forecasts."
            elif bot_type == "customer_service":
                return f"Would you like to add any special features to your {name} customer service bot? For example: ticket creation, FAQ search, or order tracking."
            else:  # ecommerce
                return f"Would you like to add any special features to your {name} e-commerce bot? For example: product recommendations, inventory checking, or price alerts."
        else:
            # If we already have features, ask for confirmation
            self.conversation_context["waiting_for"] = "confirmation"
            features_text = ", ".join(self.conversation_context["features"])
            return f"I'll create a {self.conversation_context['bot_type']} bot named {name} with these features: {features_text}. Should I proceed? (yes/no)"
    
    async def _handle_features_selection(self, message: str) -> str:
        """Handle features selection"""
        message_lower = message.lower()
        
        # Check for no features or skip
        if message_lower in ["no", "none", "skip", "no features"]:
            self.conversation_context["features"] = []
            self.conversation_context["waiting_for"] = "confirmation"
            return f"I'll create a {self.conversation_context['bot_type']} bot named {self.conversation_context['bot_name']} with default features. Should I proceed? (yes/no)"
        
        # Extract features from message
        features = []
        for feature in re.findall(r"[\w\s-]+", message):
            feature = feature.strip()
            if feature and len(feature) > 2:  # Ignore very short words
                features.append(feature)
        
        if features:
            self.conversation_context["features"] = features
            self.conversation_context["waiting_for"] = "confirmation"
            features_text = ", ".join(features)
            return f"I'll create a {self.conversation_context['bot_type']} bot named {self.conversation_context['bot_name']} with these features: {features_text}. Should I proceed? (yes/no)"
        else:
            return "I didn't catch any features. Please list them separated by commas, or say 'none' to skip."
    
    async def _handle_bot_creation_confirmation(self, message: str) -> str:
        """Handle bot creation confirmation"""
        message_lower = message.lower()
        
        if message_lower in ["yes", "y", "sure", "ok", "proceed", "create", "go ahead"]:
            return await self._create_bot_from_context()
        else:
            self.conversation_context = {
                "current_action": None,
                "bot_type": None,
                "bot_name": None,
                "features": [],
                "waiting_for": None
            }
            return "Bot creation cancelled. How else can I help you?"
    
    async def _create_bot_from_context(self) -> str:
        """Create a bot using the current conversation context"""
        try:
            bot_type = self.conversation_context["bot_type"]
            if not bot_type:
                return "I'm not sure what type of bot you want to create. Please specify weather, customer service, or e-commerce."
            
            # Convert to template name
            template_name = bot_type
            if "customer" in bot_type.lower():
                template_name = "customer_service"
            elif "shop" in bot_type.lower() or "store" in bot_type.lower():
                template_name = "ecommerce"
            
            self.requirements_collector.set_from_template(template_name)
            
            # Set bot name
            if self.conversation_context["bot_name"]:
                self.requirements_collector.set_name(self.conversation_context["bot_name"])
            
            # Add features
            for feature in self.conversation_context["features"]:
                self.requirements_collector.add_feature(feature)
            
            # Validate requirements
            errors = self.requirements_collector.validate()
            if errors:
                return f"There are some issues with your bot requirements: {', '.join(errors)}"
            
            # Create the bot
            requirements = self.requirements_collector.get_requirements()
            bot = await self.bot_manager.create_bot(requirements)
            
            # Reset context
            self.conversation_context = {
                "current_action": None,
                "bot_type": None,
                "bot_name": None,
                "features": [],
                "waiting_for": None
            }
            
            # Return success message
            return f"I've created a {template_name} bot called '{bot.name}' for you! It includes {len(bot.code)} code files with {len(bot.conversation_flow['intents'])} intents and {len(bot.business_rules)} business rules."
        
        except Exception as e:
            logger.error(f"Bot creation failed: {str(e)}")
            return f"I ran into an issue creating your bot. Error: {str(e)}"
    
    async def _handle_bot_creation(self, message: str) -> str:
        """Legacy handler for bot creation - keeping for backward compatibility"""
        message_lower = message.lower()
        
        # Check for template usage
        template_match = re.search(r"(weather|customer_service|ecommerce)(?:\s+bot)?", message_lower)
        if template_match:
            template_name = template_match.group(1)
            try:
                self.requirements_collector.set_from_template(template_name)
                
                # Check for custom name
                name_match = re.search(r"call(ed|ing)?\s+it\s+(\w+)", message_lower)
                if name_match:
                    self.requirements_collector.set_name(name_match.group(2))
                
                # Extract additional features
                features_match = re.search(r"with\s+([\w\s,]+)(\s+features?)?", message_lower)
                if features_match:
                    features = features_match.group(1).split(',')
                    for feature in features:
                        feature = feature.strip()
                        if feature:
                            self.requirements_collector.add_feature(feature)
                
                # Validate requirements
                errors = self.requirements_collector.validate()
                if errors:
                    return f"There are some issues with your bot requirements: {', '.join(errors)}"
                
                # Create the bot
                requirements = self.requirements_collector.get_requirements()
                bot = await self.bot_manager.create_bot(requirements)
                
                return f"I've created a {template_name} bot called '{bot.name}' for you. It includes {len(bot.code)} code files with {len(bot.conversation_flow['intents'])} intents and {len(bot.business_rules)} business rules."
            
            except Exception as e:
                logger.error(f"Bot creation failed: {str(e)}")
                return f"I couldn't create the bot. Error: {str(e)}"
        else:
            return """I'd be happy to create a bot for you! What type of bot would you like to create? Here are some templates I have available:
            
1. Weather Bot - for weather forecasts and alerts
2. Customer Service Bot - for handling customer inquiries and support
3. E-commerce Bot - for product searches and recommendations

For example, you could say "Create a weather bot called MyWeatherApp with historical data features" """
    
    def _handle_list_bots(self) -> str:
        """Handle request to list all bots"""
        bots = self.bot_manager.list_bots()
        if not bots:
            return "You don't have any bots yet. You can create one by saying 'Create a new bot'"
        
        bot_list = "\n".join([f"- {name}" for name in bots])
        return f"Here are your bots:\n{bot_list}"
    
    def _handle_bot_details(self, bot_name: str) -> str:
        """Handle request for bot details"""
        bot = self.bot_manager.get_bot(bot_name)
        if not bot:
            # Try to find a similar bot name
            bot_names = self.bot_manager.list_bots()
            matches = get_close_matches(bot_name, bot_names, n=1, cutoff=0.6)
            if matches:
                suggested_name = matches[0]
                bot = self.bot_manager.get_bot(suggested_name)
                if bot:
                    details = [
                        f"I found a similar bot named '{suggested_name}'. Here are its details:",
                        f"Bot Name: {bot.name}",
                        f"Code Files: {', '.join(bot.code.keys())}",
                        f"Intents: {', '.join([intent['name'] for intent in bot.conversation_flow.get('intents', [])])}",
                        f"Business Rules: {len(bot.business_rules)}"
                    ]
                    return "\n".join(details)
            
            return f"I couldn't find a bot named '{bot_name}'. Use 'List bots' to see your available bots."
        
        # Build details
        details = [
            f"Bot Name: {bot.name}",
            f"Code Files: {', '.join(bot.code.keys())}",
            f"Intents: {', '.join([intent['name'] for intent in bot.conversation_flow.get('intents', [])])}",
            f"Business Rules: {len(bot.business_rules)}"
        ]
        
        return "\n".join(details)
    
    async def _handle_bot_deletion(self, bot_name: str) -> str:
        """Handle request to delete a bot"""
        success = self.bot_manager.delete_bot(bot_name)
        if success:
            return f"I've deleted the bot '{bot_name}'."
        else:
            # Try to find a similar bot name
            bot_names = self.bot_manager.list_bots()
            matches = get_close_matches(bot_name, bot_names, n=1, cutoff=0.6)
            if matches:
                suggested_name = matches[0]
                return f"I couldn't find a bot named '{bot_name}'. Did you mean '{suggested_name}'? You can say 'Delete {suggested_name}' to delete it."
            
            return f"I couldn't find a bot named '{bot_name}'. Use 'List bots' to see your available bots."
    
    async def _handle_bot_update(self, message: str, bot_name: str) -> str:
        """Handle request to update a bot"""
        bot = self.bot_manager.get_bot(bot_name)
        if not bot:
            # Try to find a similar bot name
            bot_names = self.bot_manager.list_bots()
            matches = get_close_matches(bot_name, bot_names, n=1, cutoff=0.6)
            if matches:
                suggested_name = matches[0]
                return f"I couldn't find a bot named '{bot_name}'. Did you mean '{suggested_name}'? You can say 'Update {suggested_name}' to update it."
            
            return f"I couldn't find a bot named '{bot_name}'. Use 'List bots' to see your available bots."
        
        message_lower = message.lower()
        
        # Extract update requirements
        feature_match = re.search(r"add(?:ing)?\s+([\w\s]+)(?:\s+feature)?", message_lower)
        if feature_match:
            # Get current requirements
            requirements = self.requirements_collector.get_requirements()
            
            # Add the new feature
            new_feature = feature_match.group(1).strip()
            if new_feature not in requirements["features"]:
                requirements["features"].append(new_feature)
            
            # Update the bot
            updated_bot = await self.bot_manager.update_bot(bot_name, requirements)
            
            return f"I've updated '{bot_name}' to include the '{new_feature}' feature."
        else:
            return f"What would you like to update about '{bot_name}'? For example, you could say 'Update {bot_name} to add historical data feature'"
    
    def _handle_help(self) -> str:
        """Handle help request"""
        help_text = """
I'm a Master Bot that can help you create and manage other bots. Here's what I can do:

- Create a new bot: "Create a weather bot called MyWeatherApp"
- List your bots: "List all my bots"
- Get bot details: "Show me details for WeatherBot"
- Update a bot: "Update WeatherBot to add historical data feature"
- Delete a bot: "Delete WeatherBot"

I have templates for weather bots, customer service bots, and e-commerce bots to help you get started quickly.

To create a bot, you can:
1. Simply say "Create a new bot" and I'll guide you through the process
2. Say "Create a weather bot called RainAlert with alerts feature"
3. Ask for "Help with creating a bot" for more guidance
"""
        return help_text
    
    def _handle_default(self, message: str) -> str:
        """Handle default case when no intent is matched"""
        message_lower = message.lower()
        
        # Check if the message might be asking about a specific bot type
        bot_types = ["weather", "customer service", "ecommerce", "shopping"]
        for bot_type in bot_types:
            if bot_type in message_lower:
                return f"It sounds like you're interested in a {bot_type} bot. You can say 'Create a {bot_type} bot' to get started, or 'Tell me more about {bot_type} bots' for more information."
        
        # Check if message looks like a question
        if message.endswith("?") or message_lower.startswith(("what", "how", "can", "do", "will")):
            return """I can help you create and manage bots. Here are some things I can help with:

- Creating new bots with different templates and features
- Listing your existing bots
- Getting details about specific bots
- Updating bots with new features
- Deleting bots you no longer need

What would you like to do today?"""
        
        # Default fallback
        return """I'm not sure what you're asking for. I can help you create and manage bots. Try asking:
        
- "Create a new bot" 
- "List all my bots"
- "Show me details for a bot"
- "Help" for more options
"""

# Example usage
if __name__ == "__main__":
    async def test():
        master_bot = MasterBot()
        await master_bot.initialize()
        
        # Test conversation
        responses = []
        responses.append(await master_bot.process_message("Help"))
        responses.append(await master_bot.process_message("Create a weather bot called MyWeatherBot"))
        responses.append(await master_bot.process_message("List my bots"))
        responses.append(await master_bot.process_message("Show me details for MyWeatherBot"))
        
        for response in responses:
            print("\nBOT:", response)
    
    asyncio.run(test()) 