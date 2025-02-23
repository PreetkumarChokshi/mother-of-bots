import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import logging
from clients import bootstrap_client_and_model
from list_models import list_available_models
from models import ModelOptions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_model' not in st.session_state:
        st.session_state.current_model = "phi4:latest"
    if 'options' not in st.session_state:
        st.session_state.options = ModelOptions()

def get_available_models():
    """Get list of available models from API"""
    try:
        client, _ = bootstrap_client_and_model()
        models = client.get_models()
        return [model.name for model in models]
    except Exception as e:
        st.error(f"Error fetching models: {str(e)}")
        return ["phi-2:latest"]  # fallback

def main():
    st.title("🤖 AI Chat Interface")
    
    # Initialize session state
    init_session_state()
    
    # Sidebar for model selection and parameters
    with st.sidebar:
        st.header("Model Settings")
        
        # Model selection
        models = get_available_models()
        selected_model = st.selectbox(
            "Select Model",
            models,
            index=models.index(st.session_state.current_model) if st.session_state.current_model in models else 0
        )
        
        # Model parameters
        st.subheader("Model Parameters")
        temperature = st.slider("Temperature", 0.0, 1.0, st.session_state.options.temperature or 0.7)
        max_tokens = st.number_input("Max Tokens", 1, 4000, st.session_state.options.max_tokens or 2000)
        top_p = st.slider("Top P", 0.0, 1.0, st.session_state.options.top_p or 0.95)
        context_size = st.number_input("Context Window", 512, 8192, st.session_state.options.context_window_size or 2048)
        
        # Update options
        st.session_state.options = ModelOptions(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            context_window_size=context_size
        )
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    client, model = bootstrap_client_and_model(preferred_model=selected_model)
                    elapsed_time, response = client.chat_completion(prompt, model, st.session_state.options)
                    
                    # Display response
                    st.markdown(response)
                    st.caption(f"Response time: {elapsed_time:.2f}ms")
                    
                    # Add assistant message to chat
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 