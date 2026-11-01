from src.core.models import StoreProduct, CompetitorListing, MarketSnapshot, ActionType, ProposalStatus
from src.agents.strategist import StrategistAgent

def test_undercut_strategy_when_safe():
    # Cost 50, Floor 60, Current 90. Competitor is at 80.
    # Should undercut to 79.50 (Margin sentinel should approve).
    product = StoreProduct(sku="P1", title="Item 1", cost_price=50.0, current_price=90.0, stock_quantity=10, min_margin_pct=20.0)
    comp = CompetitorListing(competitor_name="Rival", sku="P1", price=80.0, in_stock=True)
    snapshot = MarketSnapshot(product=product, competitors=[comp])

    agent = StrategistAgent(undercut_delta=0.50)
    proposal = agent.evaluate_snapshot(snapshot)

    assert proposal.action == ActionType.PRICE_DROP
    assert proposal.proposed_price == 79.50
    assert proposal.status == ProposalStatus.AUTO_APPROVED
    assert proposal.safety_checks_passed is True

def test_stockout_hike_strategy():
    # Competitor out of stock. Should hike price by 8%.
    product = StoreProduct(sku="P2", title="Item 2", cost_price=20.0, current_price=50.0, stock_quantity=10, min_margin_pct=20.0)
    comp = CompetitorListing(competitor_name="Rival", sku="P2", price=45.0, in_stock=False)
    snapshot = MarketSnapshot(product=product, competitors=[comp])

    agent = StrategistAgent(stockout_hike_pct=10.0)
    proposal = agent.evaluate_snapshot(snapshot)

    assert proposal.action == ActionType.PRICE_HIKE
    assert proposal.proposed_price == 55.0  # 50 + 10%
    assert proposal.status == ProposalStatus.AUTO_APPROVED

def test_sentinel_blocks_margin_violation():
    # Cost 50, Floor 60. Competitor is dumping at 45.
    # Undercutting would mean 44.50 (Loss!). Sentinel must block this.
    product = StoreProduct(sku="P3", title="Item 3", cost_price=50.0, current_price=90.0, stock_quantity=10, min_margin_pct=20.0)
    comp = CompetitorListing(competitor_name="CrazyDiscounter", sku="P3", price=45.0, in_stock=True)
    snapshot = MarketSnapshot(product=product, competitors=[comp])

    agent = StrategistAgent(undercut_delta=0.50)
    proposal = agent.evaluate_snapshot(snapshot)

    assert proposal.status == ProposalStatus.BLOCKED_MARGIN_VIOLATION
    assert proposal.safety_checks_passed is False
    assert proposal.proposed_price == 90.0  # Kept original safe price