import argparse
from pathlib import Path
import pandas as pd

from mm_sandbox.io import load_config, write_outputs
from mm_sandbox.simulator import run_simulation
from mm_sandbox.metrics import compute_kpis


def run_one(cfg_path: Path, out_root: Path) -> dict:
    cfg = load_config(cfg_path)
    res = run_simulation(cfg)
    kpis = compute_kpis(
        timeseries=res["timeseries"],
        trades=res["trades"],
        final_pnl=res["final_pnl"],
        final_inventory=res["final_inventory"],
        horizon_steps=cfg.adverse_horizon_steps,
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
