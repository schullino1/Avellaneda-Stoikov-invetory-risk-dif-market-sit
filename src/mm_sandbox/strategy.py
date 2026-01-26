from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    bid: float
    ask: float


def bps_to_frac(bps: float) -> float:
    """Convert basis points to fraction. 1 bps = 1/10,000."""
    return bps / 10_000.0


def make_quote(
    *,
    mid: float,
    vol_est: float,
    inventory: float,
    base_half_spread_bps: float,
    vol_widening_bps: float,
    inventory_skew_bps: float,
) -> Quote:
    """
    Create bid/ask quotes around a fair value proxy (mid).

    Components:
    1) Base half-spread: baseline compensation for providing liquidity.
    2) Vol widening: in higher volatility, widen to reduce adverse selection risk.
    3) Inventory skew: shift quotes to encourage inventory mean-reversion.

    Interpretation of skew:
    - If inventory is positive (long), we want to sell more and buy less:
      => move both quotes downward (ask becomes easier to hit, bid becomes less attractive)
    """
    half_spread = bps_to_frac(base_half_spread_bps + vol_widening_bps * vol_est) * mid
    skew = bps_to_frac(inventory_skew_bps) * inventory * mid

    bid = mid - half_spread - skew
    ask = mid + half_spread - skew

    # Enforce invariant
    if bid >= ask:
        # Fallback to a minimal spread around mid
        bid = mid * (1 - 1e-6)
        ask = mid * (1 + 1e-6)

    return Quote(bid=bid, ask=ask)
