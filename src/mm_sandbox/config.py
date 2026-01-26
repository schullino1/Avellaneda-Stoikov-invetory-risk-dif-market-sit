from __future__ import annotations
from pydantic import BaseModel, Field


class MMConfig(BaseModel):
    seed: int = 42

    dt_seconds: float = Field(gt=0)
    n_steps: int = Field(gt=10)
    trade_size: float = Field(gt=0)

    s0: float = Field(gt=0)
    mu: float
    sigma: float = Field(ge=0)
    seconds_per_year: int = Field(gt=0)

    base_half_spread_bps: float = Field(ge=0)
    vol_widening_bps: float = Field(ge=0)
    inventory_skew_bps: float = Field(ge=0)
    max_inventory: float = Field(gt=0)

    A: float = Field(gt=0)
    k: float = Field(gt=0)
    fee_bps: float = Field(ge=0)

    adverse_horizon_steps: int = Field(ge=1)
