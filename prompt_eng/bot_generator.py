class DynamicBotGenerator:
    def __init__(self):
        self.code_generator = CodeGenerator()
        self.flow_designer = FlowDesigner()
        self.rule_engine = RuleEngine()
    
    async def generate_bot(self, requirements: RequirementAnalysis, ui_design: Optional[dict] = None) -> str:
        flow = self.flow_designer.design(requirements)
        rules = self.rule_engine.generate_rules(requirements)
        
        return self.code_generator.generate(
            requirements=requirements,
            flow=flow,
            rules=rules,
            ui_design=ui_design
        ) 