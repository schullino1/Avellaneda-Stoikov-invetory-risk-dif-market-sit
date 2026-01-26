import argparse

from mm_sandbox.io import load_config, write_outputs
from mm_sandbox.simulator import run_simulation
from mm_sandbox.metrics import compute_kpis

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", default="results/run_001")
    args = ap.parse_args()

    cfg = load_config(args.config)
    res = run_simulation(cfg)

    summary = {
        "final_pnl": res["final_pnl"],
        "final_inventory": float(res["final_inventory"]),
        "n_trades": int(len(res["trades"])),
    }

    write_outputs(args.outdir, cfg, res["timeseries"], res["trades"], summary)

    kpis = compute_kpis(
    timeseries=res["timeseries"],
    trades=res["trades"],
    final_pnl=res["final_pnl"],
    final_inventory=res["final_inventory"],
    horizon_steps=cfg.adverse_horizon_steps,
    )

    write_outputs(args.outdir, cfg, res["timeseries"], res["trades"], kpis)

    print("Run complete.")
    print(kpis)

if __name__ == "__main__":
    main()
