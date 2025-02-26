import os
import subprocess
import logging
import sys
from typing import Optional
import signal
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotDeployer:
    def __init__(self):
        self.bots_dir = "generated_bots"
        self.running_bots = {}  # Store bot processes
        self.deployment_dir = "deployed_bots"
        
        # Create necessary directories
        os.makedirs(self.bots_dir, exist_ok=True)
        os.makedirs(self.deployment_dir, exist_ok=True)
        
        # Create or load deployment status file
        self.status_file = Path(self.deployment_dir) / "deployment_status.json"
        self.load_deployment_status()

    def load_deployment_status(self):
        """Load deployment status from file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    self.deployment_status = json.load(f)
            except Exception as e:
                logger.error(f"Error loading deployment status: {e}")
                self.deployment_status = {}
        else:
            self.deployment_status = {}

    def save_deployment_status(self):
        """Save deployment status to file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.deployment_status, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving deployment status: {e}")

    def install_requirements(self, bot_type: str):
        """Install required packages based on bot type"""
        try:
            if bot_type == "discord":
                subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py"])
            elif bot_type == "web":
                subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install requirements: {e}")
            raise

    def create_env_file(self, bot_name: str, bot_type: str, token: Optional[str] = None):
        """Create environment file for bot"""
        env_path = Path(self.deployment_dir) / bot_name / ".env"
        env_path.parent.mkdir(exist_ok=True)
        
        env_vars = {
            "BOT_NAME": bot_name,
            "BOT_TYPE": bot_type
        }
        
        if bot_type == "discord" and token:
            env_vars["DISCORD_TOKEN"] = token
        
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

    def deploy_bot(self, bot_name: str, bot_type: str, token: Optional[str] = None):
        """Deploy and launch a bot"""
        try:
            # Install requirements
            self.install_requirements(bot_type)
            
            # Create deployment directory for this bot
            bot_deploy_dir = Path(self.deployment_dir) / bot_name
            bot_deploy_dir.mkdir(exist_ok=True)
            
            # Copy bot file to deployment directory
            source_file = Path(self.bots_dir) / f"{bot_name}.py"
            target_file = bot_deploy_dir / f"{bot_name}.py"
            
            if not source_file.exists():
                raise FileNotFoundError(f"Bot file not found: {source_file}")
            
            with open(source_file, 'r') as src, open(target_file, 'w') as dst:
                content = src.read()
                if bot_type == "discord" and token:
                    # Replace placeholder token with actual token
                    content = content.replace("'YOUR_TOKEN'", f"'{token}'")
                dst.write(content)
            
            # Create environment file
            self.create_env_file(bot_name, bot_type, token)
            
            # Launch bot
            self.launch_bot(bot_name, bot_type)
            
            # Update deployment status
            self.deployment_status[bot_name] = {
                "type": bot_type,
                "status": "running",
                "deploy_path": str(bot_deploy_dir)
            }
            self.save_deployment_status()
            
            logger.info(f"Successfully deployed {bot_name} ({bot_type})")
            
        except Exception as e:
            logger.error(f"Failed to deploy {bot_name}: {e}")
            raise

    def launch_bot(self, bot_name: str, bot_type: str):
        """Launch a deployed bot"""
        try:
            bot_file = Path(self.deployment_dir) / bot_name / f"{bot_name}.py"
            
            if not bot_file.exists():
                raise FileNotFoundError(f"Bot file not found: {bot_file}")
            
            # Kill existing process if running
            self.stop_bot(bot_name)
            
            # Start new process
            process = subprocess.Popen(
                [sys.executable, str(bot_file)],
                cwd=bot_file.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.running_bots[bot_name] = process
            logger.info(f"Launched {bot_name} (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"Failed to launch {bot_name}: {e}")
            raise

    def stop_bot(self, bot_name: str):
        """Stop a running bot"""
        if bot_name in self.running_bots:
            try:
                process = self.running_bots[bot_name]
                if sys.platform == 'win32':
                    # On Windows, use taskkill to forcefully terminate the process tree
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                check=False, capture_output=True)
                else:
                    # On Unix-like systems, use SIGTERM
                    os.kill(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                
                del self.running_bots[bot_name]
                
                self.deployment_status[bot_name]["status"] = "stopped"
                self.save_deployment_status()
                
                logger.info(f"Stopped {bot_name}")
            except Exception as e:
                logger.error(f"Failed to stop {bot_name}: {e}")
                raise

    def stop_all_bots(self):
        """Stop all running bots"""
        for bot_name in list(self.running_bots.keys()):
            self.stop_bot(bot_name)

    def get_bot_status(self, bot_name: str) -> dict:
        """Get status of a bot"""
        if bot_name not in self.deployment_status:
            return {"status": "not_deployed"}
        
        status = self.deployment_status[bot_name].copy()
        if bot_name in self.running_bots:
            process = self.running_bots[bot_name]
            status["pid"] = process.pid
            status["running"] = process.poll() is None
        
        return status

    def __del__(self):
        """Cleanup when deployer is destroyed"""
        self.stop_all_bots()

def main():
    """Test deployment manager"""
    deployer = BotDeployer()
    
    # Example usage
    try:
        # Deploy a Discord bot
        deployer.deploy_bot(
            bot_name="test_discord_bot",
            bot_type="discord",
            token="YOUR_DISCORD_TOKEN"
        )
        
        # Deploy a web bot
        deployer.deploy_bot(
            bot_name="test_web_bot",
            bot_type="web"
        )
        
        # Get status
        print(deployer.get_bot_status("test_discord_bot"))
        print(deployer.get_bot_status("test_web_bot"))
        
    except Exception as e:
        logger.error(f"Deployment test failed: {e}")
    finally:
        deployer.stop_all_bots()

if __name__ == "__main__":
    main() 