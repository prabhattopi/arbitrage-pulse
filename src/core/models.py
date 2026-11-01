from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum
class StoreProduct(BaseModel):
    sku: str
    title: str
    cost_price: float = Field(gt=0, description="Product procurement/manufacturing cost")
    current_price: float = Field(gt=0, description="Current selling price on our store")
    stock_quantity: int = Field(ge=0, description="Available inventory")
    min_margin_pct: float = Field(default=15.0, ge=0.0, description="Safety margin constraint")

    @property
    def floor_price(self) -> float:
        """Absolute minimum selling price to preserve margin floor."""
        return round(self.cost_price * (1 + (self.min_margin_pct / 100.0)), 2)


class CompetitorListing(BaseModel):
    competitor_name: str
    sku: str
    price: float = Field(gt=0)
    in_stock: bool = True
    url: Optional[str] = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("price", mode="before")
    @classmethod
    def clean_price(cls, v):
        if isinstance(v, str):
            clean_str = v.replace("$", "").replace("₹", "").replace(",", "").strip()
            return float(clean_str)
        return float(v)


class MarketSnapshot(BaseModel):
    product: StoreProduct
    competitors: List[CompetitorListing] = []

    @property
    def lowest_competitor_price(self) -> Optional[float]:
        in_stock_prices = [c.price for c in self.competitors if c.in_stock]
        return min(in_stock_prices) if in_stock_prices else None



class ActionType(str, Enum):
    PRICE_DROP = "PRICE_DROP"
    PRICE_HIKE = "PRICE_HIKE"
    MAINTAIN = "MAINTAIN"

class ProposalStatus(str, Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    FLAGGED = "FLAGGED"
    BLOCKED_MARGIN_VIOLATION = "BLOCKED_MARGIN_VIOLATION"

class PriceProposal(BaseModel):
    sku: str
    product_title: str
    old_price: float
    proposed_price: float
    action: ActionType
    status: ProposalStatus
    reasoning: str
    profit_margin_pct: float
    competitor_anchor_price: Optional[float] = None
    safety_checks_passed: bool = True        