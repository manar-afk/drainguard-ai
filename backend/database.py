import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "drainguard.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_drains():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drains")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_drain_by_id(drain_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drains WHERE id = ?", (drain_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_drain_condition(drain_id, condition_pct):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE drains 
    SET condition_pct = ?, last_cleaned = ? 
    WHERE id = ?
    """, (condition_pct, datetime.now().strftime("%Y-%m-%d"), drain_id))
    conn.commit()
    conn.close()

def get_flood_history(drain_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if drain_id:
        cursor.execute("SELECT * FROM flood_history WHERE drain_id = ? ORDER BY date DESC", (drain_id,))
    else:
        cursor.execute("SELECT * FROM flood_history ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_weather_forecast():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM weather_forecast ORDER BY date ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_citizen_reports(include_duplicates=True):
    conn = get_db_connection()
    cursor = conn.cursor()
    if include_duplicates:
        cursor.execute("SELECT * FROM citizen_reports ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM citizen_reports WHERE duplicate_of IS NULL ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_citizen_report(text, image_path, audio_path, lat, lng, category, severity, status="Open", duplicate_of=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO citizen_reports (text, image_path, audio_path, latitude, longitude, category, severity, status, created_at, duplicate_of)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (text, image_path, audio_path, lat, lng, category, severity, status, created_at, duplicate_of))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id

def get_infrastructure():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM infrastructure")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_maintenance_logs(drain_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if drain_id:
        cursor.execute("SELECT * FROM maintenance_logs WHERE drain_id = ? ORDER BY date DESC", (drain_id,))
    else:
        cursor.execute("SELECT * FROM maintenance_logs ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_maintenance_log(drain_id, workers_count, equipment_used, cost, risk_reduction, date_str=None, status="Scheduled"):
    conn = get_db_connection()
    cursor = conn.cursor()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
    INSERT INTO maintenance_logs (drain_id, date, workers_count, equipment_used, cost_usd, risk_reduction_pct, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (drain_id, date_str, workers_count, equipment_used, cost, risk_reduction, status))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id
