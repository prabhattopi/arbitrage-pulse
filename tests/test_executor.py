import json
import shutil
from src.core.models import PriceProposal, ActionType, ProposalStatus
from src.agents.executor import StoreExecutorAgent

def test_executor_updates_and_verifies(tmp_path):
    # Setup temporary catalog
    temp_catalog = tmp_path / "catalog.json"
    initial_data = [
        {"sku": "P1", "title": "Headphones", "cost_price": 50.0, "current_price": 90.0, "stock_quantity": 10, "min_margin_pct": 20.0},
        {"sku": "P2", "title": "Watch", "cost_price": 20.0, "current_price": 50.0, "stock_quantity": 5, "min_margin_pct": 15.0}
    ]
    with open(temp_catalog, "w", encoding="utf-8") as f:
        json.dump(initial_data, f)

    executor = StoreExecutorAgent(catalog_path=str(temp_catalog))

    approved_proposal = PriceProposal(
        sku="P1",
        product_title="Headphones",
        old_price=90.0,
        proposed_price=79.99,
        action=ActionType.PRICE_DROP,
        status=ProposalStatus.AUTO_APPROVED,
        reasoning="Competitor undercut",
        profit_margin_pct=37.5,
        safety_checks_passed=True
    )

    result = executor.execute_updates([approved_proposal])

    assert result["status"] == "SUCCESS"
    assert result["verified"] is True
    assert result["updated_count"] == 1

    # Verify disk content
    with open(temp_catalog, "r", encoding="utf-8") as f:
        updated_data = json.load(f)
    p1 = next(item for item in updated_data if item["sku"] == "P1")
    p2 = next(item for item in updated_data if item["sku"] == "P2")
    assert p1["current_price"] == 79.99
    assert p2["current_price"] == 50.0  # P2 remains unchanged

def test_executor_rollback_mechanism(tmp_path):
    temp_catalog = tmp_path / "catalog.json"
    initial_data = [{"sku": "P1", "title": "Item", "cost_price": 10.0, "current_price": 20.0, "stock_quantity": 5, "min_margin_pct": 10.0}]
    with open(temp_catalog, "w", encoding="utf-8") as f:
        json.dump(initial_data, f)

    executor = StoreExecutorAgent(catalog_path=str(temp_catalog))
    executor.create_backup()

    # Tamper with the catalog
    with open(temp_catalog, "w", encoding="utf-8") as f:
        json.dump([{"sku": "P1", "current_price": 999.0}], f)

    # Trigger rollback
    rolled_back = executor.rollback()
    assert rolled_back is True

    # Verify original state was restored
    with open(temp_catalog, "r", encoding="utf-8") as f:
        restored_data = json.load(f)
    assert restored_data[0]["current_price"] == 20.0