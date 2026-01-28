from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .config import MMConfig
from .price_process import simulate_gbm
from .strategy import make_quote, Quote


@dataclass
class Trade:
    t: int
    side: str   # "buy" or "sell" from the market maker perspective
    price: float
    size: float
    mid: float


def fill_probability(A: float, k: float, delta: float, dt: float) -> float:
    """
    Poisson-arrival fill model:
    intensity lambda(delta) = A * exp(-k * delta)
    P(fill in dt) = 1 - exp(-lambda * dt)

    delta = distance from mid (price units). Further away => lower fill probability.
    """
    lam = A * math.exp(-k * max(delta, 0.0))
    return 1.0 - math.exp(-lam * dt)


def run_simulation(cfg: MMConfig) -> Dict[str, Any]:
    rng = np.random.default_rng(cfg.seed)

    mids = simulate_gbm(
        s0=cfg.s0,
        mu=cfg.mu,
        sigma=cfg.sigma,
        dt_seconds=cfg.dt_seconds,
        n_steps=cfg.n_steps,
        seconds_per_year=cfg.seconds_per_year,
        rng=rng,
    )

    # simple volatility proxy: absolute log returns
    log_rets = np.diff(np.log(mids), prepend=np.log(mids[0]))
    vol_proxy = np.abs(log_rets) * math.sqrt(cfg.seconds_per_year / cfg.dt_seconds)

    inventory = 0.0
    cash = 0.0
    trades: List[Trade] = []
    inventory_path = []
    pnl_path = []
    bid_path = []
    ask_path = []

    dt = cfg.dt_seconds

    for t in range(cfg.n_steps):
        mid = float(mids[t])
        vol_est = float(vol_proxy[t])

        q: Quote = make_quote(
            mid=mid,
            vol_est=vol_est,
            inventory=inventory,
            base_half_spread_bps=cfg.base_half_spread_bps,
            vol_widening_bps=cfg.vol_widening_bps,
            inventory_skew_bps=cfg.inventory_skew_bps,
        )
        
        bid_path.append(q.bid)
        ask_path.append(q.ask)

        # Inventory limits: if too long, prevent further buys; if too short, prevent further sells
        bid_active = inventory < cfg.max_inventory
        ask_active = inventory > -cfg.max_inventory

        delta_bid = max(mid - q.bid, 0.0)
        delta_ask = max(q.ask - mid, 0.0)

        if bid_active:
            p_bid = fill_probability(cfg.A, cfg.k, delta_bid, dt)
            if rng.random() < p_bid:
                price = q.bid
                size = cfg.trade_size
                inventory += size
                cash -= price * size
                cash -= price * size * (cfg.fee_bps / 10_000.0)
                trades.append(Trade(t=t, side="buy", price=price, size=size, mid=mid))

        if ask_active:
            p_ask = fill_probability(cfg.A, cfg.k, delta_ask, dt)
            if rng.random() < p_ask:
                price = q.ask
                size = cfg.trade_size
                inventory -= size
                cash += price * size
                cash -= price * size * (cfg.fee_bps / 10_000.0)
                trades.append(Trade(t=t, side="sell", price=price, size=size, mid=mid))
        
        inventory_path.append(inventory)
        pnl_path.append(cash + inventory * mid)

    ts = pd.DataFrame({"t": range(cfg.n_steps), "mid": mids,"bid": bid_path, "ask": ask_path, "inventory": inventory_path,"pnl": pnl_path,})
    trades_df = pd.DataFrame([tr.__dict__ for tr in trades])

    final_pnl = cash + inventory * float(mids[-1])

    return {
        "timeseries": ts,
        "trades": trades_df,
        "final_inventory": inventory,
        "final_cash": cash,
        "final_pnl": float(final_pnl),
    }
