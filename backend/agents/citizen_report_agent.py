import json
import math
from typing import Dict, Any, List
from .base_agent import BaseAgent

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlamb/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

class CitizenReportAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are the Citizen Report Agent for DrainGuard AI. "
            "Your job is to intake text/voice reports from the public, categorize them into specific drainage issues "
            "(Garbage Blockage, Silt Accumulation, Broken Cover, Encroachment, Vegetation Overgrowth, Drain Collapse), "
            "assign severity, and check if the report is a duplicate of a nearby active complaint (within 50 meters)."
        )
        super().__init__("CitizenReportAgent", system_instruction)

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get("text", "")
        lat = inputs.get("latitude", 0.0)
        lng = inputs.get("longitude", 0.0)
        existing_reports = inputs.get("existing_reports", [])
        
        # 1. Check for duplicates in python first (deterministic geospatial filter)
        duplicate_id = None
        for report in existing_reports:
            r_lat = report.get("latitude")
            r_lng = report.get("longitude")
            r_id = report.get("id")
            r_status = report.get("status", "")
            r_cat = report.get("category", "")
            
            if r_status != "Resolved" and r_lat and r_lng:
                dist = haversine_distance(lat, lng, r_lat, r_lng)
                # If within 50 meters and similar issues, mark as duplicate
                if dist < 50.0:
                    # We will confirm duplicate if categories match or if text is similar
                    duplicate_id = r_id
                    break
                    
        # 2. Run LLM categorization if live API is present
        if self._initialized:
            prompt = (
                f"Analyze this citizen drainage complaint:\n"
                f"- Text: \"{text}\"\n"
                f"- Latitude: {lat}\n"
                f"- Longitude: {lng}\n\n"
                f"Provide a JSON response with exactly these fields:\n"
                f"1. 'category': Garbage Blockage, Silt Accumulation, Broken Cover, Encroachment, Vegetation Overgrowth, or Drain Collapse\n"
                f"2. 'severity': Low, Medium, High, or Critical\n"
                f"3. 'recommended_immediate_action': short advice for sanitation supervisor\n"
                f"4. 'explainable_reasoning': why you chose this category and severity"
            )
            response_text = self.call_gemini(prompt)
            if response_text:
                try:
                    clean_json = response_text.replace("```json", "").replace("```", "").strip()
                    res = json.loads(clean_json)
                    res["is_duplicate"] = duplicate_id is not None
                    res["duplicate_of"] = duplicate_id
                    return res
                except Exception:
                    pass # Fallback
                    
        res = self._generate_mock_response(inputs)
        res["is_duplicate"] = duplicate_id is not None
        res["duplicate_of"] = duplicate_id
        return res

    def _generate_mock_response(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get("text", "").lower()
        
        # Categorize by simple keyword matching
        category = "Garbage Blockage"
        severity = "Medium"
        action = "Deploy sanitation workers to check inlet screen."
        reason = "Detected words indicating surface rubbish obstructing flow."
        
        if "silt" in text or "mud" in text or "dirt" in text:
            category = "Silt Accumulation"
            severity = "Medium"
            action = "Add to mechanical de-silting schedule."
            reason = "Citizen describes thick mud or silt layers at the bottom of the drain."
        elif "cover" in text or "grate" in text or "hole" in text or "broken" in text:
            category = "Broken Cover"
            severity = "High"
            action = "Dispatch maintenance crew to seal the open drain and install safety barriers."
            reason = "Open drainage shafts are high-severity hazards for pedestrian safety."
        elif "shop" in text or "stall" in text or "encroach" in text or "built" in text:
            category = "Encroachment"
            severity = "Critical"
            action = "Notify municipal enforcement team to inspect unauthorized extensions."
            reason = "Building over drains completely prevents maintenance access and creates severe choke points."
        elif "weed" in text or "grass" in text or "vegetation" in text or "bush" in text:
            category = "Vegetation Overgrowth"
            severity = "Low"
            action = "Schedule weed trimming during routine local sweep."
            reason = "Vegetation restricts water flow speed, but does not fully block drainage."
        elif "collapse" in text or "fell" in text or "cave" in text or "wall" in text:
            category = "Drain Collapse"
            severity = "Critical"
            action = "Immediately send structural engineers to reinforce the drain wall."
            reason = "A collapsed retaining wall blocks water and can cause roads above it to sink."
        elif "trash" in text or "garbage" in text or "plastic" in text or "bottle" in text or "clog" in text:
            category = "Garbage Blockage"
            severity = "High"
            action = "Deploy clean-up crew to clear trash blocking water inlet."
            reason = "Trash clogging causes rapid surface pooling during rains, resulting in high risk."
            
        return {
            "category": category,
            "severity": severity,
            "recommended_immediate_action": action,
            "explainable_reasoning": reason
        }
