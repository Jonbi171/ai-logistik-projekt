"""Loads persisted models once and computes one coherent analytical snapshot."""

import os

import joblib

from backend.services.data import ARTIFACTS, load_data
from backend.services.inventory import inventory_risks
from backend.services.overview import exceptions, overview
from backend.services.supply import production, suppliers
from backend.services.transport import shipment_risks


class Tower:
    def __init__(self):
        path = ARTIFACTS / "models.joblib"
        if not path.exists():
            raise RuntimeError(
                "Models are missing. Run python -m backend.ml.train_all first, or use ./start-demo.sh."
            )
        self.bundle = joblib.load(path)
        self.tables, self.source = load_data(os.getenv("DEMO_OFFLINE") == "1")
        self.shipments = shipment_risks(self.tables, self.bundle)
        self.forecasts = self.bundle["forecasts"]
        self.inventory = inventory_risks(self.tables, self.forecasts)
        self.suppliers = suppliers(self.tables, self.bundle)
        self.production = production(self.tables)
        self.exceptions = exceptions(self.shipments, self.inventory, self.suppliers)
        self.overview = overview(
            self.tables,
            self.bundle,
            self.shipments,
            self.inventory,
            self.suppliers,
            self.production,
            self.exceptions,
            self.source,
        )
