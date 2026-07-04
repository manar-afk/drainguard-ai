import unittest
import os
import sys

# Ensure backend folder is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_all_drains, get_weather_forecast, get_citizen_reports
from backend.simulation import run_flood_simulation, haversine_distance
from backend.copilot import retrieve_context, ask_copilot
from backend.agents import DecisionIntelligenceAgent

class TestDrainGuardBackend(unittest.TestCase):
    def test_database_loads(self):
        drains = get_all_drains()
        self.assertGreater(len(drains), 0, "No drains loaded from SQLite.")
        self.assertEqual(drains[0]["id"][0], "D", "Drain IDs should follow format D01, D02...")
        
        forecast = get_weather_forecast()
        self.assertEqual(len(forecast), 7, "Forecast should contain exactly 7 days of predictions.")
        
        reports = get_citizen_reports()
        self.assertGreater(len(reports), 0, "No citizen reports loaded from SQLite.")

    def test_haversine_formula(self):
        # Mumbai Center to slightly north
        d = haversine_distance(19.0760, 72.8777, 19.0800, 72.8777)
        self.assertAlmostEqual(d, 444.78, delta=5.0, msg="Haversine distance calculations are wrong.")

    def test_flood_simulation(self):
        res_50 = run_flood_simulation(50.0)
        res_200 = run_flood_simulation(200.0)
        
        self.assertIn("summary", res_50)
        self.assertIn("drains", res_50)
        
        # 200mm rainfall should cause equal or more overflowing drains than 50mm
        overflow_50 = res_50["summary"]["overflowing_drains_current"]
        overflow_200 = res_200["summary"]["overflowing_drains_current"]
        self.assertGreaterEqual(overflow_200, overflow_50, "Heavy rain should cause equal or more overflows.")
        
        # Optimized desilting should reduce overflows
        opt_200 = res_200["summary"]["overflowing_drains_optimized"]
        self.assertLessEqual(opt_200, overflow_200, "Optimized desilted drainage should have fewer or equal overflows.")

    def test_rag_copilot(self):
        ctx_ward = retrieve_context("Which ward is at highest flood risk?")
        self.assertEqual(ctx_ward["intent"], "ward_risk")
        self.assertIn("wards_risk", ctx_ward["data"])
        
        ctx_choke = retrieve_context("Show top 10 choke points.")
        self.assertEqual(ctx_choke["intent"], "choke_points")
        self.assertGreaterEqual(len(ctx_choke["data"]["choke_points"]), 5)
        
        ans = ask_copilot("Explain why Ward C is high risk.")
        self.assertIn("answer", ans)
        self.assertIsNotNone(ans["answer"])

    def test_multi_agent_workflow(self):
        drains = get_all_drains()
        forecast = get_weather_forecast()
        
        agent = DecisionIntelligenceAgent()
        # Mock run the workflow for the first drain and first forecast day
        res = agent.run_workflow(drains[0], forecast[0], 5)
        
        self.assertIn("flood_risk_index", res)
        self.assertIn("monsoon_readiness_score", res)
        self.assertIn("sub_agents", res)
        self.assertIn("weather", res["sub_agents"])
        self.assertIn("prediction", res["sub_agents"])
        self.assertIn("maintenance", res["sub_agents"])

if __name__ == "__main__":
    unittest.main()
