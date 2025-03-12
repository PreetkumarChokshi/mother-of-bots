import json
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RequirementsCollector:
    """
    Helper class to collect and validate bot requirements from user input.
    This provides a structured way to gather all the necessary information to create a bot.
    """
    def __init__(self):
        self.requirements = {
            "name": "",
            "type": "",
            "features": [],
            "platform": "",
            "language": "python",
            "apis": [],
            "async_support": False,
            "database": None,
            "error_handling": True,
            "ui_preferences": {},
        }
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined bot templates"""
        return {
            "weather": {
                "name": "WeatherBot",
                "type": "weather",
                "features": ["daily_forecast", "location_based", "alerts"],
                "platform": "web",
                "apis": [
                    {
                        "name": "OpenWeatherMap",
                        "version": "2.5",
                        "endpoints": ["current", "forecast", "alerts"]
                    }
                ],
                "language": "python",
                "async_support": True,
                "database": "sqlite",
                "ui_preferences": {
                    "design": "modern",
                    "theme": "light",
                    "components": ["search", "forecast_display", "alerts_panel"]
                }
            },
            "customer_service": {
                "name": "CustomerServiceBot",
                "type": "customer_service",
                "features": ["faq", "ticket_creation", "order_status"],
                "platform": "chat",
                "apis": [
                    {
                        "name": "CRM API",
                        "endpoints": ["customer", "order", "ticket"]
                    }
                ],
                "language": "python",
                "async_support": True,
                "database": "mongodb",
                "ui_preferences": {
                    "design": "clean",
                    "theme": "corporate",
                    "components": ["chat_window", "knowledge_base", "ticket_form"]
                }
            },
            "ecommerce": {
                "name": "ShoppingBot",
                "type": "ecommerce",
                "features": ["product_search", "recommendations", "cart_management"],
                "platform": "web",
                "apis": [
                    {
                        "name": "E-commerce API",
                        "endpoints": ["products", "cart", "checkout"]
                    }
                ],
                "language": "python",
                "async_support": True,
                "database": "postgresql",
                "ui_preferences": {
                    "design": "responsive",
                    "theme": "shop",
                    "components": ["product_gallery", "cart_summary", "checkout_form"]
                }
            }
        }
    
    def set_from_template(self, template_name: str) -> Dict[str, Any]:
        """Use a predefined template as a starting point"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found. Available templates: {list(self.templates.keys())}")
        
        self.requirements = self.templates[template_name].copy()
        return self.requirements
    
    def set_name(self, name: str) -> None:
        """Set the bot name"""
        self.requirements["name"] = name.strip()
    
    def set_type(self, bot_type: str) -> None:
        """Set the bot type (e.g., weather, customer_service, ecommerce)"""
        self.requirements["type"] = bot_type.strip().lower()
    
    def add_feature(self, feature: str) -> None:
        """Add a feature to the bot"""
        if feature not in self.requirements["features"]:
            self.requirements["features"].append(feature.strip())
    
    def remove_feature(self, feature: str) -> None:
        """Remove a feature from the bot"""
        if feature in self.requirements["features"]:
            self.requirements["features"].remove(feature)
    
    def set_platform(self, platform: str) -> None:
        """Set the platform (e.g., web, mobile, chat)"""
        self.requirements["platform"] = platform.strip().lower()
    
    def set_language(self, language: str) -> None:
        """Set the programming language"""
        self.requirements["language"] = language.strip().lower()
    
    def add_api(self, name: str, version: Optional[str] = None, endpoints: Optional[List[str]] = None) -> None:
        """Add an API to the bot"""
        api = {"name": name}
        if version:
            api["version"] = version
        if endpoints:
            api["endpoints"] = endpoints
        
        # Check if API already exists, and update if so
        for i, existing_api in enumerate(self.requirements["apis"]):
            if existing_api["name"] == name:
                self.requirements["apis"][i] = api
                return
        
        # Otherwise add the new API
        self.requirements["apis"].append(api)
    
    def remove_api(self, name: str) -> None:
        """Remove an API from the bot"""
        self.requirements["apis"] = [api for api in self.requirements["apis"] if api["name"] != name]
    
    def set_async_support(self, async_support: bool) -> None:
        """Set whether the bot should support async operations"""
        self.requirements["async_support"] = bool(async_support)
    
    def set_database(self, database: Optional[str]) -> None:
        """Set the database to use (e.g., sqlite, mongodb, postgresql)"""
        self.requirements["database"] = database
    
    def set_error_handling(self, error_handling: bool) -> None:
        """Set whether the bot should include error handling"""
        self.requirements["error_handling"] = bool(error_handling)
    
    def set_ui_preference(self, key: str, value: Any) -> None:
        """Set a UI preference"""
        if "ui_preferences" not in self.requirements:
            self.requirements["ui_preferences"] = {}
        self.requirements["ui_preferences"][key] = value
    
    def validate(self) -> List[str]:
        """Validate the requirements and return a list of any errors"""
        errors = []
        
        # Check required fields
        if not self.requirements["name"]:
            errors.append("Bot name is required")
        if not self.requirements["type"]:
            errors.append("Bot type is required")
        if not self.requirements["features"]:
            errors.append("At least one feature is required")
        if not self.requirements["platform"]:
            errors.append("Platform is required")
        
        return errors
    
    def get_requirements(self) -> Dict[str, Any]:
        """Get the complete requirements"""
        return self.requirements.copy()
    
    def load_from_json(self, json_str: str) -> None:
        """Load requirements from a JSON string"""
        try:
            data = json.loads(json_str)
            self.requirements.update(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            raise ValueError(f"Invalid JSON: {str(e)}")
    
    def to_json(self) -> str:
        """Convert requirements to a JSON string"""
        return json.dumps(self.requirements, indent=2)

# Example usage
if __name__ == "__main__":
    collector = RequirementsCollector()
    collector.set_from_template("weather")
    collector.set_name("MyCustomWeatherBot")
    collector.add_feature("historical_data")
    collector.set_ui_preference("theme", "dark")
    
    print(collector.to_json())
    errors = collector.validate()
    if errors:
        print("Validation errors:", errors)
    else:
        print("Requirements are valid") 