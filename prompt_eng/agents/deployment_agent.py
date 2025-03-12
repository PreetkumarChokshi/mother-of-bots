from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import os
import subprocess
import logging
from pathlib import Path
from bot_deployer import BotDeployer
from clients import bootstrap_client_and_model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    platform: str  # 'web', 'discord', 'kubernetes', 'docker'
    requirements: List[str]
    environment_vars: Dict[str, str]
    port: Optional[int] = None
    domain: Optional[str] = None

@dataclass
class DeploymentGuide:
    steps: List[str]
    commands: List[str]
    prerequisites: List[str]
    configuration_files: Dict[str, str]  # filename -> content

class DeploymentAgent:
    def __init__(self):
        self.deployer = BotDeployer()
        # Initialize client for generating deployment configs
        self.client, self.model = bootstrap_client_and_model(
            preferred_model="codellama"  # Prefer code-savvy model
        )
        self.deployment_dir = Path("deployed_bots")
        self.deployment_dir.mkdir(exist_ok=True)
    
    async def deploy(self, generated_bot: dict) -> dict:
        """Deploy the generated bot and return deployment information"""
        try:
            bot_name = generated_bot.get("name", "default_bot")
            platform = generated_bot.get("platform", "web")
            
            # Generate deployment configuration
            config = await self._generate_deployment_config(generated_bot)
            
            if platform == "web":
                return await self._deploy_web_bot(bot_name, generated_bot, config)
            elif platform == "discord":
                return await self._deploy_discord_bot(bot_name, generated_bot, config)
            else:
                # Generate deployment guide for other platforms
                guide = await self._generate_deployment_guide(generated_bot, config)
                return {
                    "status": "guide_generated",
                    "bot_name": bot_name,
                    "deployment_guide": guide
                }
                
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def _generate_deployment_config(self, bot_data: dict) -> DeploymentConfig:
        """Generate deployment configuration based on bot requirements"""
        system_prompt = """Generate deployment configuration for the bot.
        Include platform requirements, environment variables, and network settings.
        Respond in JSON format."""
        
        self.client.set_system_prompt(system_prompt)
        
        _, config_json = self.client.chat_completion(
            json.dumps(bot_data),
            self.model,
            None
        )
        
        config_data = json.loads(config_json)
        return DeploymentConfig(
            platform=config_data.get("platform", "web"),
            requirements=config_data.get("requirements", []),
            environment_vars=config_data.get("env_vars", {}),
            port=config_data.get("port"),
            domain=config_data.get("domain")
        )

    async def _deploy_web_bot(self, bot_name: str, bot_data: dict, config: DeploymentConfig) -> dict:
        """Deploy bot to web platform"""
        # Create deployment directory
        bot_dir = self.deployment_dir / bot_name
        bot_dir.mkdir(exist_ok=True)
        
        # Generate necessary files
        await self._generate_deployment_files(bot_dir, bot_data, config)
        
        # Deploy using BotDeployer
        self.deployer.deploy_bot(bot_name, "web")
        self.deployer.launch_bot(bot_name, "web")
        
        deployment_info = {
            "status": "deployed",
            "bot_name": bot_name,
            "url": f"http://localhost:{config.port}" if config.port else "http://localhost:5000",
            "type": "web"
        }
        
        return deployment_info

    async def _deploy_discord_bot(self, bot_name: str, bot_data: dict, config: DeploymentConfig) -> dict:
        """Deploy bot to Discord"""
        # Create deployment directory
        bot_dir = self.deployment_dir / bot_name
        bot_dir.mkdir(exist_ok=True)
        
        # Generate necessary files
        await self._generate_deployment_files(bot_dir, bot_data, config)
        
        # Deploy using BotDeployer
        self.deployer.deploy_bot(
            bot_name, 
            "discord",
            token=config.environment_vars.get("DISCORD_TOKEN")
        )
        
        return {
            "status": "deployed",
            "bot_name": bot_name,
            "type": "discord"
        }

    async def _generate_deployment_guide(self, bot_data: dict, config: DeploymentConfig) -> DeploymentGuide:
        """Generate deployment guide for container/kubernetes deployment"""
        system_prompt = """Create a detailed deployment guide including:
        1. Prerequisites
        2. Step-by-step instructions
        3. Required commands
        4. Configuration files (Dockerfile, kubernetes manifests)
        Respond in JSON format."""
        
        self.client.set_system_prompt(system_prompt)
        
        _, guide_json = self.client.chat_completion(
            json.dumps({
                "bot_data": bot_data,
                "config": config.__dict__
            }),
            self.model,
            None
        )
        
        guide_data = json.loads(guide_json)
        return DeploymentGuide(
            steps=guide_data.get("steps", []),
            commands=guide_data.get("commands", []),
            prerequisites=guide_data.get("prerequisites", []),
            configuration_files=guide_data.get("configuration_files", {})
        )

    async def _generate_deployment_files(self, bot_dir: Path, bot_data: dict, config: DeploymentConfig):
        """Generate necessary deployment files"""
        # Generate Dockerfile
        dockerfile_content = await self._generate_dockerfile(bot_data, config)
        with open(bot_dir / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        # Generate docker-compose.yml if needed
        if config.platform == "web":
            compose_content = await self._generate_docker_compose(bot_data, config)
            with open(bot_dir / "docker-compose.yml", "w") as f:
                f.write(compose_content)
        
        # Generate environment file
        env_content = "\n".join(f"{k}={v}" for k, v in config.environment_vars.items())
        with open(bot_dir / ".env", "w") as f:
            f.write(env_content)
        
        # Copy bot code files
        for filename, content in bot_data.get("code", {}).items():
            with open(bot_dir / filename, "w") as f:
                f.write(content)

    async def _generate_dockerfile(self, bot_data: dict, config: DeploymentConfig) -> str:
        """Generate Dockerfile for the bot"""
        system_prompt = """Generate a Dockerfile for the bot deployment.
        Include necessary dependencies and configuration."""
        
        self.client.set_system_prompt(system_prompt)
        
        _, dockerfile = self.client.chat_completion(
            json.dumps({
                "bot_data": bot_data,
                "config": config.__dict__
            }),
            self.model,
            None
        )
        
        return dockerfile

    async def _generate_docker_compose(self, bot_data: dict, config: DeploymentConfig) -> str:
        """Generate docker-compose.yml for the bot"""
        system_prompt = """Generate a docker-compose.yml file for the bot deployment.
        Include necessary services and configuration."""
        
        self.client.set_system_prompt(system_prompt)
        
        _, compose_file = self.client.chat_completion(
            json.dumps({
                "bot_data": bot_data,
                "config": config.__dict__
            }),
            self.model,
            None
        )
        
        return compose_file

# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def main():
        agent = DeploymentAgent()
        
        # Example bot data
        sample_bot = {
            "name": "WeatherBot",
            "platform": "kubernetes",
            "code": {
                "main.py": "print('Hello, World!')",
                "requirements.txt": "requests==2.26.0"
            },
            "type": "web_bot"
        }
        
        # Deploy bot
        result = await agent.deploy(sample_bot)
        
        if result["status"] == "guide_generated":
            guide = result["deployment_guide"]
            print("\nDeployment Guide:")
            print("\nPrerequisites:")
            for prereq in guide.prerequisites:
                print(f"- {prereq}")
            
            print("\nSteps:")
            for i, step in enumerate(guide.steps, 1):
                print(f"{i}. {step}")
            
            print("\nCommands:")
            for cmd in guide.commands:
                print(f"$ {cmd}")
            
            print("\nConfiguration Files:")
            for filename, content in guide.configuration_files.items():
                print(f"\n{filename}:")
                print(content)
        else:
            print(f"\nDeployment Result: {result}")
    
    asyncio.run(main()) 