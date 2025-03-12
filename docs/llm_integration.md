# LLM Integration with Master Bot

This document describes how the Mother of Bots framework integrates with Large Language Models (LLMs) to provide enhanced natural language understanding capabilities.

## Overview

The Master Bot can operate in two modes:
1. **Rule-based mode**: Uses pre-defined patterns and rules for understanding user requests
2. **LLM-powered mode**: Uses an LLM API to interpret user messages more naturally

The LLM integration enables:
- Better understanding of natural language inputs
- Context-aware conversations
- More flexible entity extraction
- Enhanced response generation

## How It Works

The Master Bot uses a structured approach to integrating with LLMs:

1. **Context Building**: Builds a context object containing the current conversation state, available bots, and other relevant information
2. **Prompt Generation**: Creates a structured prompt for the LLM with specific instructions
3. **Response Parsing**: Parses the LLM response to extract intent, entities, and actions
4. **Action Execution**: Uses the detected intent and entities to perform the appropriate action
5. **Fallback Handling**: Falls back to rule-based processing if LLM processing fails

## Implementation Details

### Context Object

The context object includes:
- `available_bots`: List of available bots
- `current_conversation_context`: Current state of the conversation
- `last_messages`: Last few messages in the conversation
- `available_actions`: Actions the Master Bot can perform

### Prompt Template

The prompt template instructs the LLM to:
1. Determine the user's intent
2. Extract relevant entities (bot names, features, etc.)
3. Decide what action to take
4. Provide a natural language response

The prompt specifies a structured response format with `INTENT`, `ENTITIES`, `ACTION`, and `RESPONSE` sections.

### Client Configuration

The MasterBot can use different LLM clients:
- `OpenWebUIClient`: For API endpoints like FAU's chat.hpc.fau.edu
- `OllamaClient`: For local Ollama instances
- `MockChatbotClient`: For testing without an actual LLM

## Setting Up LLM Integration

### Configuration File

Create a `config.cfg` file in the `prompt_eng/agents/` directory:
```
[DEFAULT]
chatbot_api_host = your_llm_api_host
bearer = your_api_token
```

### Running with LLM Integration

By default, LLM integration is enabled. To disable it, use the `--no-llm` flag:
```bash
python prompt_eng/cli.py --no-llm
```

For testing with mock LLM responses:
```bash
python prompt_eng/cli.py --test-mode
```

### System Prompt

The LLM uses a system prompt that defines its role and capabilities. This can be customized in the `MasterBot` class initialization.

## Testing and Debugging

For debugging LLM interactions, use the `--debug` flag:
```bash
python prompt_eng/cli.py --debug
```

This will log:
- Prompts sent to the LLM
- Raw responses from the LLM
- Parsed intents and entities
- Actions taken based on LLM responses

## Example Interaction

User: "I want to make a weather bot called StormTracker with severe weather alerts"

Context sent to LLM:
```json
{
  "available_bots": ["MyWeatherApp"],
  "current_conversation_context": {
    "current_action": null,
    "bot_type": null,
    "bot_name": null,
    "features": [],
    "waiting_for": null
  },
  "last_messages": [
    {"role": "user", "content": "I want to make a weather bot called StormTracker with severe weather alerts"}
  ],
  "available_actions": ["create_bot", "list_bots", "get_bot_details", "update_bot", "delete_bot", "help"]
}
```

LLM Response:
```
INTENT: Create a weather bot
ENTITIES: {"bot_type": "weather", "bot_name": "StormTracker", "features": ["severe weather alerts"]}
ACTION: create_bot
RESPONSE: I'll create a weather bot named "StormTracker" with severe weather alert capabilities. Would you like me to proceed?
```

## Extending LLM Integration

To extend the LLM integration:
1. Update the system prompt to guide the LLM's behavior
2. Modify the prompt template to extract additional information
3. Add new action handlers in the `_process_with_llm` method
4. Support new LLM providers by implementing the `ChatbotClient` interface 