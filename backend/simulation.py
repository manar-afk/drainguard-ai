import math
from .database import get_all_drains, get_infrastructure

def haversine_distance(lat1, lon1, lat2, lon2):
    # Distance in meters
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamb = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlamb/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def run_flood_simulation(rainfall_mm):
    drains = get_all_drains()
    infrastructures = get_infrastructure()
    
    results = {
        "rainfall_mm": rainfall_mm,
        "summary": {
            "total_drains": len(drains),
            "overflowing_drains_current": 0,
            "overflowing_drains_optimized": 0,
            "affected_roads_current": 0,
            "affected_roads_optimized": 0,
            "affected_markets_current": 0,
            "affected_markets_optimized": 0,
            "residential_impact_current": 0, # count of residential areas
            "residential_impact_optimized": 0,
            "hospitals_at_risk_current": 0,
            "hospitals_at_risk_optimized": 0
        },
        "drains": [],
        "affected_infrastructure": []
    }
    
    affected_infra_current_ids = set()
    affected_infra_opt_ids = set()
    
    for drain in drains:
        lat = drain["latitude"]
        lng = drain["longitude"]
        capacity = drain["capacity_m3s"]
        cond = drain["condition_pct"]
        elev = drain["elevation_m"]
        length = drain["length_m"]
        
        # Current status calculations
        effective_capacity_current = capacity * (cond / 100.0)
        # Runoff coefficient: 0.75 for urban concrete, 0.40 for parks. We use 0.70.
        # Required discharge = area * rain_intensity. Area approximated by length * width.
        # Let's say drainage width is 2m, runoff width factor is 50m.
        # Runoff volume rate: rainfall_mm/1000 * length * 50 / (duration of 3 hours in seconds)
        runoff_factor = 50.0
        duration_seconds = 3 * 3600 # 3 hours monsoon downpour
        required_discharge = (rainfall_mm / 1000.0) * length * runoff_factor * 0.70 / duration_seconds
        
        flow_ratio_current = required_discharge / effective_capacity_current
        overflow_current = 1 if flow_ratio_current > 0.9 else 0
        
        # Optimized status calculations (after 100% cleaning)
        effective_capacity_opt = capacity * 1.0 # 100% capacity
        flow_ratio_opt = required_discharge / effective_capacity_opt
        overflow_opt = 1 if flow_ratio_opt > 0.9 else 0
        
        depth_current = 0.0
        depth_opt = 0.0
        
        if overflow_current:
            depth_current = round((flow_ratio_current - 0.9) * 120.0 + (30.0 - elev)*0.5, 1)
            depth_current = max(5.0, min(180.0, depth_current))
            results["summary"]["overflowing_drains_current"] += 1
            
        if overflow_opt:
            depth_opt = round((flow_ratio_opt - 0.9) * 120.0 + (30.0 - elev)*0.5, 1)
            depth_opt = max(5.0, min(180.0, depth_opt))
            results["summary"]["overflowing_drains_optimized"] += 1
            
        # Determine risk color code
        def get_color_code(overflow, flow_ratio):
            if not overflow:
                return "green" if flow_ratio < 0.5 else "yellow"
            else:
                return "orange" if flow_ratio < 1.3 else "red"
                
        color_current = get_color_code(overflow_current, flow_ratio_current)
        color_opt = get_color_code(overflow_opt, flow_ratio_opt)
        
        drain_result = {
            "id": drain["id"],
            "name": drain["name"],
            "ward": drain["ward"],
            "latitude": lat,
            "longitude": lng,
            "elevation_m": elev,
            "condition_pct": cond,
            "flow_ratio_current": round(flow_ratio_current, 2),
            "flow_ratio_optimized": round(flow_ratio_opt, 2),
            "overflow_current": overflow_current,
            "overflow_optimized": overflow_opt,
            "depth_cm_current": depth_current,
            "depth_cm_optimized": depth_opt,
            "color_current": color_current,
            "color_optimized": color_opt
        }
        results["drains"].append(drain_result)
        
        # Check affected infrastructure (within 400m and elevation-matching)
        for infra in infrastructures:
            infra_lat = infra["latitude"]
            infra_lng = infra["longitude"]
            infra_elev = infra["elevation_m"]
            infra_type = infra["type"]
            infra_id = infra["id"]
            
            dist = haversine_distance(lat, lng, infra_lat, infra_lng)
            
            # If distance is close and infrastructure elevation is low enough compared to water head
            # Elevation of flood water level = drain elevation + water depth (in meters)
            water_level_elev_current = elev + (depth_current / 100.0) if overflow_current else elev
            water_level_elev_opt = elev + (depth_opt / 100.0) if overflow_opt else elev
            
            if dist < 400.0:
                is_affected_current = False
                is_affected_opt = False
                
                # Check current flooding
                if overflow_current and (infra_elev <= water_level_elev_current or (infra_elev - elev) < 0.5):
                    is_affected_current = True
                    affected_infra_current_ids.add(infra_id)
                    
                # Check optimized flooding
                if overflow_opt and (infra_elev <= water_level_elev_opt or (infra_elev - elev) < 0.5):
                    is_affected_opt = True
                    affected_infra_opt_ids.add(infra_id)
                    
                if is_affected_current or is_affected_opt:
                    results["affected_infrastructure"].append({
                        "id": infra_id,
                        "name": infra["name"],
                        "type": infra_type,
                        "latitude": infra_lat,
                        "longitude": infra_lng,
                        "elevation_m": infra_elev,
                        "distance_to_drain_m": round(dist, 1),
                        "affected_by_drain_id": drain["id"],
                        "current_status": "Flooded" if is_affected_current else "Safe",
                        "optimized_status": "Flooded" if is_affected_opt else "Safe"
                    })
                    
    # Calculate summaries
    for infra in infrastructures:
        i_id = infra["id"]
        itype = infra["type"]
        
        curr_aff = i_id in affected_infra_current_ids
        opt_aff = i_id in affected_infra_opt_ids
        
        if curr_aff:
            if itype == "Major Road":
                results["summary"]["affected_roads_current"] += 1
            elif itype == "Market":
                results["summary"]["affected_markets_current"] += 1
            elif itype == "Residential Area":
                results["summary"]["residential_impact_current"] += 1
            elif itype == "Hospital":
                results["summary"]["hospitals_at_risk_current"] += 1
                
        if opt_aff:
            if itype == "Major Road":
                results["summary"]["affected_roads_optimized"] += 1
            elif itype == "Market":
                results["summary"]["affected_markets_optimized"] += 1
            elif itype == "Residential Area":
                results["summary"]["residential_impact_optimized"] += 1
            elif itype == "Hospital":
                results["summary"]["hospitals_at_risk_optimized"] += 1
                
    return results
