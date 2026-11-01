import json
from src.orchestrator import ArbitragePulseOrchestrator

def test_full_pipeline_cycle(tmp_path):
    catalog_file = tmp_path / "test_catalog.json"
    competitor_file = tmp_path / "test_competitors.json"
    log_dir = tmp_path / "logs"

    catalog_data = [
        {"sku": "SKU-A", "title": "Headphones", "cost_price": 50.0, "current_price": 90.0, "stock_quantity": 20, "min_margin_pct": 20.0},
        {"sku": "SKU-B", "title": "Mug", "cost_price": 10.0, "current_price": 25.0, "stock_quantity": 10, "min_margin_pct": 10.0}
    ]
    competitor_data = [
        {"competitor_name": "RivalStore", "sku": "SKU-A", "price": 82.0, "in_stock": True},
        {"competitor_name": "RivalStore", "sku": "SKU-B", "price": 11.0, "in_stock": True}  # Undercutting would violate SKU-B floor (11.0)
    ]

    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f)
    with open(competitor_file, "w", encoding="utf-8") as f:
        json.dump(competitor_data, f)

    orchestrator = ArbitragePulseOrchestrator(
        catalog_path=str(catalog_file),
        competitor_path=str(competitor_file),
        log_dir=str(log_dir)
    )

    # Run non-interactive cycle with auto_approve=True
    result = orchestrator.run_cycle(auto_approve=True, dry_run=False, interactive=False)

    assert result["total_evaluated"] == 2
    # Only SKU-A should be approved (SKU-B violates floor margin and gets blocked)
    assert result["approved_count"] == 1
    assert result["execution"]["status"] == "SUCCESS"
    assert result["execution"]["verified"] is True
    assert result["execution"]["updated_count"] == 1

    # Verify on-disk mutation
    with open(catalog_file, "r", encoding="utf-8") as f:
        final_catalog = json.load(f)

    sku_a = next(i for i in final_catalog if i["sku"] == "SKU-A")
    sku_b = next(i for i in final_catalog if i["sku"] == "SKU-B")

    # SKU-A undercut to 81.50 (82.0 - 0.50)
    assert sku_a["current_price"] == 81.50
    # SKU-B preserved at original 25.0
    assert sku_b["current_price"] == 25.0

    # Verify audit log was recorded
    log_file = log_dir / "agent_work_log.json"
    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        logs = json.load(f)
    assert len(logs) == 2