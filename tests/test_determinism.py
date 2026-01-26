from mm_sandbox.config import MMConfig
from mm_sandbox.simulator import run_simulation


def test_determinism_same_seed_same_result():
    cfg = MMConfig(
        seed=123,
        dt_seconds=1.0,
        n_steps=500,
        trade_size=1.0,
        s0=100.0,
        mu=0.0,
        sigma=0.02,
        seconds_per_year=31536000,
        base_half_spread_bps=5.0,
        vol_widening_bps=30.0,
        inventory_skew_bps=8.0,
        max_inventory=20.0,
        A=1.5,
        k=80.0,
        fee_bps=0.5,
        adverse_horizon_steps=10,
    )
    r1 = run_simulation(cfg)
    r2 = run_simulation(cfg)
    assert r1["final_pnl"] == r2["final_pnl"]
    assert len(r1["trades"]) == len(r2["trades"])
