"""
run_scenarios.py

Ziel:
- Beantwortet die Forschungsfrage: Wie verändert γ (Risikoaversion) den Trade-off zwischen
  Profitabilität (PnL) und Inventory-/Tail-Risk (z.B. VaR) unter verschiedenen Marktregimen?
- Dafür laufen wir eine Grid-Search:
    Szenarien (mu/sigma)  ×  Gamma-Werte
- Pro Run schreiben wir einen auditierbaren Output-Ordner:
    config_used.yaml, timeseries.csv, trades.csv, summary.json
- Zusätzlich schreiben wir eine zentrale Ergebnis-Tabelle:
    results/.../experiment_summary.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from mm_sandbox.io import load_config, write_outputs
from mm_sandbox.simulator import run_simulation
from mm_sandbox.metrics import compute_kpis, compute_var_inventory_horizon


def run_one(cfg, outdir: Path) -> dict:
    """
    Führt genau einen Simulations-Run aus und schreibt die Outputs in einen Run-Ordner.

    cfg   : MMConfig (pydantic model) – enthält alle Parameter (dt, T, mu, sigma, gamma, A, k, ...)
    outdir: Zielordner für auditierbare Outputs (pro Run ein eigener Ordner)
    """
    # 1) Simulation ausführen (Preisprozess + Quotes + Fills -> Timeseries & Trades)
    res = run_simulation(cfg)

    # 2) KPIs berechnen (PnL, Trades, Inventory, adverse selection proxy, ...)
    horizon_steps = getattr(cfg, "adverse_horizon_steps", 10)
    kpis = compute_kpis(
        timeseries=res["timeseries"],
        trades=res["trades"],
        final_pnl=res["final_pnl"],
        final_inventory=res["final_inventory"],
        horizon_steps=horizon_steps,
    )

    # 3) VaR über kurzen Horizont (Inventory-Risk Proxy)
    #    (z.B. 0.05s im Paper-Setup oder 60s in früheren Toy-Setups)
    var_horizon_seconds = getattr(cfg, "var_horizon_seconds", 0.05)
    var_levels = getattr(cfg, "var_levels", (0.95, 0.99))
    kpis.update(
        compute_var_inventory_horizon(
            ts=res["timeseries"],
            horizon_seconds=var_horizon_seconds,
            dt_seconds=cfg.dt_seconds,
            levels=var_levels,
        )
    )

    # 4) Auditierbare Outputs schreiben: Config + Timeseries + Trades + KPI Summary
    write_outputs(outdir, cfg, res["timeseries"], res["trades"], kpis)

    return kpis


def main() -> None:
    ap = argparse.ArgumentParser()

    # Base-Config: eine YAML als “Single Source of Truth”
    # Szenarien (mu/sigma) und gamma-sweep machen wir im Code.
    ap.add_argument(
        "--base_config",
        default="config/base.yaml",
        help="Pfad zur Base-Config (YAML). Szenarien & gamma sweep werden im Code definiert.",
    )

    # Output root: hier entstehen die Run-Ordner + Summary CSV
    ap.add_argument(
        "--outdir",
        default="results/experiment",
        help="Output root directory (z.B. results/experiment).",
    )

    args = ap.parse_args()

    base_cfg_path = Path(args.base_config)
    out_root = Path(args.outdir)
    out_root.mkdir(parents=True, exist_ok=True)

    # 1) Base-Config laden (Paper-Baseline Parameter + Defaults)
    #    Wichtig: diese Config enthält z.B. A, k, dt, T, s0, fee_bps, ...
    cfg = load_config(base_cfg_path)

    # 2) Definition der Marktregime (nur mu/sigma Overrides)
    #    - calm      : niedrigere Volatilität (ruhiger Markt)
    #    - turbulent : höhere Volatilität (stressiger Markt)
    #    - uptrend   : positiver Drift
    #    - downtrend : negativer Drift
    #
    #    Hinweis: mu ist bei uns in Preis-Einheiten pro Sekunde (arithmetischer Drift).
    scenarios = [
        {"name": "calm",      "mu": 0.0,  "sigma": 2.0},
        {"name": "turbulent", "mu": 0.0,  "sigma": 10.0},
        {"name": "uptrend",   "mu": 10.0,  "sigma": 2.0},
        {"name": "downtrend", "mu": -10.0, "sigma": 2.0},
    ]

    # 3) Gamma-Grid (log-artig gestaffelt -> sinnvoll für Sensitivitätsanalyse)
    #    gamma klein -> risk-neutraler, enger/aktiver
    #    gamma groß  -> risikoaverser, konservativer
    gammas = [0.001, 0.01, 0.05, 0.1, 0.3]

    rows: list[dict] = []

    # 4) Grid-Search: Szenario × Gamma
    for sc in scenarios:
        for g in gammas:
            # pydantic v2: model_copy(deep=True)
            # Falls du v1 nutzt: cfg.copy(deep=True)
            cfg_run = cfg.model_copy(deep=True)

            # Override der Regime-Parameter
            cfg_run.mu = sc["mu"]
            cfg_run.sigma = sc["sigma"]

            # Override der Forschungsvariable
            cfg_run.gamma = g

            # Output-Ordner pro Run (auditierbar, reproduzierbar)
            # Beispiel: results/experiment/calm/gamma_0.1/
            outdir = out_root / sc["name"] / f"gamma_{g}"
            outdir.mkdir(parents=True, exist_ok=True)

            # Run durchführen + KPIs sammeln
            kpis = run_one(cfg_run, outdir)

            # Eine Zeile in die zentrale Summary
            rows.append(
                {
                    "scenario": sc["name"],
                    "gamma": g,
                    **kpis,
                }
            )

    # 5) Zentrale Summary-Tabelle schreiben
    df = pd.DataFrame(rows).sort_values(["scenario", "gamma"])
    df.to_csv(out_root / "experiment_summary.csv", index=False)


if __name__ == "__main__":
    main()
