import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.core.models import PriceProposal, StoreProduct

class StoreExecutorAgent:
    def __init__(self, catalog_path: str):
        self.catalog_path = Path(catalog_path)
        self.backup_path = self.catalog_path.with_suffix(".backup.json")

    def create_backup(self) -> None:
        """Creates an immediate snapshot before any mutation for zero-risk rollback."""
        if self.catalog_path.exists():
            shutil.copy2(self.catalog_path, self.backup_path)

    def rollback(self) -> bool:
        """Restores store catalog from the last valid backup."""
        if self.backup_path.exists():
            shutil.copy2(self.backup_path, self.catalog_path)
            return True
        return False

    def load_catalog_raw(self) -> List[Dict[str, Any]]:
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute_updates(self, approved_proposals: List[PriceProposal]) -> Dict[str, Any]:
        """Applies approved price updates, verifies live state, and returns execution metrics."""
        if not approved_proposals:
            return {"updated_count": 0, "status": "NO_OP", "verified": True}

        # Step 1: Create backup
        self.create_backup()

        raw_items = self.load_catalog_raw()
        proposal_map = {p.sku: p.proposed_price for p in approved_proposals}
        updated_skus = []

        # Step 2: Mutate catalog
        for item in raw_items:
            sku = item.get("sku")
            if sku in proposal_map:
                item["current_price"] = proposal_map[sku]
                updated_skus.append(sku)

        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(raw_items, f, indent=2)

        # Step 3: Self-Verification Step (Re-read and verify)
        verified = self.verify_catalog_state(proposal_map)
        if not verified:
            self.rollback()
            return {
                "updated_count": 0,
                "status": "FAILED_VERIFICATION_ROLLED_BACK",
                "verified": False,
                "updated_skus": []
            }

        return {
            "updated_count": len(updated_skus),
            "status": "SUCCESS",
            "verified": True,
            "updated_skus": updated_skus
        }

    def verify_catalog_state(self, expected_prices: Dict[str, float]) -> bool:
        """Verifies that on-disk prices match the approved target prices."""
        try:
            current_items = self.load_catalog_raw()
            for item in current_items:
                sku = item.get("sku")
                if sku in expected_prices:
                    if item.get("current_price") != expected_prices[sku]:
                        return False
            return True
        except Exception:
            return False