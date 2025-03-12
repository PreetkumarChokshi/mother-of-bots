from typing import Dict, List
from dataclasses import dataclass
from analysis.intent_recognizer import IntentRecognizer
from analysis.entity_extractor import EntityExtractor, Entity
from analysis.context_builder import ContextBuilder, BotContext

@dataclass
class RequirementAnalysis:
    context: BotContext
    summary: str
    recommendations: List[str]
    risks: List[str]
    needs_ui: bool

class RequirementAnalysisEngine:
    def __init__(self):
        self.context_builder = ContextBuilder()
    
    async def analyze(self, description: str) -> RequirementAnalysis:
        """
        Analyze requirements and provide comprehensive analysis
        """
        # Build context
        context = self.context_builder.build(description)
        
        # Generate summary
        summary = self._generate_summary(context)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(context)
        
        # Identify risks
        risks = self._identify_risks(context)
        
        # Determine UI needs
        needs_ui = self._needs_ui(context)
        
        return RequirementAnalysis(
            context=context,
            summary=summary,
            recommendations=recommendations,
            risks=risks,
            needs_ui=needs_ui
        )
    
    def _generate_summary(self, context: BotContext) -> str:
        """Generate human-readable summary of requirements"""
        return (
            f"Creating a {context.complexity.lower()} {context.intent} with "
            f"{len(context.features)} main features. Estimated development time: "
            f"{context.estimated_time}. Platform: {context.requirements['platform']}."
        )
    
    def _generate_recommendations(self, context: BotContext) -> List[str]:
        """Generate recommendations based on context"""
        recommendations = []
        
        # Architecture recommendations
        if context.complexity == "Complex":
            recommendations.append("Consider modular architecture for maintainability")
        
        # Feature recommendations
        if "database" in context.features and "backup" not in context.features:
            recommendations.append("Consider adding automated backup functionality")
        
        # Security recommendations
        if "authentication" in context.features:
            recommendations.append("Implement rate limiting and token rotation")
        
        return recommendations
    
    def _identify_risks(self, context: BotContext) -> List[str]:
        """Identify potential risks and challenges"""
        risks = []
        
        # Complexity risks
        if context.complexity == "Complex":
            risks.append("High complexity may increase development time and bugs")
        
        # Integration risks
        if len(context.requirements['integrations']) > 2:
            risks.append("Multiple integrations may cause compatibility issues")
        
        # Security risks
        if "database" in context.features and "authentication" not in context.features:
            risks.append("Database without authentication poses security risk")
        
        return risks
    
    def _needs_ui(self, context: BotContext) -> bool:
        """Determine if bot needs a UI"""
        return (
            context.intent == "web_bot" or
            "dashboard" in context.features or
            "monitoring" in context.features
        ) 