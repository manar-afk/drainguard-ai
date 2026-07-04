import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .weather_intelligence_agent import WeatherIntelligenceAgent
from .flood_prediction_agent import FloodPredictionAgent
from .maintenance_planning_agent import MaintenancePlanningAgent

class DecisionIntelligenceAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are the Lead Decision Intelligence Agent for DrainGuard AI. "
            "Your job is to coordinate the other agents (Weather, Flood Prediction, Maintenance Planning) "
            "and synthesize their individual reports into a single, cohesive, explainable decision directive. "
            "You will establish the overall Flood Risk Index, the Drain Health Score, and list the "
            "prioritized prevention steps with transparent reasoning."
        )
        super().__init__("DecisionIntelligenceAgent", system_instruction)
        self.weather_agent = WeatherIntelligenceAgent()
        self.prediction_agent = FloodPredictionAgent()
        self.maintenance_agent = MaintenancePlanningAgent()

    def run_workflow(self, drain_data: Dict[str, Any], weather_data: Dict[str, Any], history_count: int) -> Dict[str, Any]:
        # 1. Run Weather Agent
        weather_inputs = {"forecast": weather_data}
        weather_result = self.weather_agent.run(weather_inputs)
        
        # 2. Run Flood Prediction Agent
        prediction_inputs = {
            "drain": drain_data,
            "weather": weather_data,
            "history_count": history_count
        }
        prediction_result = self.prediction_agent.run(prediction_inputs)
        
        # 3. Run Maintenance Planning Agent
        maintenance_inputs = {
            "drain": drain_data,
            "risk": prediction_result
        }
        maintenance_result = self.maintenance_agent.run(maintenance_inputs)
        
        # 4. Synthesize the results (Run self as Decision Agent)
        overall_risk_index = round(prediction_result.get("overflow_probability", 0.0) * 100.0, 1)
        drain_health_score = round(drain_data.get("condition_pct", 100.0), 1)
        
        # Readiness calculation: base readiness is drain health, degraded by weather risk severity
        weather_multiplier = weather_result.get("risk_multiplier", 1.0)
        monsoon_readiness_score = round(max(0.0, min(100.0, drain_health_score - (weather_multiplier - 1.0) * 20.0)), 1)
        
        if self._initialized:
            prompt = (
                f"Compile a final decision report for Drain: {drain_data.get('name')} (ID: {drain_data.get('id')}).\n"
                f"Here are the inputs from your sub-agents:\n\n"
                f"--- WEATHER INTELLIGENCE REPORT ---\n"
                f"{json.dumps(weather_result, indent=2)}\n\n"
                f"--- FLOOD RISK PREDICTION REPORT ---\n"
                f"{json.dumps(prediction_result, indent=2)}\n\n"
                f"--- MAINTENANCE PLANNING REPORT ---\n"
                f"{json.dumps(maintenance_result, indent=2)}\n\n"
                f"Synthesize this information. Create a final executive decision briefing. "
                f"Output a JSON object containing exactly these fields:\n"
                f"1. 'flood_risk_index': float (0-100)\n"
                f"2. 'drain_health_score': float (0-100)\n"
                f"3. 'monsoon_readiness_score': float (0-100)\n"
                f"4. 'risk_status': Green, Yellow, Orange, or Red\n"
                f"5. 'recommended_immediate_action': string\n"
                f"6. 'action_details': dict with 'workers', 'cost', 'time_hours', 'equipment'\n"
                f"7. 'expected_impact_reduction_pct': float\n"
                f"8. 'executive_summary': A cohesive briefing summarizing the meteorological threat, hydraulic vulnerability, operational response required, and explainable reasoning for the priority status."
            )
            response_text = self.call_gemini(prompt)
            if response_text:
                try:
                    clean_json = response_text.replace("```json", "").replace("```", "").strip()
                    res = json.loads(clean_json)
                    # Include sub-agent details in final response
                    res["sub_agents"] = {
                        "weather": weather_result,
                        "prediction": prediction_result,
                        "maintenance": maintenance_result
                    }
                    return res
                except Exception:
                    pass # Fallback to mock
                    
        # Fallback simulation
        summary_text = (
            f"Drain {drain_data.get('name')} shows a Flood Risk Index of {overall_risk_index}% "
            f"under a weather forecast of {weather_data.get('rainfall_mm')}mm rainfall. "
            f"The Weather Agent has declared an {weather_result.get('alert_level')} alert level. "
            f"The Flood Prediction Agent notes a probability of {prediction_result.get('overflow_probability')} "
            f"for overflow, estimating a water depth of {prediction_result.get('estimated_accumulation_depth_cm')} cm. "
            f"To mitigate this risk, the Maintenance Planning Agent recommends deploying {maintenance_result.get('workers_required')} workers "
            f"with {', '.join(maintenance_result.get('equipment_required', []))} for a duration of {maintenance_result.get('estimated_time_hours')} hours, "
            f"costing ${maintenance_result.get('estimated_cost_usd')}. This intervention will reduce the flood risk by {maintenance_result.get('expected_risk_reduction_pct')}%."
        )
        
        return {
            "flood_risk_index": overall_risk_index,
            "drain_health_score": drain_health_score,
            "monsoon_readiness_score": monsoon_readiness_score,
            "risk_status": prediction_result.get("severity", "Green"),
            "recommended_immediate_action": maintenance_result.get("explainable_reasoning", ""),
            "action_details": {
                "workers": maintenance_result.get("workers_required", 0),
                "cost": maintenance_result.get("estimated_cost_usd", 0.0),
                "time_hours": maintenance_result.get("estimated_time_hours", 0.0),
                "equipment": maintenance_result.get("equipment_required", [])
            },
            "expected_impact_reduction_pct": maintenance_result.get("expected_risk_reduction_pct", 0.0),
            "executive_summary": summary_text,
            "sub_agents": {
                "weather": weather_result,
                "prediction": prediction_result,
                "maintenance": maintenance_result
            }
        }
