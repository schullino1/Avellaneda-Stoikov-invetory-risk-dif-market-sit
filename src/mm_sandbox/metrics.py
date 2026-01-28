from __future__ import annotations

import numpy as np
import pandas as pd


def compute_adverse_selection_proxy(
    trades: pd.DataFrame,
    timeseries: pd.DataFrame,
    horizon_steps: int,
) -> float:
    """
    Adverse selection proxy:
    - After a BUY fill: if the future mid is BELOW the fill price -> likely adverse (picked off)
    - After a SELL fill: if the future mid is ABOVE the fill price -> likely adverse

    Returns share of trades that look adverse (0..1). NaNs are ignored.
    """
    if trades.empty:
        return float("nan")

    mids = timeseries.set_index("t")["mid"]
    future_mid = mids.shift(-horizon_steps)

    def is_adverse(row) -> float:
        t = int(row["t"])
        fm = future_mid.loc[t]
        if pd.isna(fm):
            return np.nan
        price = float(row["price"])
        side = str(row["side"])
        if side == "buy":
            return 1.0 if fm < price else 0.0
        if side == "sell":
            return 1.0 if fm > price else 0.0
        return np.nan

    adverse = trades.apply(is_adverse, axis=1)
    return float(np.nanmean(adverse))


def compute_kpis(
    *,
    timeseries: pd.DataFrame,
    trades: pd.DataFrame,
    final_pnl: float,
    final_inventory: float,
    horizon_steps: int,
) -> dict:
    """
    Compute a compact KPI set for market-making simulations.

    KPI rationale (interview-friendly):
    - PnL: overall result (mark-to-market)
    - Trades: activity / fill intensity outcome
    - Inventory: risk exposure
    - Adverse selection proxy: did price move against us after fills?
    """
    n_trades = int(len(trades))
    inv = float(final_inventory)

    # Inventory distribution needs per-step inventory; for MVP we at least show final inventory and max abs estimate if present
    adverse_rate = compute_adverse_selection_proxy(trades, timeseries, horizon_steps)

    return {
        "final_pnl": float(final_pnl),
        "final_inventory": inv,
        "n_trades": n_trades,
        "adverse_selection_rate": adverse_rate,
    }

def compute_var_inventory_horizon(ts: pd.DataFrame, horizon_seconds: int, dt_seconds: int, levels=(0.95, 0.99)) -> dict:
    """
    Inventory VaR over a fixed holding horizon.
    PnL shock(t) = inventory[t] * (mid[t+h] - mid[t])
    VaR_level = -Quantile(PnL_shock, 1-level)
    """
    if dt_seconds <= 0:
        raise ValueError("dt_seconds must be > 0")

    h = int(round(horizon_seconds / dt_seconds))
    if h < 1:
        raise ValueError("horizon is < 1 step; increase horizon_seconds or reduce dt_seconds")
    if len(ts) <= h:
        raise ValueError("timeseries too short for chosen horizon")

    mid = ts["mid"].to_numpy(dtype=float)
    inv = ts["inventory"].to_numpy(dtype=float)

    shocks = inv[:-h] * (mid[h:] - mid[:-h])  # 60s holding PnL (inventory frozen at t)
    out = {}
    for lvl in levels:
        alpha = 1.0 - float(lvl)
        out[f"var_{int(lvl*100)}_inv_{horizon_seconds}s"] = float(-np.quantile(shocks, alpha))
    return out

def compute_basic_kpis(ts: pd.DataFrame, trades: pd.DataFrame) -> dict:
    # hier packst du deine bestehenden KPIs rein
    return {
        "final_pnl": float(ts["pnl"].iloc[-1]) if "pnl" in ts.columns else None,
        "final_inventory": float(ts["inventory"].iloc[-1]) if "inventory" in ts.columns else None,
        "n_trades": int(len(trades)),
    }