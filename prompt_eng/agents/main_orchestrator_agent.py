import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
import logging

# Import your agent classes (assume you have created these modules)
from user_interaction_agent import UserInteractionAgent
from requirement_analysis_agent import RequirementAnalysisAgent
from agents.dynamic_bot_generator_agent import DynamicBotGeneratorAgent
from learning_engine_agent import LearningEngineAgent
from ui_generator_agent import UIGeneratorAgent
from deployment_agent import DeploymentAgent
from clients import bootstrap_client_and_model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowContext:
    user_requirements: Dict
    generated_bot: Optional[Dict] = None
    knowledge_base: Optional[Dict] = None
    ui_design: Optional[Dict] = None
    deployment_info: Optional[Dict] = None

class MainOrchestratorAgent:
    def __init__(self):
        # Initialize all agents
        try:
            self.user_agent = UserInteractionAgent()
            self.req_analysis_agent = RequirementAnalysisAgent()
            self.bot_generator = DynamicBotGeneratorAgent()
            self.learning_engine = LearningEngineAgent()
            self.ui_generator = UIGeneratorAgent()
            self.deployment_agent = DeploymentAgent()
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    async def orchestrate_workflow(self) -> Dict:
        """Main workflow orchestration"""
        workflow = WorkflowContext(user_requirements={})
        
        try:
            # Step 1: Get user requirements
            logger.info("Step 1: Gathering user requirements...")
            raw_requirements = await self.user_agent.get_user_input()
            
            # Step 2: Analyze requirements
            logger.info("Step 2: Analyzing requirements...")
            analysis_result = await self.req_analysis_agent.analyze(raw_requirements)
            workflow.user_requirements = analysis_result["requirements"]
            
            # Step 3: Process any provided documents for learning
            if "documents" in workflow.user_requirements:
                logger.info("Step 3: Processing provided documents...")
                docs = workflow.user_requirements["documents"]
                processed_docs = await self.learning_engine.process_documents(docs)
                await self.learning_engine.build_knowledge_base(processed_docs)
                workflow.knowledge_base = {
                    "processed_documents": len(processed_docs),
                    "status": "ready"
                }
            
            # Step 4: Generate bot code
            logger.info("Step 4: Generating bot code...")
            generated_bot = await self.bot_generator.generate_bot(workflow.user_requirements)
            workflow.generated_bot = {
                "name": generated_bot.name,
                "code": generated_bot.code,
                "conversation_flow": generated_bot.conversation_flow,
                "business_rules": generated_bot.business_rules
            }
            
            # Step 5: Generate UI if needed
            if workflow.user_requirements.get("ui_preferences"):
                logger.info("Step 5: Generating UI...")
                ui_code = self.ui_generator.generate_ui(workflow.user_requirements)
                workflow.ui_design = {"ui_code": ui_code}
                workflow.generated_bot["code"]["ui.jsx"] = ui_code
            
            # Step 6: Deploy the bot
            logger.info("Step 6: Deploying bot...")
            deployment_info = await self.deployment_agent.deploy({
                **workflow.generated_bot,
                "platform": workflow.user_requirements.get("platform", "web")
            })
            workflow.deployment_info = deployment_info
            
            # Return complete workflow summary
            return self._generate_workflow_summary(workflow)
            
        except Exception as e:
            return await self._handle_error(e, "workflow_orchestration")

    def _generate_workflow_summary(self, workflow: WorkflowContext) -> Dict:
        """Generate a summary of the complete workflow"""
        return {
            "status": "success",
            "bot_details": {
                "name": workflow.generated_bot["name"],
                "type": workflow.user_requirements.get("bot_type"),
                "features": workflow.user_requirements.get("features", [])
            },
            "knowledge_base": workflow.knowledge_base,
            "ui_generated": bool(workflow.ui_design),
            "deployment": workflow.deployment_info
        }

    async def _handle_error(self, error: Exception, step: str) -> Dict:
        """Handle workflow errors"""
        logger.error(f"Error in {step}: {str(error)}")
        return {
            "status": "failed",
            "error": str(error),
            "step": step
        }

# Example usage:
if __name__ == "__main__":
    async def main():
        orchestrator = MainOrchestratorAgent()
        
        print("Welcome to Mother of Bots!")
        print("This system will help you create, customize, and deploy your bot.")
        print("\nStarting workflow...")
        
        result = await orchestrator.orchestrate_workflow()
        
        if result["status"] == "success":
            print("\nBot creation successful!")
            print(f"Bot Name: {result['bot_details']['name']}")
            print(f"Type: {result['bot_details']['type']}")
            print(f"Features: {', '.join(result['bot_details']['features'])}")
            
            if result["deployment"]["status"] == "deployed":
                print(f"\nBot deployed successfully!")
                if "url" in result["deployment"]:
                    print(f"Access your bot at: {result['deployment']['url']}")
            elif result["deployment"]["status"] == "guide_generated":
                print("\nDeployment Guide Generated:")
                guide = result["deployment"]["deployment_guide"]
                print("\nPrerequisites:")
                for prereq in guide.prerequisites:
                    print(f"- {prereq}")
                print("\nFollow these steps:")
                for i, step in enumerate(guide.steps, 1):
                    print(f"{i}. {step}")
        else:
            print(f"\nError occurred during {result['step']}")
            print(f"Error: {result['error']}")
    
    asyncio.run(main()) 