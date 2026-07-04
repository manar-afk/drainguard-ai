import json
from typing import Dict, Any
from .base_agent import BaseAgent

class WeatherIntelligenceAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are the Weather Intelligence Agent for DrainGuard AI. "
            "Your job is to analyze upcoming weather forecasts, calculate the monsoon intensity level, "
            "and output a structured risk summary. You must classify rainfall severity (Light, Moderate, "
            "Heavy, Very Heavy) and produce explainable meteorological remarks."
        )
        super().__init__("WeatherIntelligenceAgent", system_instruction)

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # inputs should contain weather data (e.g., list of forecast dicts or next 24h forecast)
        forecast = inputs.get("forecast", {})
        rainfall = forecast.get("rainfall_mm", 0.0)
        
        if self._initialized:
            prompt = (
                f"Analyze this 24-hour weather forecast:\n"
                f"- Date: {forecast.get('date')}\n"
                f"- Forecasted Rainfall: {rainfall} mm\n"
                f"- Temperature: {forecast.get('temperature_c')} C\n"
                f"- Humidity: {forecast.get('humidity_pct')}%\n"
                f"- Wind Speed: {forecast.get('wind_speed_kmh')} km/h\n\n"
                f"Please output a JSON object containing exactly these fields:\n"
                f"1. 'alert_level': Green, Yellow, Orange, or Red\n"
                f"2. 'severity_category': Light, Moderate, Heavy, or Very Heavy\n"
                f"3. 'description': Detailed meteorological summary of the situation\n"
                f"4. 'risk_multiplier': A factor between 1.0 and 2.5 representing weather severity risk\n"
                f"5. 'explainable_reasoning': Why you chose this alert and severity level"
            )
            response_text = self.call_gemini(prompt)
            if response_text:
                try:
                    # Clean markdown code blocks if any
                    clean_json = response_text.replace("```json", "").replace("```", "").strip()
                    return json.loads(clean_json)
                except Exception:
                    pass # Fallback to simulated response if parsing fails
                    
        return self._generate_mock_response(inputs)

    def _generate_mock_response(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        forecast = inputs.get("forecast", {})
        rainfall = forecast.get("rainfall_mm", 0.0)
        
        # Heuristics based on rainfall
        if rainfall < 15.0:
            alert = "Green"
            cat = "Light"
            mult = 1.0
            desc = "Scattered light showers expected. Soil moisture remains normal. No immediate flooding threat."
            reason = "Precipitation is well within typical drainage capacities. Soil infiltration rate exceeds rainfall rate."
        elif rainfall < 50.0:
            alert = "Yellow"
            cat = "Moderate"
            mult = 1.3
            desc = "Moderate rainfall forecast. Slow traffic expected. Drainage systems will run at 40-60% capacity."
            reason = "Continuous rainfall over several hours could saturate soil, causing minor localized water accumulation on roads."
        elif rainfall < 110.0:
            alert = "Orange"
            cat = "Heavy"
            mult = 1.8
            desc = "Heavy rainfall warning. Localized street flooding is likely in low-lying areas. Ensure de-silting is completed."
            reason = "High volume of runoff will put major drains under pressure, especially segments with existing silting or blockages."
        else:
            alert = "Red"
            cat = "Very Heavy"
            mult = 2.4
            desc = "Extreme monsoon downpour warning. Immediate risk of major urban flooding. Mobilize disaster management teams."
            reason = "Rainfall intensity (exceeding 100mm/day) will saturate the city's drainage network, leading to extensive overflows at multiple choke points."
            
        return {
            "alert_level": alert,
            "severity_category": cat,
            "description": desc,
            "risk_multiplier": mult,
            "explainable_reasoning": reason
        }
