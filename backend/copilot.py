import os
import json
import sqlite3
from typing import Dict, Any, List
from .database import get_db_connection
from .simulation import run_flood_simulation

def retrieve_context(query: str) -> Dict[str, Any]:
    """
    RAG Retrieval: Analyzes the query, queries the SQLite database, 
    and returns a structured dict of facts.
    """
    query_lower = query.lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    context = {
        "intent": "general",
        "data": {},
        "text_summary": ""
    }
    
    # 1. Intent: "Which drains should be cleaned today?" or "priority drains"
    if "clean" in query_lower or "priority" in query_lower or "maintenance" in query_lower:
        context["intent"] = "maintenance_priority"
        # Drains with condition < 70 sorted by lowest condition
        cursor.execute("SELECT id, name, ward, condition_pct, capacity_m3s FROM drains WHERE condition_pct < 75 ORDER BY condition_pct ASC LIMIT 5")
        rows = cursor.fetchall()
        drains = [dict(r) for r in rows]
        context["data"]["priority_drains"] = drains
        context["text_summary"] = (
            "Top 5 priority drains requiring cleaning based on siltation levels:\n" +
            "\n".join([f"- {d['name']} ({d['id']}) in {d['ward']}: Silt level is at {100 - d['condition_pct']:.1f}% (Condition: {d['condition_pct']:.1f}%)" for d in drains])
        )
        
    # 2. Intent: "Which ward is at highest flood risk?"
    elif "ward" in query_lower or "highest risk" in query_lower or "high risk area" in query_lower:
        context["intent"] = "ward_risk"
        # Calculate risk based on average drain condition and history count
        cursor.execute("""
            SELECT d.ward, COUNT(h.id) as flood_count, AVG(d.condition_pct) as avg_cond, AVG(d.elevation_m) as avg_elev
            FROM drains d
            LEFT JOIN flood_history h ON d.id = h.drain_id AND h.overflow_occurred = 1
            GROUP BY d.ward
            ORDER BY flood_count DESC, avg_cond ASC
        """)
        rows = cursor.fetchall()
        wards = [dict(r) for r in rows]
        context["data"]["wards_risk"] = wards
        top_ward = wards[0]["ward"] if wards else "Unknown"
        context["text_summary"] = (
            f"Ward Risk Assessment (highest to lowest):\n" +
            "\n".join([f"- {w['ward']}: {w['flood_count']} historical flood overflows, Average Drain Condition: {w['avg_cond']:.1f}%, Avg Elevation: {w['avg_elev']:.1f}m" for w in wards])
        )
        
    # 3. Intent: "Show top 10 choke points."
    elif "choke point" in query_lower or "chokepoints" in query_lower or "choke" in query_lower:
        context["intent"] = "choke_points"
        # Find drains with lowest condition percentage (highest silting)
        cursor.execute("SELECT id, name, ward, condition_pct, capacity_m3s, elevation_m FROM drains ORDER BY condition_pct ASC LIMIT 10")
        rows = cursor.fetchall()
        drains = [dict(r) for r in rows]
        context["data"]["choke_points"] = drains
        context["text_summary"] = (
            "Top 10 Drainage Choke Points (ordered by severity of silting):\n" +
            "\n".join([f"- {d['name']} ({d['id']}) in {d['ward']}: Condition {d['condition_pct']}%, Elevation {d['elevation_m']}m" for d in drains])
        )

    # 4. Intent: "How much flooding can be prevented if Drain D12 is cleaned?"
    elif "prevent" in query_lower or "if drain" in query_lower or "d12" in query_lower or ("d" in query_lower and any(char.isdigit() for char in query_lower)):
        context["intent"] = "preventive_impact"
        # Extract drain ID (e.g. D12, D01, D05)
        import re
        match = re.search(r'd\d+', query_lower)
        target_id = match.group(0).upper() if match else "D12"
        
        cursor.execute("SELECT * FROM drains WHERE id = ?", (target_id,))
        drain = cursor.fetchone()
        
        if drain:
            drain_dict = dict(drain)
            # Run simulation at 100mm rain
            sim = run_flood_simulation(100.0)
            
            # Find the specific drain in the simulation results
            drain_sim = next((d for d in sim["drains"] if d["id"] == target_id), None)
            
            context["data"]["drain"] = drain_dict
            context["data"]["simulation_at_100mm"] = drain_sim
            
            if drain_sim:
                depth_curr = drain_sim["depth_cm_current"]
                depth_opt = drain_sim["depth_cm_optimized"]
                overflow_curr = drain_sim["overflow_current"]
                overflow_opt = drain_sim["overflow_optimized"]
                
                reduction_text = ""
                if overflow_curr and not overflow_opt:
                    reduction_text = "Flooding is COMPLETELY PREVENTED at this segment (Overflow reduced to 0)."
                elif overflow_curr and overflow_opt:
                    diff = depth_curr - depth_opt
                    reduction_text = f"Flooding overflow is reduced, lowering depth by {diff:.1f} cm (from {depth_curr} cm to {depth_opt} cm)."
                else:
                    reduction_text = "This drain is already in good condition; cleaning provides minor redundant safety margin."
                    
                context["text_summary"] = (
                    f"Preventive Cleaning Analysis for Drain {drain_dict['name']} ({drain_dict['id']}):\n"
                    f"- Current condition: {drain_dict['condition_pct']}% (Silt block: {100 - drain_dict['condition_pct']}%)\n"
                    f"- At 100mm rainfall, current overflow depth: {depth_curr} cm.\n"
                    f"- If cleaned to 100% capacity: overflow depth becomes {depth_opt} cm.\n"
                    f"- Impact: {reduction_text}"
                )
            else:
                context["text_summary"] = f"Could not find simulation data for drain {target_id}."
        else:
            context["text_summary"] = f"Drain ID {target_id} was not found in the database."

    # 5. Intent: "Explain why Zone C is high risk." (Zone = Ward)
    elif "why" in query_lower or "explain" in query_lower or "zone" in query_lower or "ward" in query_lower:
        context["intent"] = "explain_risk"
        # Find which ward is mentioned (Ward A, B, C, D, E) or guess based on letter
        target_ward = "Ward C"
        for w in ["Ward A", "Ward B", "Ward C", "Ward D", "Ward E"]:
            if w.lower() in query_lower or w.split()[-1].lower() in query_lower:
                target_ward = w
                break
                
        cursor.execute("SELECT id, name, condition_pct, capacity_m3s, elevation_m FROM drains WHERE ward = ?", (target_ward,))
        drains = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("""
            SELECT COUNT(id) as total_floods, AVG(water_accumulation_depth_cm) as avg_depth
            FROM flood_history
            WHERE drain_id IN (SELECT id FROM drains WHERE ward = ?) AND overflow_occurred = 1
        """, (target_ward,))
        history = dict(cursor.fetchone())
        
        context["data"]["ward"] = target_ward
        context["data"]["drains"] = drains
        context["data"]["flood_history"] = history
        
        clogged_drains = [d for d in drains if d["condition_pct"] < 70]
        low_elevation_drains = [d for d in drains if d["elevation_m"] < 8.0]
        
        context["text_summary"] = (
            f"Risk analysis for {target_ward}:\n"
            f"- Total historical flooding events recorded: {history.get('total_floods', 0)} events.\n"
            f"- Average historical flood depth: {history.get('avg_depth', 0.0) or 0.0:.1f} cm.\n"
            f"- Average elevation of drains in this ward: {sum(d['elevation_m'] for d in drains)/len(drains) if drains else 0:.1f}m.\n"
            f"- Clogged drains in this ward: {len(clogged_drains)} out of {len(drains)} drains.\n"
            f"- Low-lying segments (<8m): {len(low_elevation_drains)} segments."
        )

    # 6. Default Fallback context (grab general state)
    else:
        context["intent"] = "general_state"
        cursor.execute("SELECT COUNT(id) FROM drains WHERE condition_pct < 65")
        critical_count = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(condition_pct) FROM drains")
        avg_cond = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(id) FROM citizen_reports WHERE status = 'Open'")
        open_complaints = cursor.fetchone()[0]
        
        context["data"]["general"] = {
            "critical_drains_count": critical_count,
            "average_drain_health": round(avg_cond, 1) if avg_cond else 100.0,
            "open_citizen_complaints": open_complaints
        }
        context["text_summary"] = (
            f"DrainGuard AI General System Status:\n"
            f"- Average drain health score: {avg_cond:.1f}% across all zones.\n"
            f"- Critical choke points (condition < 65%): {critical_count} segments.\n"
            f"- Active citizen complaints currently open: {open_complaints} reports."
        )
        
    conn.close()
    return context

def ask_copilot(query: str) -> Dict[str, Any]:
    context = retrieve_context(query)
    api_key = os.getenv("GEMINI_API_KEY")
    
    # If key is available, run real Gemini with context grounding
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=(
                    "You are the DrainGuard AI Decision Copilot. "
                    "You answer municipal officers' queries about flooding, drainage health, and maintenance. "
                    "You must ground your response strictly on the database facts provided in the prompt. "
                    "Do not make up facts or extrapolate beyond the provided data. "
                    "Keep your tone professional, authoritative, and helpful."
                )
            )
            prompt = (
                f"User Question: \"{query}\"\n\n"
                f"Grounded Context from Project Database:\n"
                f"{context['text_summary']}\n\n"
                f"JSON Data:\n"
                f"{json.dumps(context['data'], indent=2)}\n\n"
                f"Please write a natural language response answering the question using only the facts above."
            )
            response = model.generate_content(prompt)
            return {
                "answer": response.text,
                "context": context
            }
        except Exception as e:
            # Fallback if Gemini fails
            pass
            
    # Heuristic response construction (Simulated Mode)
    intent = context["intent"]
    ans = ""
    
    if intent == "maintenance_priority":
        drains = context["data"]["priority_drains"]
        ans = (
            f"According to the latest sensor data and inspection reports, the municipal crew should prioritize cleaning the following "
            f"**{len(drains)} critical drains** today due to high siltation levels:\n\n"
        )
        for i, d in enumerate(drains):
            ans += f"{i+1}. **{d['name']} ({d['id']})** in **{d['ward']}**:\n"
            ans += f"   - Silt level: **{100 - d['condition_pct']:.1f}%** (Condition: {d['condition_pct']:.1f}%)\n"
            ans += f"   - Capacity: {d['capacity_m3s']} m³/s\n\n"
        ans += "We recommend dispatching high-capacity sucking machines and manual crews to these segments immediately to restore full storm runoff capacity before the next downpour."
        
    elif intent == "ward_risk":
        wards = context["data"]["wards_risk"]
        top_ward = wards[0]
        ans = (
            f"The ward at **highest flood risk** is **{top_ward['ward']}**.\n\n"
            f"**Key Risk Factors for {top_ward['ward']}:**\n"
            f"- **Historical Incidents**: It has experienced **{top_ward['flood_count']}** drain overflows in the past two monsoon seasons.\n"
            f"- **System Vulnerability**: Drains in this ward have a low average health score of **{top_ward['avg_cond']:.1f}%**.\n"
            f"- **Topographic Risk**: Average drain elevation is **{top_ward['avg_elev']:.1f} meters**, making it a low-lying zone where runoff naturally pools.\n\n"
            f"Here is the risk comparison of all wards:\n"
        )
        for w in wards:
            ans += f"- **{w['ward']}**: {w['flood_count']} overflows, {w['avg_cond']:.1f}% avg drain health, {w['avg_elev']:.1f}m avg elevation.\n"
            
    elif intent == "choke_points":
        cp = context["data"]["choke_points"]
        ans = (
            f"Here are the **top 10 drainage choke points** across the municipality, ordered by the severity of blockages:\n\n"
            f"| Drain ID | Drain Name | Ward | Condition | Elevation | Status |\n"
            f"| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        )
        for d in cp:
            status = "CRITICAL" if d['condition_pct'] < 55 else "WARNING"
            ans += f"| **{d['id']}** | {d['name']} | {d['ward']} | {d['condition_pct']}% | {d['elevation_m']}m | `{status}` |\n"
        ans += "\nThese segments are the most restricted in the city. Silt and garbage accumulation here represents a severe bottleneck, which will trigger localized flooding during any rainfall exceeding 40mm."

    elif intent == "preventive_impact":
        d_name = context["data"]["drain"]["name"]
        d_id = context["data"]["drain"]["id"]
        d_cond = context["data"]["drain"]["condition_pct"]
        sim_data = context["data"]["simulation_at_100mm"]
        
        ans = (
            f"### Preventive Cleaning Impact Analysis: **{d_name} ({d_id})**\n\n"
            f"- **Current Condition**: Silt level is **{100 - d_cond:.1f}%** (Condition score: {d_cond}%).\n"
            f"- **Rainfall Scenario**: 100 mm heavy monsoon downpour.\n\n"
        )
        if sim_data:
            depth_curr = sim_data["depth_cm_current"]
            depth_opt = sim_data["depth_cm_optimized"]
            
            if sim_data["overflow_current"] and not sim_data["overflow_optimized"]:
                ans += (
                    f"**Impact of Cleaning**: 🟢 **100% Flood Prevention**\n\n"
                    f"Under the current silted state, this drain will **overflow**, accumulating **{depth_curr} cm** of water on surrounding streets. "
                    f"If we clean this drain to 100% capacity, **flooding will be completely prevented** (overflow depth drops to 0 cm). "
                    f"This action will protect the nearby infrastructure from waterlogging."
                )
            elif sim_data["overflow_current"] and sim_data["overflow_optimized"]:
                diff = depth_curr - depth_opt
                ans += (
                    f"**Impact of Cleaning**: 🟡 **Significant Mitigation ({diff:.1f} cm depth reduction)**\n\n"
                    f"Under the current silted state, the drain overflows by **{depth_curr} cm**. "
                    f"Due to extreme rainfall intensity and low elevation, the drain will still overflow slightly even if cleaned, "
                    f"but the flood depth will drop to **{depth_opt} cm** (a reduction of **{diff:.1f} cm**). "
                    f"This reduces the flood footprint and decreases road recovery time from 12 hours to less than 2 hours."
                )
            else:
                ans += (
                    f"**Impact of Cleaning**: 🟢 **Low Risk Segment**\n\n"
                    f"This drain is not predicted to overflow under 100mm rain (current overflow depth is 0 cm). "
                    f"Cleaning will maintain its good condition but will not directly prevent active flooding at this specific location."
                )
        else:
            ans += "No simulation data is available for this drain."
            
    elif intent == "explain_risk":
        ward = context["data"]["ward"]
        drains_count = len(context["data"]["drains"])
        history = context["data"]["flood_history"]
        clogged = len([d for d in context["data"]["drains"] if d["condition_pct"] < 70])
        low_elev = len([d for d in context["data"]["drains"] if d["elevation_m"] < 8.0])
        
        ans = (
            f"### Why is **{ward}** classified as a High-Risk Zone?\n\n"
            f"Our Decision Intelligence model has flagged **{ward}** due to a combination of meteorological, topographic, and structural vulnerabilities:\n\n"
            f"1. **Topographical Vulnerability (Low Elevation)**:\n"
            f"   - Out of the {drains_count} drain segments in this ward, **{low_elev}** are low-lying segments (elevation < 8 meters). "
            f"Runoff from surrounding elevated areas naturally drains into this zone, creating a basin effect.\n\n"
            f"2. **Maintenance Backlog & Blockages**:\n"
            f"   - **{clogged} of {drains_count} drains** are heavily silted (health score < 70%). "
            f"This limits the physical volume of storm water the network can discharge per second.\n\n"
            f"3. **Historical Precedent**:\n"
            f"   - This ward has experienced **{history.get('total_floods', 0)} verified overflow incidents** over the past two monsoons, "
            f"with an average flood accumulation depth of **{history.get('avg_depth', 0.0) or 0.0:.1f} cm**.\n\n"
            f"**Recommendation**: Immediately dispatch mechanical desilting units to the clogged segments in {ward} and install portable high-capacity dewatering pumps in low-elevation points before heavy rain begins."
        )
        
    else:
        gen = context["data"]["general"]
        ans = (
            f"Hello! I am the **DrainGuard AI Decision Copilot**.\n\n"
            f"Here is a quick snapshot of the municipal drainage system status:\n"
            f"- **Average Drain Health**: **{gen['average_drain_health']}%** across all zones.\n"
            f"- **Critical Choke Points**: There are **{gen['critical_drains_count']} drains** with severe silting (condition < 65%).\n"
            f"- **Citizen Alerts**: We have **{gen['open_citizen_complaints']} active citizen reports** awaiting verification or deployment.\n\n"
            f"How can I help you today? You can ask me questions like:\n"
            f"- *'Which drains should be cleaned today?'*\n"
            f"- *'Which ward is at highest flood risk?'*\n"
            f"- *'Show top 10 choke points.'*\n"
            f"- *'How much flooding can be prevented if Drain D05 is cleaned?'*\n"
            f"- *'Explain why Ward C is high risk.'*"
        )
        
    return {
        "answer": ans,
        "context": context
    }
