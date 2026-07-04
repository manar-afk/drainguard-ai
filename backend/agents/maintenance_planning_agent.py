import json
from typing import Dict, Any
from .base_agent import BaseAgent

class MaintenancePlanningAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are the Maintenance Planning Agent for DrainGuard AI. "
            "Your job is to take flood risk outputs and drain details, and generate optimal maintenance "
            "work orders. Recommend numbers of field workers, necessary equipment (vacuum trucks, excavators, "
            "crew tools), cost estimates, repair time, and the percentage reduction in flood risk "
            "that will be achieved after cleaning. Explain your resource allocation logic."
        )
        super().__init__("MaintenancePlanningAgent", system_instruction)

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        drain = inputs.get("drain", {})
        risk = inputs.get("risk", {})
        
        if self._initialized:
            prompt = (
                f"Create a maintenance recommendation for this drain:\n"
                f"- Drain ID: {drain.get('id')}\n"
                f"- Name: {drain.get('name')}\n"
                f"- Silt Condition: {drain.get('condition_pct')}%\n"
                f"- Capacity: {drain.get('capacity_m3s')} m3/s\n"
                f"- Overflow Probability: {risk.get('overflow_probability')}\n"
                f"- Flood Risk Severity: {risk.get('severity')}\n\n"
                f"Return a JSON object containing exactly these fields:\n"
                f"1. 'priority_level': an integer from 1 (lowest) to 5 (highest)\n"
                f"2. 'workers_required': integer\n"
                f"3. 'equipment_required': list of strings\n"
                f"4. 'estimated_time_hours': float\n"
                f"5. 'estimated_cost_usd': float\n"
                f"6. 'expected_risk_reduction_pct': float (how much the overflow probability will decrease, e.g. 75.0% reduction)\n"
                f"7. 'explainable_reasoning': explanation of the chosen resources, cost, and risk impact"
            )
            response_text = self.call_gemini(prompt)
            if response_text:
                try:
                    clean_json = response_text.replace("```json", "").replace("```", "").strip()
                    return json.loads(clean_json)
                except Exception:
                    pass # Fallback
                    
        return self._generate_mock_response(inputs)

    def _generate_mock_response(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        drain = inputs.get("drain", {})
        risk = inputs.get("risk", {})
        
        prob = risk.get("overflow_probability", 0.1)
        sev = risk.get("severity", "Green")
        cond = drain.get("condition_pct", 100.0)
        
        # Calculate priorities based on risk severity
        if sev == "Critical":
            priority = 5
            workers = 12
            equipment = ["High-Capacity Sucking Machine", "JCB Heavy Excavator", "Dewatering Pumps", "De-silting Crew Kit"]
            time = 18.0
            cost = 2400.0
            reduction = round(prob * 0.85 * 100.0, 1) # reduce risk by 85%
            reason = (
                f"Due to CRITICAL risk, we recommend immediate mobilization of a large de-silting crew "
                f"supported by heavy mechanical sucking machines and excavators. The drain is severely clogged "
                f"({cond}% condition), and clearing it will restore flow capacity, preventing significant flooding."
            )
        elif sev == "Red" or sev == "High":
            priority = 4
            workers = 8
            equipment = ["Sucking Machine", "JCB Excavator", "De-silting Crew Kit"]
            time = 12.0
            cost = 1500.0
            reduction = round(prob * 0.80 * 100.0, 1)
            reason = (
                f"High-risk rating requires deployment of a standard mechanical de-silting unit. "
                f"Clearing blockages will reduce overflow probability by {reduction} percentage points, "
                f"protecting nearby roadways and commercial markets."
            )
        elif sev == "Orange" or sev == "Medium":
            priority = 3
            workers = 6
            equipment = ["De-silting Crew Kit", "Trash Collection Vehicle"]
            time = 8.0
            cost = 800.0
            reduction = round(prob * 0.75 * 100.0, 1)
            reason = (
                f"Medium-risk drain. Recommended cleaning by a manual de-silting crew with trash collection support. "
                f"This proactive clearing will prevent silt build-up from escalating to a high-severity bottleneck."
            )
        elif sev == "Yellow":
            priority = 2
            workers = 4
            equipment = ["Manual Cleansing Tools", "Trash Collection Vehicle"]
            time = 6.0
            cost = 400.0
            reduction = round(prob * 0.70 * 100.0, 1)
            reason = (
                f"Low-risk drain. Routine maintenance is scheduled. A 4-worker manual team can clear superficial garbage "
                f"and vegetation, maintaining the drain's current performance."
            )
        else:
            priority = 1
            workers = 2
            equipment = ["Manual Cleansing Tools"]
            time = 4.0
            cost = 150.0
            reduction = round(prob * 0.50 * 100.0, 1)
            reason = (
                f"Drain is in excellent condition ({cond}%). Minimal maintenance required. "
                f"A 2-person inspection crew will clear surface dry leaves and minor litter."
            )
            
        return {
            "priority_level": priority,
            "workers_required": workers,
            "equipment_required": equipment,
            "estimated_time_hours": time,
            "estimated_cost_usd": cost,
            "expected_risk_reduction_pct": reduction,
            "explainable_reasoning": reason
        }
