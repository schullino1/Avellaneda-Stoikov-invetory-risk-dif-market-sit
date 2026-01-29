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
    sigma: float,          # σ: Preisvolatilität in Preis-Einheiten (Paper)
    inventory: float,      # q: aktuelles Inventory (positiv = long, negativ = short)
    gamma: float,          # γ: Risikoaversion
    k: float,              # k: Liquidity/Depth-Parameter im Arrival-Rate Modell
    tau_seconds: float,    # tau = (T - t) in SEKUNDEN (Paper arbeitet in kontinuierlicher Zeit)
) -> tuple[Quote, float, float]:
    """
    Avellaneda–Stoikov (Paper-nahe Version), in Preis-Einheiten:

    Reservation Price (Indifferenzpreis):
        r = s - q * γ * σ^2 * τ
    Intuition:
        - Wenn q > 0 (long), wird r nach unten verschoben -> du willst eher verkaufen.
        - Wenn q < 0 (short), wird r nach oben verschoben -> du willst eher kaufen.

    Optimaler totaler Spread (Preis-Einheiten):
        Δ = γ * σ^2 * τ + (2/γ) * ln(1 + γ/k)

    Quotes:
        bid = r - Δ/2
        ask = r + Δ/2
    """
    # 1) Reservation Price r(s,t,q) – “fairer” Preis aus Sicht des Market Makers unter Inventory-Risiko
    r = mid - inventory * gamma * (sigma ** 2) * tau_seconds

    # 2) Total Spread Δ – Risiko- + Liquiditätskomponente
    spread = gamma * (sigma ** 2) * tau_seconds + (2.0 / gamma) * math.log(1.0 + gamma / k)

    # 3) Halbspread -> Bid/Ask um r
    half_spread = 0.5 * spread
    bid = r - half_spread
    ask = r + half_spread

    # Invariant: bid < ask (numerische Sicherheit)
    if bid >= ask:
        eps = 1e-6
        bid = mid - eps
        ask = mid + eps
        r = mid
        half_spread = eps

    return Quote(bid=bid, ask=ask), r, half_spread
