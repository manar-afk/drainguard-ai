import sqlite3
import random
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "drainguard.db")

# Bounding box for simulation: Mumbai suburb (bandra/kurla area)
# Center: Lat 19.0760, Lng 72.8777
LAT_CENTER = 19.0760
LNG_CENTER = 72.8777

WARDS = ["Ward A", "Ward B", "Ward C", "Ward D", "Ward E"]
DRAIN_TYPES = ["Open Main Drain", "Closed Storm Sewer", "Natural Outflow Channel", "Box Drain"]
INFRA_TYPES = ["School", "Hospital", "Market", "Residential Area", "Major Road"]
REPORT_CATEGORIES = [
    "Garbage Blockage", "Silt Accumulation", "Broken Cover", 
    "Encroachment", "Vegetation Overgrowth", "Drain Collapse"
]
SEVERITIES = ["Low", "Medium", "High", "Critical"]

def get_elevation(lat, lng):
    # Simulate topographic elevation (5m to 25m)
    # Wards with lower average elevations will be more prone to flooding
    # We create a simple mathematical valley structure
    dist_from_river = abs(lng - 72.8600) + abs(lat - 19.0700)
    elev = 5.0 + dist_from_river * 200.0
    return round(max(2.0, min(30.0, elev)), 2)

def generate_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS maintenance_logs")
    cursor.execute("DROP TABLE IF EXISTS citizen_reports")
    cursor.execute("DROP TABLE IF EXISTS infrastructure")
    cursor.execute("DROP TABLE IF EXISTS weather_forecast")
    cursor.execute("DROP TABLE IF EXISTS flood_history")
    cursor.execute("DROP TABLE IF EXISTS drains")

    # Create tables
    cursor.execute("""
    CREATE TABLE drains (
        id TEXT PRIMARY KEY,
        name TEXT,
        ward TEXT,
        type TEXT,
        capacity_m3s REAL,
        current_flow_pct REAL,
        condition_pct REAL,
        latitude REAL,
        longitude REAL,
        elevation_m REAL,
        length_m REAL,
        last_cleaned TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE flood_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drain_id TEXT,
        date TEXT,
        rainfall_mm REAL,
        overflow_occurred INTEGER,
        severity TEXT,
        flood_area_sqm REAL,
        water_accumulation_depth_cm REAL,
        confidence_score REAL,
        FOREIGN KEY(drain_id) REFERENCES drains(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE weather_forecast (
        date TEXT PRIMARY KEY,
        rainfall_mm REAL,
        temperature_c REAL,
        humidity_pct REAL,
        wind_speed_kmh REAL,
        alert_level TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE citizen_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        image_path TEXT,
        audio_path TEXT,
        latitude REAL,
        longitude REAL,
        category TEXT,
        severity TEXT,
        status TEXT,
        created_at TEXT,
        duplicate_of INTEGER,
        FOREIGN KEY(duplicate_of) REFERENCES citizen_reports(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE infrastructure (
        id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT,
        latitude REAL,
        longitude REAL,
        ward TEXT,
        elevation_m REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE maintenance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drain_id TEXT,
        date TEXT,
        workers_count INTEGER,
        equipment_used TEXT,
        cost_usd REAL,
        risk_reduction_pct REAL,
        status TEXT,
        FOREIGN KEY(drain_id) REFERENCES drains(id)
    )
    """)

    # 1. Generate Drains (30 items)
    drains = []
    drain_names_pool = [
        "LBS Marg Storm Conduit", "Kurla West Main Drain", "BKC Link Drain", "Sion Lowland Outfall",
        "Mithi River Outlet Canal", "Dharavi Sector 3 Sewer", "Santacruz East Trunk Line",
        "Bandra Station Arterial", "CST Road Box Drain", "Kalina University Outlet",
        "Chembur North Relief Channel", "Ghatkopar West Highway Drain", "Vikhroli Lowland Collector",
        "Kurla Station Collector", "Nehru Nagar Main Drain", "Chunabhatti Marsh Outlet",
        "Tilak Nagar Storm Sewer", "Koliwada Fishing Creek Drain", "Pratiksha Nagar Outlet",
        "Wadala Saltpan Discharger", "Mahim Bay Storm Channel", "Matunga West Outflow",
        "Parel Low-lying Box Drain", "Elphinstone Road Sewer", "Worli Nullah Bypass",
        "Dadar TT Box Drain", "Sion Station Main Conduit", "Khar Subway Bypass Channel",
        "Santacruz Subway Arterial", "Milan Subway Outflow Canal"
    ]

    for i, name in enumerate(drain_names_pool):
        drain_id = f"D{i+1:02d}"
        ward = WARDS[i % len(WARDS)]
        drain_type = DRAIN_TYPES[random.randint(0, len(DRAIN_TYPES)-1)]
        capacity = round(random.uniform(1.5, 12.0), 2)
        current_flow = round(random.uniform(15.0, 75.0), 2)
        condition = round(random.uniform(35.0, 95.0), 2)
        
        # Jitter coordinates around the center
        lat = LAT_CENTER + random.uniform(-0.02, 0.02)
        lng = LNG_CENTER + random.uniform(-0.02, 0.02)
        elev = get_elevation(lat, lng)
        length = round(random.uniform(300, 2500), 1)
        
        days_ago = random.randint(5, 120)
        last_cleaned = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        drains.append((drain_id, name, ward, drain_type, capacity, current_flow, condition, lat, lng, elev, length, last_cleaned))

    cursor.executemany("""
    INSERT INTO drains VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, drains)

    # 2. Generate Infrastructure (50 items)
    infra = []
    infra_names = {
        "School": ["National Public School", "St. Xavier Academy", "Municipal High School", "Little Angels Academy", "Pioneer Tech Institute", "Arya Girls High School"],
        "Hospital": ["City General Hospital", "Apex Trauma Care", "LifeLine Multispeciality", "Municipal Maternity Home", "Caring Touch Clinic", "Holy Cross Hospital"],
        "Market": ["Bandra Retail Bazar", "Kurla Vegetable Market", "Sion Wholesale Hub", "Santacruz Station Plaza", "Kalina General Market", "BKC Corporate Hub"],
        "Residential Area": ["Siddharth Colony", "Nehru Nagar Housing Society", "Milan Subway Slums", "Transit Camp Phase 1", "BKC Residences", "Railway Colony", "Green Meadows Enclave"],
        "Major Road": ["LBS Marg Highway", "CST Road", "Sion-Panvel Expressway", "Link Road North", "University Bypass Road", "Station Arterial Road"]
    }

    infra_count = 0
    for itype, names in infra_names.items():
        for name in names:
            for ward in WARDS:
                infra_count += 1
                infra_id = f"INF{infra_count:03d}"
                lat = LAT_CENTER + random.uniform(-0.025, 0.025)
                lng = LNG_CENTER + random.uniform(-0.025, 0.025)
                elev = get_elevation(lat, lng)
                
                # Make residential area or school names unique by appending ward
                full_name = f"{name} ({ward})"
                infra.append((infra_id, full_name, itype, lat, lng, ward, elev))

    cursor.executemany("""
    INSERT INTO infrastructure VALUES (?, ?, ?, ?, ?, ?, ?)
    """, infra)

    # 3. Generate Weather Forecast (7 days starting today)
    forecast = []
    base_date = datetime.now().date()
    forecast_rains = [15.0, 45.0, 110.0, 160.0, 80.0, 25.0, 10.0]  # Standard Monsoon Spike
    for j in range(7):
        date_str = (base_date + timedelta(days=j)).strftime("%Y-%m-%d")
        rain = forecast_rains[j]
        temp = round(random.uniform(26.0, 31.0), 1)
        humidity = round(random.uniform(75.0, 98.0), 1)
        wind = round(random.uniform(10.0, 35.0), 1)
        
        if rain < 20.0:
            alert = "Green"
        elif rain < 70.0:
            alert = "Yellow"
        elif rain < 120.0:
            alert = "Orange"
        else:
            alert = "Red"
            
        forecast.append((date_str, rain, temp, humidity, wind, alert))

    cursor.executemany("""
    INSERT INTO weather_forecast VALUES (?, ?, ?, ?, ?, ?)
    """, forecast)

    # 4. Generate Flood History (~300 records for the past 2 monsoons)
    history = []
    # Monsoon months are roughly June, July, August, September
    # We will simulate 10 heavy rain days in 2024 and 10 in 2025
    rain_events = [
        # Date, rainfall_mm
        # 2024
        ("2024-06-15", 45.0), ("2024-06-28", 125.0), ("2024-07-02", 90.0), 
        ("2024-07-15", 160.0), ("2024-07-22", 55.0), ("2024-08-04", 195.0), 
        ("2024-08-18", 110.0), ("2024-09-02", 65.0), ("2024-09-12", 130.0),
        # 2025
        ("2025-06-10", 35.0), ("2025-06-25", 85.0), ("2025-07-05", 210.0), 
        ("2025-07-18", 140.0), ("2025-07-30", 75.0), ("2025-08-11", 175.0), 
        ("2025-08-25", 100.0), ("2025-09-05", 50.0), ("2025-09-18", 120.0),
    ]

    for date_str, rain in rain_events:
        for d in drains:
            drain_id, _, _, _, capacity, _, condition, _, _, elev, length, _ = d
            
            # Simple overflow likelihood formula:
            # - More rain increases flow
            # - Lower capacity increases overflow likelihood
            # - Lower condition (more blockages) increases overflow likelihood
            # - Lower elevation increases overflow likelihood
            
            effective_capacity = capacity * (condition / 100.0)
            required_discharge = (rain * length * 0.05) / 3600.0  # simple rational method simulation
            
            flow_ratio = required_discharge / effective_capacity
            overflow = 1 if flow_ratio > 0.9 else 0
            
            severity = None
            depth = 0.0
            area = 0.0
            confidence = round(random.uniform(0.85, 0.98), 2)

            if overflow == 1:
                depth = round((flow_ratio - 0.9) * 100.0 + random.uniform(5, 30), 1)
                # Cap depth
                depth = min(150.0, depth)
                
                # Severity based on depth and elevation
                if depth < 15.0:
                    severity = "Low"
                    area = round(random.uniform(50, 200), 1)
                elif depth < 40.0:
                    severity = "Medium"
                    area = round(random.uniform(200, 800), 1)
                elif depth < 80.0:
                    severity = "High"
                    area = round(random.uniform(800, 3000), 1)
                else:
                    severity = "Critical"
                    area = round(random.uniform(3000, 15000), 1)
                    
            history.append((drain_id, date_str, rain, overflow, severity, area, depth, confidence))

    cursor.executemany("""
    INSERT INTO flood_history (drain_id, date, rainfall_mm, overflow_occurred, severity, flood_area_sqm, water_accumulation_depth_cm, confidence_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, history)

    # 5. Generate Citizen Reports (~120 records, some active, some duplicate)
    reports = []
    complaint_texts = {
        "Garbage Blockage": [
            "Heavy plastic waste and bottles dumped inside the drain near the market. Water is starting to pool.",
            "Drain is completely clogged with garbage bags. Municipal trash bin fell into it.",
            "Plastic bottles and trash clogging the main inlet grid."
        ],
        "Silt Accumulation": [
            "Severe mud and black silt accumulation. Silt has filled up 70% of the drain depth.",
            "Constructed silt has not been cleaned from the storm sewer, water flow is restricted.",
            "Mud and construction debris dumped into the drain, blockages visible."
        ],
        "Broken Cover": [
            "The concrete cover of the main pedestrian drain is broken. Risk of accidents during rain.",
            "Iron grating of the storm drain is missing near the school entrance.",
            "Cover has collapsed into the drain chamber, blocking the flow."
        ],
        "Encroachment": [
            "A temporary food stall has extended its platform right over the main storm canal, making maintenance impossible.",
            "Cement wall built over the natural outfall path by a local garage.",
            "Shops extending their concrete floors and covering the open drain line."
        ],
        "Vegetation Overgrowth": [
            "Thick weeds and small wild bushes have grown inside the open drain. Flow is extremely slow.",
            "Wild creepers and vegetation completely blocking the channel outlet.",
            "Vines and grass growing inside the concrete conduit."
        ],
        "Drain Collapse": [
            "The brick sidewall of the drain has collapsed inward. Soil is falling into the channel.",
            "Main pipe joint cracked and leaking storm water. Road above is sinking.",
            "Drainage structural wall cracked and collapsed due to heavy vehicle parking."
        ]
    }

    report_count = 0
    # Let's generate base reports
    base_date_dt = datetime.now() - timedelta(days=20)
    for _ in range(80):
        report_count += 1
        cat = random.choice(REPORT_CATEGORIES)
        text = random.choice(complaint_texts[cat])
        
        lat = LAT_CENTER + random.uniform(-0.018, 0.018)
        lng = LNG_CENTER + random.uniform(-0.018, 0.018)
        
        sev = random.choice(SEVERITIES)
        status = random.choice(["Open", "In Progress", "Resolved"])
        created_at = (base_date_dt + timedelta(days=random.randint(0, 18), hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Audio and Image paths simulation
        image_path = f"/uploads/reports/img_{report_count}.jpg"
        audio_path = f"/uploads/reports/aud_{report_count}.mp3" if random.random() > 0.6 else None
        
        reports.append((text, image_path, audio_path, lat, lng, cat, sev, status, created_at, None))

    cursor.executemany("""
    INSERT INTO citizen_reports (text, image_path, audio_path, latitude, longitude, category, severity, status, created_at, duplicate_of)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, reports)

    # Let's generate duplicate reports (about 20 records) to simulate AI duplicate detection
    cursor.execute("SELECT id, latitude, longitude, category, created_at FROM citizen_reports")
    existing_reports = cursor.fetchall()
    
    duplicates = []
    for _ in range(25):
        # Pick an existing report
        orig = random.choice(existing_reports)
        orig_id, orig_lat, orig_lng, orig_cat, orig_date = orig
        
        # Add slight coordinates jitter to simulate different citizen uploads
        dup_lat = orig_lat + random.uniform(-0.0003, 0.0003)
        dup_lng = orig_lng + random.uniform(-0.0003, 0.0003)
        
        # Parse date and add some minutes/hours
        orig_dt = datetime.strptime(orig_date, "%Y-%m-%d %H:%M:%S")
        dup_dt = orig_dt + timedelta(minutes=random.randint(5, 360))
        dup_date_str = dup_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        dup_texts = [
            f"Already reported, but the {orig_cat.lower()} is still not cleared and causing problems.",
            f"Same issue of {orig_cat.lower()} at this spot. Please fix.",
            f"Water is flooding the road because of this {orig_cat.lower()}.",
            f"Blocked drain at this point. {orig_cat} is blocking the water."
        ]
        text = random.choice(dup_texts)
        image_path = f"/uploads/reports/img_dup_{random.randint(1, 100)}.jpg"
        
        duplicates.append((text, image_path, None, dup_lat, dup_lng, orig_cat, "High", "Open", dup_date_str, orig_id))

    cursor.executemany("""
    INSERT INTO citizen_reports (text, image_path, audio_path, latitude, longitude, category, severity, status, created_at, duplicate_of)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, duplicates)

    # 6. Generate Maintenance Logs (~120 records, historical and scheduled)
    logs = []
    equipments = ["Sucking Machine", "JCB Excavator", "De-silting Crew Tools", "Concrete Mixer", "Trash Grate Spares"]
    
    # Generate past logs (completed)
    for _ in range(90):
        dr = random.choice(drains)
        drain_id = dr[0]
        days_ago = random.randint(10, 150)
        date_str = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        workers = random.randint(3, 12)
        equip = ", ".join(random.sample(equipments, k=random.randint(1, 3)))
        cost = round(workers * random.uniform(50, 120) + random.uniform(100, 1500), 2)
        reduction = round(random.uniform(20.0, 75.0), 2)
        
        logs.append((drain_id, date_str, workers, equip, cost, reduction, "Completed"))

    # Generate upcoming logs (scheduled)
    for _ in range(15):
        dr = random.choice(drains)
        drain_id = dr[0]
        days_ahead = random.randint(1, 10)
        date_str = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        workers = random.randint(4, 15)
        equip = ", ".join(random.sample(equipments, k=random.randint(1, 3)))
        cost = round(workers * random.uniform(60, 140) + random.uniform(200, 2000), 2)
        reduction = round(random.uniform(30.0, 85.0), 2)
        
        logs.append((drain_id, date_str, workers, equip, cost, reduction, "Scheduled"))

    cursor.executemany("""
    INSERT INTO maintenance_logs (drain_id, date, workers_count, equipment_used, cost_usd, risk_reduction_pct, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, logs)

    conn.commit()
    conn.close()
    print("Database generated successfully with synthetic records!")

if __name__ == "__main__":
    generate_db()
