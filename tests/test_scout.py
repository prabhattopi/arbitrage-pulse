from src.core.models import CompetitorListing, StoreProduct
from src.agents.scout import ScoutAgent

def test_competitor_price_cleaning():
    # String with currency symbol should cleanly convert to float
    listing = CompetitorListing(
        competitor_name="TestShop",
        sku="SKU-1",
        price="$129.50",
        in_stock=True
    )
    assert listing.price == 129.50

def test_store_product_floor_price():
    # Cost = 100, min_margin = 20% -> Floor price must be 120.0
    prod = StoreProduct(
        sku="TEST-1",
        title="Sample",
        cost_price=100.0,
        current_price=150.0,
        stock_quantity=10,
        min_margin_pct=20.0
    )
    assert prod.floor_price == 120.0

def test_scout_agent_snapshot_building():
    scout = ScoutAgent(
        catalog_path="src/data/mock_store_catalog.json",
        competitor_path="src/data/mock_competitors.json"
    )
    snapshots = scout.build_market_snapshots()
    assert len(snapshots) == 3

    # Check ANC headphones has ApexGizmos and ElectroDirect
    anc_snapshot = next(s for s in snapshots if s.product.sku == "TECH-ANC-001")
    assert len(anc_snapshot.competitors) == 2
    assert anc_snapshot.lowest_competitor_price == 79.99