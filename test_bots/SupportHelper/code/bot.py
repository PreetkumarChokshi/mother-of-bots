
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
