import json
from pathlib import Path
from typing import List, Dict
from src.core.models import StoreProduct, CompetitorListing, MarketSnapshot

class ScoutAgent:
    def __init__(self, catalog_path: str, competitor_path: str):
        self.catalog_path = Path(catalog_path)
        self.competitor_path = Path(competitor_path)

    def load_store_catalog(self) -> Dict[str, StoreProduct]:
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog file missing at {self.catalog_path}")
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return {item["sku"]: StoreProduct(**item) for item in raw_data}

    def load_competitor_listings(self) -> List[CompetitorListing]:
        if not self.competitor_path.exists():
            raise FileNotFoundError(f"Competitor data missing at {self.competitor_path}")
        with open(self.competitor_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [CompetitorListing(**item) for item in raw_data]

    def build_market_snapshots(self) -> List[MarketSnapshot]:
        catalog = self.load_store_catalog()
        competitors = self.load_competitor_listings()

        snapshots: List[MarketSnapshot] = []
        for sku, product in catalog.items():
            matching_competitors = [c for c in competitors if c.sku == sku]
            snapshots.append(MarketSnapshot(product=product, competitors=matching_competitors))
        return snapshots