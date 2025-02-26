
from flask import Flask, request, jsonify, render_template_string
import logging
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Configuration
class BotConfig:
    BOT_NAME = "bot_0"
    MODEL = "llava"
    PERSONALITY = "technincal"
    API_HOST = "chat.hpc.fau.edu"
    BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Ijg4OTE4MWNlLWIxNTEtNDU4Ni05NzBiLWQwNjVlZDRkY2U0NyJ9.XkWF8CNuoS5a-ruELxuzT4NfT9G7LKVmeLDVqq2BAFU"

class ChatAPI:
    @staticmethod
    def get_response(message: str) -> str:
        """Get response from AI model API"""
        try:
            headers = {
                "Authorization": f"Bearer {BotConfig.BEARER_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # First try OpenWebUI endpoint
            url = f"https://{BotConfig.API_HOST}/api/chat/completions"
            payload = {
                "messages": [
                    {"role": "system", "content": f"You are {BotConfig.PERSONALITY}. Respond accordingly."},
                    {"role": "user", "content": message}
                ],
                "model": BotConfig.MODEL,
                "stream": False
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            
            # If OpenWebUI fails, try Ollama endpoint
            url = f"http://{BotConfig.API_HOST}/api/chat"
            payload = {
                "model": BotConfig.MODEL,
                "messages": [
                    {"role": "system", "content": f"You are {BotConfig.PERSONALITY}. Respond accordingly."},
                    {"role": "user", "content": message}
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()['message']['content']
            
            raise Exception(f"API request failed with status code: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error calling AI API: {str(e)}")
            return f"Error: {str(e)}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ bot_name }} - Chat Interface</title>
    <style>
        body { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
        .chat-container { margin-top: 20px; }
        #chat-messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }
        .message { margin-bottom: 10px; }
        .user-message { color: blue; }
        .bot-message { color: green; }
    </style>
</head>
<body>
    <h1>{{ bot_name }} ({{ personality }})</h1>
    <div class="chat-container">
        <div id="chat-messages"></div>
        <input type="text" id="message-input" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        async function sendMessage() {
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML += '<div class="message user-message">You: ' + message + '</div>';
            messageInput.value = '';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                const data = await response.json();
                messagesDiv.innerHTML += '<div class="message bot-message">Bot: ' + data.response + '</div>';
            } catch (error) {
                messagesDiv.innerHTML += '<div class="message error">Error: ' + error.message + '</div>';
            }
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, 
                                bot_name=BotConfig.BOT_NAME,
                                personality=BotConfig.PERSONALITY)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message', '')
        response = ChatAPI.get_response(message)
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
