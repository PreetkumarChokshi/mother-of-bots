from flask import Flask, request, jsonify, render_template_string
from clients import bootstrap_rag_client
import tempfile
import os
import asyncio
from functools import partial

app = Flask(__name__)
rag_pipeline = None

# HTML template for the interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Document Chat Interface</title>
    <style>
        body { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
        .chat-container { margin-top: 20px; }
        #chat-messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        .message { margin-bottom: 10px; }
        .user-message { color: blue; }
        .bot-message { color: green; }
        #message-input { width: 80%; padding: 5px; }
        button { padding: 5px 10px; }
        .upload-section { margin-bottom: 20px; padding: 10px; background: #f5f5f5; }
    </style>
</head>
<body>
    <h1>Document Chat Interface</h1>
    
    <div class="upload-section">
        <h2>Upload Documents</h2>
        <form id="upload-form">
            <input type="file" id="documents" name="documents" multiple>
            <button type="submit">Upload</button>
        </form>
        <div id="upload-status"></div>
    </div>

    <div class="chat-container">
        <div id="chat-messages"></div>
        <input type="text" id="message-input" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            if (!message) return;

            // Display user message
            addMessage('User: ' + message, 'user-message');
            input.value = '';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                const data = await response.json();
                addMessage('Bot: ' + data.response, 'bot-message');
            } catch (error) {
                addMessage('Error: ' + error.message, 'error');
            }
        }

        function addMessage(message, className) {
            const messagesDiv = document.getElementById('chat-messages');
            const messageElement = document.createElement('div');
            messageElement.className = 'message ' + className;
            messageElement.textContent = message;
            messagesDiv.appendChild(messageElement);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        document.getElementById('upload-form').onsubmit = async function(e) {
            e.preventDefault();
            const formData = new FormData();
            const files = document.getElementById('documents').files;
            
            for (let file of files) {
                formData.append('documents', file);
            }

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                document.getElementById('upload-status').textContent = 
                    data.status === 'success' ? 'Upload successful!' : 'Upload failed';
            } catch (error) {
                document.getElementById('upload-status').textContent = 
                    'Error uploading files: ' + error.message;
            }
        };

        // Handle Enter key in message input
        document.getElementById('message-input').onkeypress = function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        };
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    global rag_pipeline
    data = request.json
    
    if not rag_pipeline:
        rag_pipeline, _ = bootstrap_rag_client()
    
    # Use synchronous chat instead of async
    try:
        response = rag_pipeline.query(data['message'])
        return jsonify({'response': str(response)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_docs():
    global rag_pipeline
    try:
        files = request.files.getlist('documents')
        
        # Save files temporarily
        file_paths = [save_temp(f) for f in files]
        
        if not rag_pipeline:
            rag_pipeline, _ = bootstrap_rag_client()
        
        rag_pipeline.ingest_documents(file_paths)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def save_temp(file) -> str:
    """Save uploaded file to temporary storage"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp.name)
            return tmp.name
    except Exception as e:
        raise RuntimeError(f"Failed to save file: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True) 