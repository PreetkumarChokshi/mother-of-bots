import os
import json
from typing import Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables or config file"""
    # For testing, return mock config
    if os.getenv("TEST_MODE") == "true":
        return {
            "chatbot_api_host": "mock",
            "bearer": "mock"
        }
    
    # Try to load from agents/config.cfg first (your existing config)
    agents_config_path = Path(__file__).parent.parent / "agents" / "config.cfg"
    if agents_config_path.exists():
        try:
            config = {}
            with open(agents_config_path, "r") as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        config[key.strip()] = value.strip()
            
            logger.info(f"Loaded config from {agents_config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config from {agents_config_path}: {e}")
    
    # Try to load from config file as a fallback
    config_path = os.getenv("CONFIG_PATH", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
    
    # Fallback to environment variables
    return {
        "chatbot_api_host": os.getenv("CHATBOT_API_HOST", "localhost:11434"),
        "bearer": os.getenv("BEARER_TOKEN", "")
    } 