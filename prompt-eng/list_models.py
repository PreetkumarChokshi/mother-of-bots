import requests
import logging
from config import config_factory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_available_models():
    """List all available models from the API"""
    try:
        # Get configuration
        config = config_factory()
        host = config["chatbot_api_host"]
        bearer = config["bearer"]

        # First try Ollama endpoint
        try:
            url = f"http://{host}/api/tags"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                print("\n=== Available Models (Ollama) ===")
                for model in data["models"]:
                    name = model["name"]
                    size = model.get("details", {}).get("parameter_size", "Unknown")
                    print(f"- {name} ({size})")
                return
        except Exception as e:
            logger.debug(f"Not an Ollama endpoint: {str(e)}")

        # Try OpenWebUI endpoint
        url = f"https://{host}/api/models"
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print("\n=== Available Models (OpenWebUI) ===")
        for model in data["data"]:
            name = model["name"]
            try:
                size = model["ollama"]["details"]["parameter_size"]
            except KeyError:
                size = "Unknown"
            print(f"- {name} ({size})")

    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}", exc_info=True)
        print(f"\n❌ An error occurred: {str(e)}")
    finally:
        print("=====================")

if __name__ == "__main__":
    list_available_models() 