from typing import List
from src.core.models import MarketSnapshot, PriceProposal, ActionType, ProposalStatus
from src.core.config import settings

class StrategistAgent:
    def __init__(self, undercut_delta: float = 0.50, stockout_hike_pct: float = 8.0):
        self.undercut_delta = undercut_delta
        self.stockout_hike_pct = stockout_hike_pct

    def evaluate_snapshot(self, snapshot: MarketSnapshot) -> PriceProposal:
        product = snapshot.product
        lowest_comp = snapshot.lowest_competitor_price

        # Strategy 1: Competitor In-Stock & cheaper -> Undercut or Match
        if lowest_comp is not None and lowest_comp < product.current_price:
            target_price = round(lowest_comp - self.undercut_delta, 2)
            action = ActionType.PRICE_DROP
            reason = f"Competitor selling at ${lowest_comp:.2f}. Undercutting by ${self.undercut_delta:.2f} to recapture buy-box."

        # Strategy 2: All competitors out of stock -> Arbitrage Price Hike
        elif snapshot.competitors and all(not c.in_stock for c in snapshot.competitors):
            target_price = round(product.current_price * (1 + (self.stockout_hike_pct / 100.0)), 2)
            action = ActionType.PRICE_HIKE
            reason = f"Competitors are OUT OF STOCK. Raising price by {self.stockout_hike_pct}% to capitalize on scarce inventory."

        # Strategy 3: Already competitive or no competitors
        else:
            target_price = product.current_price
            action = ActionType.MAINTAIN
            reason = "Current price is already optimal or competitor prices are higher."

        # ------------------ MARGIN SENTINEL (Self-Checking Verification) ------------------
        margin_pct = round(((target_price - product.cost_price) / target_price) * 100.0, 2)
        price_drop_pct = round(((product.current_price - target_price) / product.current_price) * 100.0, 2) if target_price < product.current_price else 0.0

        # Guardrail 1: Hard Margin Floor Check
        if target_price < product.floor_price:
            return PriceProposal(
                sku=product.sku,
                product_title=product.title,
                old_price=product.current_price,
                proposed_price=product.current_price,  # Keep safe price
                action=ActionType.MAINTAIN,
                status=ProposalStatus.BLOCKED_MARGIN_VIOLATION,
                reasoning=f"BLOCKED: Proposed ${target_price:.2f} violates floor price of ${product.floor_price:.2f} (Cost: ${product.cost_price:.2f}, Min Margin: {product.min_margin_pct}%).",
                profit_margin_pct=round(((product.current_price - product.cost_price) / product.current_price) * 100.0, 2),
                competitor_anchor_price=lowest_comp,
                safety_checks_passed=False
            )

        # Guardrail 2: Volatility / Circuit Breaker Check
        if price_drop_pct > settings.MAX_PRICE_DROP_PCT:
            return PriceProposal(
                sku=product.sku,
                product_title=product.title,
                old_price=product.current_price,
                proposed_price=target_price,
                action=action,
                status=ProposalStatus.FLAGGED,
                reasoning=f"FLAGGED: Proposed price drop of {price_drop_pct:.1f}% exceeds max allowed drop threshold of {settings.MAX_PRICE_DROP_PCT}%. Requires manual confirmation.",
                profit_margin_pct=margin_pct,
                competitor_anchor_price=lowest_comp,
                safety_checks_passed=False
            )

        # Passed all guardrails
        return PriceProposal(
            sku=product.sku,
            product_title=product.title,
            old_price=product.current_price,
            proposed_price=target_price,
            action=action,
            status=ProposalStatus.AUTO_APPROVED,
            reasoning=reason,
            profit_margin_pct=margin_pct,
            competitor_anchor_price=lowest_comp,
            safety_checks_passed=True
        )

    def generate_proposals(self, snapshots: List[MarketSnapshot]) -> List[PriceProposal]:
        return [self.evaluate_snapshot(snapshot) for snapshot in snapshots]