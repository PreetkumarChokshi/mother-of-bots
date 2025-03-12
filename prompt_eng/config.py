import os
from pathlib import Path

def config_factory():
    """Create configuration with default values"""
    config = {
        "chatbot_api_host": os.getenv("CHATBOT_API_HOST", "localhost:11434"),  # Default Ollama port
        "bearer": os.getenv("BEARER_TOKEN", ""),  # For OpenWebUI authentication
        "model_preferences": {
            "code": ["codellama", "deepseek-coder", "wizard-coder"],
            "creative": ["mistral", "llama2"],
            "math": ["qwen", "deepseek", "mixtral"],
            "large_context": ["claude", "mixtral", "qwen"]
        }
    }
    
    # Load from config file if exists
    config_path = Path(__file__).parent / "config.cfg"
    if config_path.exists():
        with open(config_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    config[key.strip()] = value.strip()
    
    return config 