import argparse
from pathlib import Path
import pandas as pd

from mm_sandbox.io import load_config, write_outputs
from mm_sandbox.simulator import run_simulation
from mm_sandbox.metrics import compute_kpis, compute_var_inventory_horizon  

def run_one(cfg_path: Path, out_root: Path) -> dict:
    cfg = load_config(cfg_path)
    res = run_simulation(cfg)

    horizon_steps = getattr(cfg, "adverse_horizon_steps", 10)
    kpis = compute_kpis(
        timeseries=res["timeseries"],
        trades=res["trades"],
        final_pnl=res["final_pnl"],
        final_inventory=res["final_inventory"],
        horizon_steps=horizon_steps,
    )

    # VaR (95% + 99%)
    var_horizon_seconds = getattr(cfg, "var_horizon_seconds", 60)
    var_levels = getattr(cfg, "var_levels", (0.95, 0.99))
    kpis.update(
        compute_var_inventory_horizon(
            ts=res["timeseries"],
            horizon_seconds=var_horizon_seconds,
            dt_seconds=cfg.dt_seconds,
            levels=var_levels,
        )
    )

    scenario_name = cfg_path.stem
    outdir = out_root / scenario_name
    write_outputs(outdir, cfg, res["timeseries"], res["trades"], kpis)

    return {"scenario": scenario_name, **kpis}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config_dir", default="config")
    ap.add_argument("--outdir", default="results/scenarios")
    args = ap.parse_args()

    config_dir = Path(args.config_dir)
    out_root = Path(args.outdir)
    out_root.mkdir(parents=True, exist_ok=True)

    rows = []
    for cfg_path in sorted(config_dir.glob("*.yaml")):
        # skip base.yaml if you want
        if cfg_path.name == "base.yaml":
            continue
        rows.append(run_one(cfg_path, out_root))

    df = pd.DataFrame(rows).sort_values("scenario")
    df.to_csv(out_root / "scenario_summary.csv", index=False)
    print(df)


if __name__ == "__main__":
    main()
