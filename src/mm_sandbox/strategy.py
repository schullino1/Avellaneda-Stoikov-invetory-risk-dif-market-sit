from __future__ import annotations
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class Quote:
    bid: float
    ask: float

def make_quote_as(
    *,
    mid: float,
    sigma: float,      # volatility estimate (dimensionless, consistent with your sim scale)
    inventory: float,  # q
    gamma: float,      # risk aversion
    kappa: float,      # liquidity parameter (k)
    tau: float,        # remaining time fraction in [0,1]
) -> Quote:
    # Reservation price: r = s - q * gamma * sigma^2 * tau * s
    r = mid - inventory * gamma * (sigma ** 2) * tau * mid

    # Optimal total spread (dimensionless): Δ = gamma*sigma^2*tau + (2/gamma)*ln(1+gamma/kappa)
    # Convert to price units by multiplying by mid
    spread_frac = gamma * (sigma ** 2) * tau + (2.0 / gamma) * math.log(1.0 + gamma / kappa)
    half_spread = 0.5 * spread_frac * mid

    bid = r - half_spread
    ask = r + half_spread

    if bid >= ask:
        bid = mid * (1 - 1e-6)
        ask = mid * (1 + 1e-6)

    return Quote(bid=bid, ask=ask)
