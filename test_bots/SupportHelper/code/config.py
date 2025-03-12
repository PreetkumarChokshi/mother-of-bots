
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
