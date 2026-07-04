import os
import shutil
import base64
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .database import (
    get_all_drains, get_drain_by_id, update_drain_condition, get_flood_history,
    get_weather_forecast, get_citizen_reports, insert_citizen_report,
    get_infrastructure, get_maintenance_logs, insert_maintenance_log
)
from .simulation import run_flood_simulation
from .copilot import ask_copilot
from .agents import DecisionIntelligenceAgent, DrainInspectionAgent, CitizenReportAgent

app = FastAPI(title="DrainGuard AI Decision Intelligence Platform API")

# Configure CORS so our React frontend can query the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this. For hackathon, allow all.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories for file uploads (complaints, voice, etc.)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(UPLOADS_DIR, "reports")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Mount static uploads folder
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Dynamic Gemini API Key storage
@app.post("/api/settings/apikey")
def save_api_key(payload: dict):
    key = payload.get("api_key", "").strip()
    if key:
        os.environ["GEMINI_API_KEY"] = key
        # Re-initialize agents with the new API key
        global decision_agent, inspection_agent, citizen_agent
        decision_agent = DecisionIntelligenceAgent()
        inspection_agent = DrainInspectionAgent()
        citizen_agent = CitizenReportAgent()
        return {"status": "success", "message": "Gemini API Key updated successfully."}
    else:
        # Clear key
        os.environ.pop("GEMINI_API_KEY", None)
        return {"status": "success", "message": "Gemini API Key removed. Running in simulated mode."}

@app.get("/api/settings/apikey")
def get_api_key_status():
    has_key = "GEMINI_API_KEY" in os.environ and bool(os.environ["GEMINI_API_KEY"])
    return {"has_key": has_key}

# Initialize Agents
decision_agent = DecisionIntelligenceAgent()
inspection_agent = DrainInspectionAgent()
citizen_agent = CitizenReportAgent()

# 1. AI Decision Dashboard Endpoint
@app.get("/api/dashboard")
def get_dashboard_summary():
    drains = get_all_drains()
    forecast = get_weather_forecast()
    complaints = get_citizen_reports(include_duplicates=False)
    
    if not drains:
        raise HTTPException(status_code=500, detail="No drains found in database. Run generator first.")
        
    next_rain_forecast = forecast[0] if forecast else {"rainfall_mm": 0.0, "alert_level": "Green"}
    rainfall_forecast_mm = next_rain_forecast.get("rainfall_mm", 0.0)
    
    # Calculate Overall Stats
    total_drains = len(drains)
    avg_health = sum(d["condition_pct"] for d in drains) / total_drains
    
    # Critical choke points: Condition < 65
    critical_choke_points = len([d for d in drains if d["condition_pct"] < 65])
    
    # Simple simulated run for overall flood risk index
    sim_100mm = run_flood_simulation(100.0)
    overflow_count = sim_100mm["summary"]["overflowing_drains_current"]
    overall_flood_risk_index = round((overflow_count / total_drains) * 100.0, 1)
    
    # Monsoon Readiness Score
    weather_alert = next_rain_forecast.get("alert_level", "Green")
    weather_penalty = 0
    if weather_alert == "Yellow":
        weather_penalty = 10
    elif weather_alert == "Orange":
        weather_penalty = 25
    elif weather_alert == "Red":
        weather_penalty = 45
        
    monsoon_readiness_score = round(max(0.0, min(100.0, avg_health - weather_penalty)), 1)
    
    # High Risk Areas: Wards with most overflow events in 100mm simulation
    ward_overflows = {}
    for d_sim in sim_100mm["drains"]:
        if d_sim["overflow_current"] == 1:
            ward = d_sim["ward"]
            ward_overflows[ward] = ward_overflows.get(ward, 0) + 1
            
    high_risk_areas = sorted(ward_overflows.items(), key=lambda x: x[1], reverse=True)
    high_risk_wards = [w[0] for w in high_risk_areas[:2]] if high_risk_areas else ["None"]
    
    # Recommended Immediate Actions (Top 3 silted drains requiring action)
    sorted_drains = sorted(drains, key=lambda x: x["condition_pct"])
    immediate_actions = []
    for d in sorted_drains[:3]:
        # Invoke Decision Agent Workflow for top silted drain
        history = get_flood_history(d["id"])
        action_data = decision_agent.run_workflow(d, next_rain_forecast, len(history))
        immediate_actions.append({
            "drain_id": d["id"],
            "drain_name": d["name"],
            "ward": d["ward"],
            "condition": d["condition_pct"],
            "risk_status": action_data["risk_status"],
            "action": action_data["recommended_immediate_action"],
            "details": action_data["action_details"],
            "executive_summary": action_data["executive_summary"]
        })
        
    return {
        "flood_risk_index": overall_flood_risk_index,
        "drain_health_score": round(avg_health, 1),
        "monsoon_readiness_score": monsoon_readiness_score,
        "critical_choke_points": critical_choke_points,
        "rainfall_forecast": next_rain_forecast,
        "high_risk_wards": high_risk_wards,
        "active_citizen_reports_count": len([c for c in complaints if c["status"] != "Resolved"]),
        "recommended_actions": immediate_actions
    }

# 2. AI Drain Risk Prediction Endpoint
@app.get("/api/predictions")
def get_drain_predictions():
    drains = get_all_drains()
    forecast = get_weather_forecast()
    next_rain_forecast = forecast[0] if forecast else {"rainfall_mm": 20.0, "alert_level": "Green"}
    
    predictions = []
    for d in drains:
        history = get_flood_history(d["id"])
        # Invoke Prediction Agent directly
        inputs = {
            "drain": d,
            "weather": next_rain_forecast,
            "history_count": len(history)
        }
        pred = decision_agent.prediction_agent.run(inputs)
        
        predictions.append({
            "drain_id": d["id"],
            "name": d["name"],
            "ward": d["ward"],
            "capacity_m3s": d["capacity_m3s"],
            "condition_pct": d["condition_pct"],
            "elevation_m": d["elevation_m"],
            "overflow_probability": pred.get("overflow_probability", 0.0),
            "severity": pred.get("severity", "Green"),
            "estimated_accumulation_depth_cm": pred.get("estimated_accumulation_depth_cm", 0.0),
            "estimated_flood_area_sqm": pred.get("estimated_flood_area_sqm", 0.0),
            "confidence_score": pred.get("confidence_score", 0.90),
            "feature_importance": pred.get("feature_importance", {}),
            "explainable_reasoning": pred.get("explainable_reasoning", "")
        })
        
    return predictions

# 3. Computer Vision Inspection Endpoint
@app.post("/api/vision/inspect")
async def inspect_drain(
    image: UploadFile = File(...),
    description: str = Form("")
):
    # Sanitize filename to prevent path traversal LFI
    safe_filename = os.path.basename(image.filename)
    # Save the file temporarily
    temp_path = os.path.join(REPORTS_DIR, f"temp_inspect_{safe_filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    try:
        # Load image bytes and base64 encode for Gemini
        with open(temp_path, "rb") as img_file:
            img_bytes = img_file.read()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            
        inputs = {
            "image_bytes": img_b64,
            "image_name": safe_filename,
            "description": description
        }
        
        cv_result = inspection_agent.run(inputs)
        
        # Save a permanent copy if issues detected
        if cv_result.get("detected_issues"):
            perm_filename = f"cv_{int(shutil.time.time())}_{safe_filename}"
            perm_path = os.path.join(REPORTS_DIR, perm_filename)
            shutil.copy(temp_path, perm_path)
            cv_result["image_url"] = f"/uploads/reports/{perm_filename}"
        else:
            cv_result["image_url"] = None
            
        return cv_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision inspection failed: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# 4. Smart Choke Point Detection Endpoint (Map overlays)
@app.get("/api/chokepoints")
def get_chokepoints():
    drains = get_all_drains()
    sim_100mm = run_flood_simulation(100.0) # Evaluated at heavy rain
    
    chokepoints_geojson = []
    for d in drains:
        # Find simulation data for this drain
        sim_data = next((s for s in sim_100mm["drains"] if s["id"] == d["id"]), None)
        color = sim_data["color_current"] if sim_data else "green"
        prob = sim_data["flow_ratio_current"]*0.8 if sim_data else 0.1
        
        chokepoints_geojson.append({
            "id": d["id"],
            "name": d["name"],
            "ward": d["ward"],
            "latitude": d["latitude"],
            "longitude": d["longitude"],
            "capacity": d["capacity_m3s"],
            "condition": d["condition_pct"],
            "elevation": d["elevation_m"],
            "overflow_probability": min(0.99, round(prob, 2)),
            "severity_color": color, # green, yellow, orange, red
            "type": d["type"]
        })
        
    return {
        "drains": chokepoints_geojson,
        "infrastructure": get_infrastructure(),
        "wards": [
            {"name": "Ward A", "risk_index": 72.5, "lat": 19.085, "lng": 72.885, "color": "orange"},
            {"name": "Ward B", "risk_index": 45.0, "lat": 19.075, "lng": 72.895, "color": "yellow"},
            {"name": "Ward C", "risk_index": 88.0, "lat": 19.065, "lng": 72.865, "color": "red"},
            {"name": "Ward D", "risk_index": 30.0, "lat": 19.090, "lng": 72.870, "color": "green"},
            {"name": "Ward E", "risk_index": 60.5, "lat": 19.055, "lng": 72.880, "color": "yellow"}
        ]
    }

# 5. Flood Impact Simulation Endpoint
@app.get("/api/simulation")
def get_simulation_results(rainfall_mm: float = Query(100.0, ge=0.0, le=300.0)):
    return run_flood_simulation(rainfall_mm)

# 6. AI Decision Copilot (RAG Chat)
class ChatQuery(BaseModel):
    query: str

@app.post("/api/copilot/chat")
def copilot_chat(payload: ChatQuery):
    if not payload.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return ask_copilot(payload.query)

# 7. Citizen Reporting Endpoint (with Duplication check)
@app.post("/api/citizen/report")
async def submit_citizen_report(
    text: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None)
):
    image_url = None
    audio_url = None
    
    # Save Image if uploaded
    if image:
        safe_img_name = os.path.basename(image.filename)
        img_filename = f"citizen_img_{int(shutil.time.time())}_{safe_img_name}"
        img_path = os.path.join(REPORTS_DIR, img_filename)
        with open(img_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/uploads/reports/{img_filename}"
        
    # Save Audio if uploaded
    if audio:
        safe_aud_name = os.path.basename(audio.filename)
        aud_filename = f"citizen_aud_{int(shutil.time.time())}_{safe_aud_name}"
        aud_path = os.path.join(REPORTS_DIR, aud_filename)
        with open(aud_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        audio_url = f"/uploads/reports/{aud_filename}"
        
    # Run Agent check for duplicates and categorization
    existing_reports = get_citizen_reports(include_duplicates=False)
    
    agent_inputs = {
        "text": text,
        "latitude": latitude,
        "longitude": longitude,
        "existing_reports": existing_reports
    }
    
    report_analysis = citizen_agent.run(agent_inputs)
    
    # Insert report into SQLite
    report_id = insert_citizen_report(
        text=text,
        image_path=image_url,
        audio_path=audio_url,
        lat=latitude,
        lng=longitude,
        category=report_analysis.get("category", "Garbage Blockage"),
        severity=report_analysis.get("severity", "Medium"),
        status="Open",
        duplicate_of=report_analysis.get("duplicate_of")
    )
    
    return {
        "report_id": report_id,
        "category": report_analysis.get("category"),
        "severity": report_analysis.get("severity"),
        "is_duplicate": report_analysis.get("is_duplicate"),
        "duplicate_of": report_analysis.get("duplicate_of"),
        "recommended_immediate_action": report_analysis.get("recommended_immediate_action"),
        "explainable_reasoning": report_analysis.get("explainable_reasoning"),
        "image_url": image_url,
        "audio_url": audio_url
    }

@app.get("/api/citizen/reports")
def get_citizen_complaints():
    return get_citizen_reports()

# 8. Maintenance Recommendation Engine Endpoint
@app.get("/api/maintenance/recommendations")
def get_maintenance_recommendations():
    drains = get_all_drains()
    forecast = get_weather_forecast()
    next_rain_forecast = forecast[0] if forecast else {"rainfall_mm": 50.0}
    
    recommendations = []
    for d in drains:
        if d["condition_pct"] < 80.0:  # Only recommend for drains that are somewhat silted
            history = get_flood_history(d["id"])
            risk_inputs = {
                "drain": d,
                "weather": next_rain_forecast,
                "history_count": len(history)
            }
            risk_result = decision_agent.prediction_agent.run(risk_inputs)
            
            maint_inputs = {
                "drain": d,
                "risk": risk_result
            }
            maint_result = decision_agent.maintenance_agent.run(maint_inputs)
            
            recommendations.append({
                "drain_id": d["id"],
                "drain_name": d["name"],
                "ward": d["ward"],
                "condition_pct": d["condition_pct"],
                "overflow_probability": risk_result.get("overflow_probability", 0.0),
                "risk_severity": risk_result.get("severity", "Green"),
                "priority_level": maint_result.get("priority_level", 1),
                "workers_required": maint_result.get("workers_required", 2),
                "equipment_required": maint_result.get("equipment_required", []),
                "estimated_time_hours": maint_result.get("estimated_time_hours", 4.0),
                "estimated_cost_usd": maint_result.get("estimated_cost_usd", 150.0),
                "expected_risk_reduction_pct": maint_result.get("expected_risk_reduction_pct", 50.0),
                "explainable_reasoning": maint_result.get("explainable_reasoning", "")
            })
            
    # Sort recommendations by priority level (descending) and condition (ascending)
    recommendations.sort(key=lambda x: (-x["priority_level"], x["condition_pct"]))
    return recommendations

# Create a mock action to mark a drain as cleaned (for the interactive recommendation page)
@app.post("/api/maintenance/clean/{drain_id}")
def clean_drain_action(drain_id: str):
    drain = get_drain_by_id(drain_id)
    if not drain:
        raise HTTPException(status_code=404, detail="Drain not found.")
    
    # Restore condition to 100%
    update_drain_condition(drain_id, 100.0)
    
    # Log the maintenance event in database
    insert_maintenance_log(
        drain_id=drain_id,
        workers_count=6,
        equipment_used="Mechanical Sucking Pump, Desilting Tools",
        cost=800.0,
        risk_reduction=65.0,
        status="Completed"
    )
    
    return {"status": "success", "message": f"Drain {drain_id} has been cleaned and capacity restored to 100%."}

# 9. Analytics Dashboard Endpoint
@app.get("/api/analytics")
def get_analytics():
    drains = get_all_drains()
    forecast = get_weather_forecast()
    history = get_flood_history()
    reports = get_citizen_reports()
    
    # 1. Drain Condition Distribution
    cond_bins = {"Excellent (90-100)": 0, "Good (75-89)": 0, "Fair (60-74)": 0, "Critical (<60)": 0}
    for d in drains:
        c = d["condition_pct"]
        if c >= 90:
            cond_bins["Excellent (90-100)"] += 1
        elif c >= 75:
            cond_bins["Good (75-89)"] += 1
        elif c >= 60:
            cond_bins["Fair (60-74)"] += 1
        else:
            cond_bins["Critical (<60)"] += 1
            
    # 2. Citizen complaint categories count
    categories_count = {}
    for r in reports:
        if r["duplicate_of"] is None: # Only count unique ones
            cat = r["category"]
            categories_count[cat] = categories_count.get(cat, 0) + 1
            
    # 3. Maintenance effectiveness: average cost vs average risk reduction
    logs = get_maintenance_logs()
    avg_cost = sum(l["cost_usd"] for l in logs if l["status"] == "Completed") / len([l for l in logs if l["status"] == "Completed"]) if logs else 0.0
    avg_reduction = sum(l["risk_reduction_pct"] for l in logs if l["status"] == "Completed") / len([l for l in logs if l["status"] == "Completed"]) if logs else 0.0
    
    # 4. Historical rainfall vs flooding frequency
    rain_floods = {}
    for h in history:
        # Group by rainfall level binned to nearest 10mm
        rain_bin = int(round(h["rainfall_mm"] / 10.0) * 10)
        if rain_bin not in rain_floods:
            rain_floods[rain_bin] = {"total_events": 0, "overflows": 0}
        rain_floods[rain_bin]["total_events"] += 1
        if h["overflow_occurred"] == 1:
            rain_floods[rain_bin]["overflows"] += 1
            
    rain_trend = []
    for r_bin in sorted(rain_floods.keys()):
        stats = rain_floods[r_bin]
        pct = (stats["overflows"] / stats["total_events"]) * 100.0 if stats["total_events"] > 0 else 0.0
        rain_trend.append({
            "rainfall_bin_mm": r_bin,
            "overflow_rate_pct": round(pct, 1),
            "total_incidents": stats["overflows"]
        })
        
    return {
        "drain_condition_distribution": [{"status": k, "count": v} for k, v in cond_bins.items()],
        "citizen_complaint_categories": [{"category": k, "count": v} for k, v in categories_count.items()],
        "maintenance_metrics": {
            "average_cost_usd": round(avg_cost, 2),
            "average_risk_reduction_pct": round(avg_reduction, 1)
        },
        "rainfall_flood_trend": rain_trend,
        "forecast": forecast
    }

# Mount static frontend files if built
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
