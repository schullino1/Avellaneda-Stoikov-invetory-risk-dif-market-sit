import argparse

from mm_sandbox.io import load_config, write_outputs
from mm_sandbox.simulator import run_simulation
from mm_sandbox.metrics import compute_kpis, compute_var_inventory_horizon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", default="results/run_001")
    args = ap.parse_args()

    cfg = load_config(args.config)
    res = run_simulation(cfg)

    ts = res["timeseries"]
    trades = res["trades"]

    # 1) Deine bestehenden KPIs (inkl. adverse selection etc.)
    horizon_steps = getattr(cfg, "adverse_horizon_steps", 10)
    kpis = compute_kpis(
        timeseries=ts,
        trades=trades,
        final_pnl=res["final_pnl"],
        final_inventory=res["final_inventory"],
        horizon_steps=horizon_steps,
    )

    # 2) VaR(60s) 95% und 99% ergänzen
    var_horizon_seconds = getattr(cfg, "var_horizon_seconds", 60)
    var_levels = getattr(cfg, "var_levels", (0.95, 0.99))
    kpis.update(
        compute_var_inventory_horizon(
            ts=ts,
            horizon_seconds=var_horizon_seconds,
            dt_seconds=cfg.dt_seconds,
            levels=var_levels,
        )
    )

    write_outputs(args.outdir, cfg, ts, trades, kpis)

    print("Run complete.")
    print(kpis)


if __name__ == "__main__":
    main()
