"""Decision and ML integrity checks; integration checks use the real saved data."""

import os
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from backend.ml.features import shipment_features, temporal_split
from backend.services.data import ARTIFACTS
from backend.services.inventory import project, scenario


class ProjectionTests(unittest.TestCase):
    def test_receipt_after_shortage_does_not_erase_early_failure(self):
        result = project(20, 10, [{"day": 5, "quantity": 100}], horizon=7)
        self.assertEqual(result["shortage_day"], 3)
        self.assertEqual(result["projected_balance"], 50)
        self.assertEqual(result["shortage"], 20)
        self.assertEqual(result["risk"], "High")

    def test_receipt_on_boundary_prevents_shortage(self):
        result = project(20, 10, [{"day": 3, "quantity": 60}], horizon=7)
        self.assertIsNone(result["shortage_day"])
        self.assertEqual(result["projected_balance"], 10)

    def test_safety_stock_is_threshold_not_supply(self):
        low = project(100, 10, [], horizon=7, safety_stock=10)
        high = project(100, 10, [], horizon=7, safety_stock=40)
        self.assertEqual(low["projected_balance"], high["projected_balance"])
        self.assertEqual((low["risk"], high["risk"]), ("Low", "Medium"))

    def test_replenishment_outside_horizon_has_no_effect(self):
        row = {
            "daily_demand": 10,
            "available": 20,
            "inbound_schedule": [],
            "safety_stock": 0,
            "unit_cost": 2,
        }
        result = scenario(row, 0, 1000, 35, 0)
        self.assertEqual(result["baseline"], result["scenario"])

    def test_no_demand_means_undefined_days_of_supply(self):
        self.assertIsNone(project(100, 0, [])["days_of_supply"])


class LeakageTests(unittest.TestCase):
    def test_post_delivery_fields_cannot_change_features(self):
        frame = pd.DataFrame(
            [
                dict(
                    total_weight_kg=10,
                    total_volume_m3=1,
                    distance_km=500,
                    planned_departure_at="2025-01-01",
                    planned_arrival_at="2025-01-02",
                    transport_mode="ROAD",
                    service_level="STANDARD",
                    carrier_id="c",
                    origin_location_id="a",
                    destination_location_id="b",
                    actual_arrival_at="2025-01-03",
                    delay_hours=24,
                    freight_cost_sek=1000,
                )
            ]
        )
        altered = frame.assign(
            actual_arrival_at="2030-01-01", delay_hours=10000, freight_cost_sek=99999
        )
        assert_frame_equal(shipment_features(frame), shipment_features(altered))

    def test_outcomes_after_cutoff_are_purged(self):
        frame = pd.DataFrame({"planned": pd.date_range("2025-01-01", periods=200, tz="UTC")})
        frame["outcome"] = frame.planned + pd.Timedelta(days=30)
        train, test, cutoff = temporal_split(frame, "planned", "outcome")
        self.assertTrue((train.outcome < cutoff).all())
        self.assertTrue((test.planned >= cutoff).all())
        self.assertLess(len(train), 160)


@unittest.skipUnless(
    (ARTIFACTS / "models.joblib").exists() and (ARTIFACTS / "snapshot.json").exists(),
    "Run demo setup with PostgreSQL access first",
)
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DEMO_OFFLINE"] = "1"
        from fastapi.testclient import TestClient

        from backend.app.main import app

        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_every_core_endpoint_serializes(self):
        for path in [
            "health",
            "tower/overview",
            "tower/shipments",
            "tower/inventory",
            "tower/demand",
            "tower/suppliers",
            "tower/production",
            "tower/models",
            "tower/exceptions",
            "tower/options",
        ]:
            with self.subTest(path=path):
                response = self.client.get("/" + path)
                self.assertEqual(response.status_code, 200, response.text[:100])
                self.assertNotIn("NaN", response.text)

    def test_kpi_denominator_matches_completed_shipments(self):
        overview = self.client.get("/tower/overview").json()
        values = {k["label"]: k["value"] for k in overview["kpis"]}
        self.assertAlmostEqual(values["On-time delivery"] + values["Shipment delay rate"], 100)
        self.assertTrue(overview["source"]["offline"])

    def test_filters_and_detail_are_consistent(self):
        result = self.client.get("/tower/shipments?risk=High&mode=ROAD&limit=5").json()
        self.assertGreater(result["total"], 0)
        for row in result["items"]:
            self.assertEqual(row["risk"], "High")
            self.assertEqual(row["transport_mode"], "ROAD")
            self.assertEqual(
                self.client.get("/tower/shipments/" + row["id"]).json()["id"], row["id"]
            )
        self.assertEqual(self.client.get("/tower/shipments/missing").status_code, 404)

    def test_unknown_and_invalid_scenarios(self):
        self.assertEqual(
            self.client.post(
                "/tower/scenarios/transport", json={"shipment_id": "bad", "distance_km": -1}
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post("/tower/scenarios/transport", json={"shipment_id": "bad"}).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/tower/scenarios/transport", json={"shipment_id": "bad", "carrier_id": "unknown"}
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/tower/scenarios/inventory", json={"inventory_id": "bad", "lead_days": 0}
            ).status_code,
            422,
        )

    def test_transport_identity_and_input_sensitivity(self):
        row = self.client.get("/tower/shipments?limit=1").json()["items"][0]
        unchanged = self.client.post(
            "/tower/scenarios/transport", json={"shipment_id": row["id"]}
        ).json()
        self.assertEqual(unchanged["baseline"]["cost"], unchanged["scenario"]["cost"])
        changed = self.client.post(
            "/tower/scenarios/transport",
            json={"shipment_id": row["id"], "distance_km": row["distance_km"] * 1.2},
        ).json()
        self.assertNotEqual(changed["baseline"]["cost"], changed["scenario"]["cost"])

    def test_forecasts_have_disjoint_history_and_future(self):
        for forecast in self.client.get("/tower/demand").json()["items"]:
            self.assertLess(forecast["history"][-1]["week"], forecast["future"][0]["week"])
            self.assertEqual(sum(h["backtest"] is not None for h in forecast["history"]), 8)
            self.assertGreaterEqual(forecast["metrics"]["mae"], 0)

    def test_model_metrics_match_test_confusion_matrix(self):
        for model in self.client.get("/tower/models").json()["items"]:
            if "confusion_matrix" in model["metrics"]:
                matrix = model["metrics"]["confusion_matrix"]
                count = sum(sum(row) for row in matrix)
                self.assertEqual(count, model["test_rows"])
                self.assertAlmostEqual(
                    (matrix[0][0] + matrix[1][1]) / count, model["metrics"]["accuracy"]
                )

    def test_no_fake_forecast_for_component_inventory(self):
        rows = self.client.get("/tower/inventory").json()["items"]
        unscored = [r for r in rows if r["risk"] == "Not scored"]
        self.assertGreater(len(unscored), 0)
        for row in unscored:
            self.assertIsNone(row["forecast_demand"])
            response = self.client.post(
                "/tower/scenarios/inventory", json={"inventory_id": row["id"]}
            )
            self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
