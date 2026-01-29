from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .config import MMConfig
from .price_process import simulate_rw_paper
from .strategy import make_quote_as, Quote

@dataclass
class Trade:
    t: int
    side: str   # "buy" or "sell" from the market maker perspective
    price: float
    size: float
    mid: float

def fill_prob_paper(A: float, k: float, delta: float, dt: float) -> float:
    """
    Paper: Ankunftsrate λ(δ) = A * exp(-k*δ)
    Approximation: P(fill in dt) ≈ λ(δ) * dt   (für kleines dt)
    """
    lam = A * math.exp(-k * max(delta, 0.0))
    return min(lam * dt, 1.0)

def run_simulation(cfg: MMConfig) -> Dict[str, Any]:
    rng = np.random.default_rng(cfg.seed)

    mids = simulate_rw_paper(
        s0=cfg.s0,
        mu=cfg.mu,
        sigma=cfg.sigma,
        dt=cfg.dt_seconds,
        n_steps=cfg.n_steps,
        rng=rng,
    )

    inventory = 0.0
    cash = 0.0
    trades: List[Trade] = []
    inventory_path = []
    pnl_path = []
    bid_path = []
    ask_path = []
    r_path = []
    half_spread_path = []

    dt = cfg.dt_seconds

    for t in range(cfg.n_steps):
        mid = float(mids[t])

        T_steps = int(round(cfg.T_seconds / cfg.dt_seconds))
        if T_steps <= 0:
            raise ValueError("T_seconds too small vs dt_seconds")

        t_in_period = t if cfg.tau_mode == "session" else (t % T_steps)

        t_seconds = t * cfg.dt_seconds
        tau_seconds = max(cfg.T_seconds - t_seconds, 0.0)  # Restzeit bis T

        q, r, half_spread = make_quote_as(
            mid=mid,
            sigma=cfg.sigma,
            inventory=inventory,
            gamma=cfg.gamma,
            k=cfg.k,
            tau_seconds=tau_seconds,
        )

        # Logging für Plot/Erklärung
        bid_path.append(q.bid)
        ask_path.append(q.ask)
        r_path.append(r)
        half_spread_path.append(half_spread)

        delta_bid = max(mid - q.bid, 0.0)
        delta_ask = max(q.ask - mid, 0.0)

        p_bid = fill_prob_paper(cfg.A, cfg.k, delta_bid, dt)
        p_ask = fill_prob_paper(cfg.A, cfg.k, delta_ask, dt)
    
        inventory_path.append(inventory)
        pnl_path.append(cash + inventory * mid)

    ts = pd.DataFrame({"t": range(cfg.n_steps),"mid": mids,"r": r_path,"bid": bid_path,"ask": ask_path,"half_spread": half_spread_path,"inventory": inventory_path,"pnl": pnl_path,})
    trades_df = pd.DataFrame([tr.__dict__ for tr in trades])

    final_pnl = cash + inventory * float(mids[-1])

    return {
        "timeseries": ts,
        "trades": trades_df,
        "final_inventory": inventory,
        "final_cash": cash,
        "final_pnl": float(final_pnl),
    }
