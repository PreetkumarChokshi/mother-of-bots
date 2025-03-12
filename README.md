# Mother of Bots

Mother of Bots is a framework for creating and managing specialized chatbots with different capabilities. The system uses a master bot to help users generate specialized bots for various purposes.

## Features

- **Master Bot**: A conversational interface for creating and managing bots
- **Bot Generation**: Create bots from templates with customized features
- **LLM Integration**: Enhanced natural language understanding powered by LLM APIs
- **Bot Management**: Store, retrieve, update, and delete generated bots
- **Multi-platform Support**: Generate bots for web, CLI, or Discord

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mother-of-bots.git
cd mother-of-bots
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the LLM API (optional):
Create a `config.cfg` file in the `prompt_eng/agents/` directory with the following content:
```
[DEFAULT]
chatbot_api_host = your_llm_api_host
bearer = your_api_token
```

### Running the Master Bot

You can run the Master Bot in several modes:

#### Standard Mode
```bash
python prompt_eng/cli.py
```

#### With LLM Integration
```bash
python prompt_eng/cli.py --config your_config_file.cfg
```

#### With Debug Logging
```bash
python prompt_eng/cli.py --debug
```

#### Test Mode (with mock responses)
```bash
python prompt_eng/cli.py --test-mode
```

#### Without LLM (rule-based only)
```bash
python prompt_eng/cli.py --no-llm
```

## Using the Master Bot

The Master Bot allows you to interact with it using natural language. Here are some examples:

- **Create a bot**: "Create a weather bot called WeatherHelper"
- **List bots**: "Show me all my bots"
- **Get bot details**: "Tell me about WeatherHelper"
- **Update a bot**: "Update WeatherHelper to add severe weather alerts feature"
- **Delete a bot**: "Delete WeatherHelper"

## LLM-Powered Interactions

When running with LLM integration enabled, the Master Bot can understand more natural language expressions and maintain context across the conversation. This provides:

1. Better understanding of user intent
2. Context-aware responses
3. More natural conversational flow
4. Improved entity extraction (bot names, features, etc.)

### Configuration for LLM

To use your own LLM API:

1. Create a configuration file with your API credentials
2. Use the `--config` flag when starting the Master Bot
3. Ensure your API provides a compatible interface with the supported clients

## Bot Templates

Currently, the following bot templates are available:

- **Weather Bot**: For weather forecasts and alerts
- **Customer Service Bot**: For handling customer inquiries and support 
- **E-commerce Bot**: For product searches and recommendations

Each template comes with predefined intents, responses, and business rules that can be customized.

## Architecture

The Mother of Bots framework consists of several key components:

- **MasterBot**: Main interface for user interaction
- **BotManager**: Handles the storage and retrieval of generated bots
- **DynamicBotGenerator**: Creates specialized bots based on requirements
- **LLMClient**: Interfaces with external LLM APIs for enhanced language understanding

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
