# Mother of Bots (MOB) - AI Bot Generator

## Overview
Mother of Bots (MOB) is a Discord bot that can generate, deploy, and manage specialized AI chatbots. It uses advanced language models to create purpose-specific bots that can be deployed either as Discord bots or web applications.

## Features
- 🤖 Generate specialized AI chatbots
- 🚀 Automatic deployment system
- 💬 Discord bot generation
- 🌐 Web interface bot generation
- 📝 Custom personality and purpose configuration
- 🔄 Dynamic model selection
- 🛠️ Built-in process management

## Prerequisites
- Python 3.8+
- Discord Developer Account (for Discord bots)
- API access to language models

## Installation

1. Clone the repository
bash
git clone https://github.com/yourusername/mother-of-bots.git
cd mother-of-bots

2. Install required packages:

bash
pip install -r requirements.txt


3. Create a `.env` file in the root directory:

env
DISCORD_TOKEN=your_discord_token
CHATBOT_API_HOST=your_api_host
BEARER=your_bearer_token



## Project Structure
mother-of-bots/
├── prompt-eng/
│ ├── mother_of_bots.py # Main MOB Discord bot
│ ├── bot_deployer.py # Deployment manager
│ ├── list_models.py # Available models lister
│ └── config.py # Configuration manager
├── generated_bots/ # Generated bot code storage
├── deployed_bots/ # Active bot deployments
├── requirements.txt
└── README.md



## Usage

### Starting the Mother Bot

bash
python prompt-eng/mother_of_bots.py



### Discord Commands
- `!mob create <bot_name>` - Start bot creation wizard
- `!mob list` - List all created bots
- `!mob deploy <bot_name>` - Deploy a bot
- `!mob delete <bot_name>` - Delete a bot
- `!mob help` - Show help message

### Bot Creation Process
1. Use `!mob create <bot_name>` to start the creation wizard
2. Follow the prompts to specify:
   - Bot type (Discord/Web)
   - Purpose
   - Personality traits
   - Special instructions
3. The bot will be generated and saved
4. Use `!mob deploy <bot_name>` to deploy the bot

### Deployment Types

#### Discord Bot Deployment
When deploying a Discord bot:
1. Create a new application in the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a bot for your application
3. Get the bot token
4. Use the token when prompted during deployment
5. Use the OAuth2 URL generator to invite the bot to your server

#### Web Bot Deployment
Web bots are automatically deployed with:
- Default port: 5000
- Endpoint: `/chat`
- Method: POST
- Request format:
- json
{
"message": "Your message here"
}



## Configuration

### Model Selection
Models are automatically selected based on the bot's purpose:
- Coding tasks: Coding-specialized models
- Knowledge tasks: Large knowledge-based models
- General purpose: Standard chat models

The available models are fetched from your API endpoint and selected based on best match for the purpose.

### Environment Variables
- `DISCORD_TOKEN`: Your Discord bot token
- `CHATBOT_API_HOST`: Host URL for the chat API
- `BEARER`: Bearer token for API authentication

## Deployment Management

The `BotDeployer` class handles:
- Automatic dependency installation
- Process management
- Environment setup
- Status tracking
- Cleanup on shutdown

### Deployment Status
Check deployment status with:
bash
python -c "from bot_deployer import BotDeployer; print(BotDeployer().get_bot_status('bot_name'))




## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Error Handling
- All errors are logged to the console
- Discord error messages are sent to the channel
- Deployment errors are tracked in the status file

## Security Notes
- Keep your `.env` file secure
- Never share API tokens or keys
- Delete messages containing sensitive information
- Use appropriate permissions for deployed bots

## License
[MIT License](LICENSE)

## Support
For support, please open an issue in the GitHub repository.

## Acknowledgments
- Discord.py library
- Flask framework
- AI model providers

---
Made with ❤️ by [Your Name]
