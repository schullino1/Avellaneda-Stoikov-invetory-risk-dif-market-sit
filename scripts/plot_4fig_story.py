# scripts/plot_4fig_story.py
from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl


# === Project paths ===
ROOT = Path("results/experiment")
OUTDIR = ROOT / "final_figures"
OUTDIR.mkdir(parents=True, exist_ok=True)

# === Scenario setup ===
SCENARIOS = ["calm", "turbulent", "uptrend", "downtrend"]

SCENARIO_TITLES = {
    "calm": "Ruhiger Markt",
    "turbulent": "Volatiler Markt",
    "uptrend": "Aufwärtstrend",
    "downtrend": "Abwärtstrend",
}


# -----------------------------
# Helpers: gamma discovery + colors
# -----------------------------
def collect_all_gammas() -> list[float]:
    """Collect all gamma values from results folder names: gamma_<value>."""
    gammas: set[float] = set()
    for scenario in SCENARIOS:
        scenario_dir = ROOT / scenario
        if not scenario_dir.exists():
            continue
        for p in scenario_dir.iterdir():
            if p.is_dir() and p.name.startswith("gamma_"):
                try:
                    gammas.add(float(p.name.replace("gamma_", "")))
                except ValueError:
                    continue
    return sorted(gammas)


def build_gamma_color_map(gammas: list[float]) -> dict[float, tuple]:
    """
    Deterministic mapping gamma -> color.
    Uses tab10/tab20; if >20, colors repeat (still deterministic).
    """
    cmap = mpl.cm.get_cmap("tab10") if len(gammas) <= 10 else mpl.cm.get_cmap("tab20")
    return {g: cmap(i % cmap.N) for i, g in enumerate(gammas)}


# -----------------------------
# Helpers: read runs + var keys
# -----------------------------
def find_var_cols(kpi: dict) -> tuple[str, str]:
    """Find keys like var_95_inv_* and var_99_inv_* in summary.json dict."""
    v95 = None
    v99 = None
    for k in kpi.keys():
        if k.startswith("var_95_inv_"):
            v95 = k
        if k.startswith("var_99_inv_"):
            v99 = k
    if v95 is None or v99 is None:
        raise ValueError("Could not find var_95_inv_* and var_99_inv_* in summary.json")
    return v95, v99


def read_all_runs_for_scenario(scenario: str) -> list[dict]:
    """
    Returns list of runs:
      [{
        "gamma": float,
        "ts": DataFrame,
        "kpi": dict,
        "trades": DataFrame,
        "run_dir": Path
      }, ...]
    Folder structure: results/experiment/<scenario>/gamma_<g>/
    """
    scenario_dir = ROOT / scenario
    if not scenario_dir.exists():
        return []

    run_dirs = sorted([p for p in scenario_dir.iterdir() if p.is_dir() and p.name.startswith("gamma_")])
    runs: list[dict] = []
    for rd in run_dirs:
        ts_path = rd / "timeseries.csv"
        kpi_path = rd / "summary.json"
        trades_path = rd / "trades.csv"
        if not ts_path.exists() or not kpi_path.exists():
            continue

        try:
            gamma = float(rd.name.replace("gamma_", ""))
        except ValueError:
            continue

        ts = pd.read_csv(ts_path)
        trades = pd.read_csv(trades_path) if trades_path.exists() else pd.DataFrame()
        kpi = json.loads(kpi_path.read_text(encoding="utf-8"))
        runs.append({"gamma": gamma, "ts": ts, "trades": trades, "kpi": kpi, "run_dir": rd})

    runs.sort(key=lambda x: x["gamma"])
    return runs


# -----------------------------
# Helpers: scenario params (μ, σ) from config_used.yaml
# -----------------------------
def read_mu_sigma_from_config_used(run_dir: Path) -> tuple[float | None, float | None]:
    """
    Reads mu and sigma from config_used.yaml inside a run folder.
    Minimal parser: looks for lines like 'mu: 0.0' and 'sigma: 2.0'.
    """
    p = run_dir / "config_used.yaml"
    if not p.exists():
        return None, None

    mu = None
    sigma = None
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("mu:"):
            try:
                mu = float(s.split("mu:", 1)[1].strip())
            except ValueError:
                pass
        if s.startswith("sigma:"):
            try:
                sigma = float(s.split("sigma:", 1)[1].strip())
            except ValueError:
                pass
    return mu, sigma

def read_adverse_horizon_steps(run_dir: Path) -> int | None:
    """
    Reads adverse_horizon_steps from config_used.yaml inside a run folder.
    Minimal parser: looks for line like 'adverse_horizon_steps: 10'.
    """
    p = run_dir / "config_used.yaml"
    if not p.exists():
        return None

    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("adverse_horizon_steps:"):
            try:
                return int(s.split("adverse_horizon_steps:", 1)[1].strip())
            except ValueError:
                return None
    return None

def scenario_title_with_params(scenario: str) -> str:
    """
    Build subplot title like:
      'Ruhiger Markt (μ=0.0, σ=1.0)'
    Uses config_used.yaml from the first gamma-run it finds.
    """
    runs = read_all_runs_for_scenario(scenario)
    base = SCENARIO_TITLES.get(scenario, scenario)
    if not runs:
        return base

    mu, sigma = read_mu_sigma_from_config_used(runs[0]["run_dir"])
    if mu is None or sigma is None:
        return base

    return f"{base} (μ={mu:g}, σ={sigma:g})"


# -----------------------------
# Helpers: layout + legends + y-limits
# -----------------------------
def scenario_axes_grid(fig_title: str):
    """Create a 2x2 grid and map scenario->axis."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(fig_title, fontsize=14)
    ax_map = dict(zip(SCENARIOS, axes.flatten()))
    return fig, axes, ax_map


def add_shared_gamma_legend(fig, gamma_values: list[float], gamma_colors: dict[float, tuple]):
    """Shared legend: one entry per gamma (colored)."""
    handles = []
    labels = []
    for g in gamma_values:
        handles.append(mpl.lines.Line2D([0], [0], color=gamma_colors[g], linewidth=3))
        labels.append(f"γ={g:g}")

    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=min(6, len(labels)),
        bbox_to_anchor=(0.5, 0.01),
        fontsize=9,
    )


def compute_global_ylim_for_timeseries(col: str) -> tuple[float | None, float | None]:
    """Compute global min/max for a timeseries column across all scenarios and gammas."""
    y_min, y_max = None, None
    for scenario in SCENARIOS:
        runs = read_all_runs_for_scenario(scenario)
        for run in runs:
            ts = run["ts"]
            if col not in ts.columns:
                continue
            mn = float(ts[col].min())
            mx = float(ts[col].max())
            y_min = mn if y_min is None else min(y_min, mn)
            y_max = mx if y_max is None else max(y_max, mx)

    if y_min is None or y_max is None:
        return None, None

    pad = 0.05 * (y_max - y_min if y_max > y_min else 1.0)
    return y_min - pad, y_max + pad


def compute_global_ylim_for_quoting() -> tuple[float | None, float | None]:
    """
    Compute global min/max across r/bid/ask (NOT mid) to align quoting panels.
    Mid is shown separately in its own figure.
    """
    y_min, y_max = None, None
    cols = ["r", "bid", "ask"]

    for scenario in SCENARIOS:
        runs = read_all_runs_for_scenario(scenario)
        for run in runs:
            ts = run["ts"]
            present = [c for c in cols if c in ts.columns]
            if not present:
                continue
            mn = float(ts[present].min().min())
            mx = float(ts[present].max().max())
            y_min = mn if y_min is None else min(y_min, mn)
            y_max = mx if y_max is None else max(y_max, mx)

    if y_min is None or y_max is None:
        return None, None

    pad = 0.03 * (y_max - y_min if y_max > y_min else 1.0)
    return y_min - pad, y_max + pad


def compute_global_ylim_for_mid_only() -> tuple[float | None, float | None]:
    """Global min/max for mid across scenarios (one gamma run per scenario is enough)."""
    y_min, y_max = None, None
    for scenario in SCENARIOS:
        runs = read_all_runs_for_scenario(scenario)
        if not runs:
            continue
        ts = runs[0]["ts"]  # mid should be same across gammas (seed fixed)
        if "mid" not in ts.columns:
            continue
        mn = float(ts["mid"].min())
        mx = float(ts["mid"].max())
        y_min = mn if y_min is None else min(y_min, mn)
        y_max = mx if y_max is None else max(y_max, mx)

    if y_min is None or y_max is None:
        return None, None

    pad = 0.05 * (y_max - y_min if y_max > y_min else 1.0)
    return y_min - pad, y_max + pad


def compute_global_ylim_for_var() -> float | None:
    """Compute global max VaR across scenarios/gammas to align VaR bar panels."""
    sample_kpi = None
    for sc in SCENARIOS:
        runs = read_all_runs_for_scenario(sc)
        if runs:
            sample_kpi = runs[0]["kpi"]
            break
    if sample_kpi is None:
        return None

    v95_key, v99_key = find_var_cols(sample_kpi)

    vmax = None
    for sc in SCENARIOS:
        runs = read_all_runs_for_scenario(sc)
        for run in runs:
            kpi = run["kpi"]
            v95 = float(kpi.get(v95_key, float("nan")))
            v99 = float(kpi.get(v99_key, float("nan")))
            for v in (v95, v99):
                if pd.notna(v):
                    vmax = v if vmax is None else max(vmax, v)

    if vmax is None:
        return None

    return vmax * 1.15

# -----------------------------
# Helpers: markout per trade
# -----------------------------
def compute_markouts(
    trades: pd.DataFrame,
    timeseries: pd.DataFrame,
    horizon_steps: int,
) -> list[float]:
    """
    Markout per trade:
      buy:  mid_{t+h} - price_fill
      sell: price_fill - mid_{t+h}
    Negative => adverse selection.
    """
    if trades.empty:
        return []
    if "t" not in trades.columns or "price" not in trades.columns or "side" not in trades.columns:
        return []
    if "t" not in timeseries.columns or "mid" not in timeseries.columns:
        return []

    mids = timeseries.set_index("t")["mid"]
    future_mid = mids.shift(-horizon_steps)
    markouts: list[float] = []

    for _, row in trades.iterrows():
        t = int(row["t"])
        fm = future_mid.get(t)
        if pd.isna(fm):
            continue
        price = float(row["price"])
        side = str(row["side"])
        if side == "buy":
            markouts.append(float(fm - price))
        elif side == "sell":
            markouts.append(float(price - fm))

    return markouts

# -----------------------------
# NEW Figure 0: Market price overview (mid only, all scenarios in one chart)
# -----------------------------
def plot_market_price_overview() -> None:
    fig = plt.figure(figsize=(14, 6))
    ax = fig.add_subplot(1, 1, 1)
    fig.suptitle("0) Marktpreis (Mid) — Überblick über alle Marktsituationen", fontsize=14)

    y_min, y_max = compute_global_ylim_for_mid_only()

    # Each scenario: plot mid from first run
    for scenario in SCENARIOS:
        runs = read_all_runs_for_scenario(scenario)
        if not runs:
            continue
        ts = runs[0]["ts"]
        if "mid" not in ts.columns:
            continue

        label = scenario_title_with_params(scenario)
        ax.plot(ts["t"], ts["mid"], linewidth=1.6, label=label)

    ax.set_title("Mid (Marktpreis) je Marktsituation")
    ax.set_xlabel("Zeit (Schritte)")
    ax.set_ylabel("Preis")
    ax.grid(True, alpha=0.2)

    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9)
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    fig.savefig(OUTDIR / "00_mid_overview.png", dpi=180)
    plt.close(fig)

def plot_markout_distributions(gamma_values: list[float], gamma_colors: dict[float, tuple]) -> None:
    fig, axes, ax_map = scenario_axes_grid(
        "5) Markout pro Trade (positiv = vorteilhaft, negativ = adverse)"
    )

    for scenario in SCENARIOS:
        ax = ax_map[scenario]
        runs = read_all_runs_for_scenario(scenario)
        if not runs:
            ax.set_axis_off()
            continue

        horizon_steps = read_adverse_horizon_steps(runs[0]["run_dir"])
        horizon_suffix = f"h={horizon_steps} Schritte" if horizon_steps else "h=unbekannt"

        gammas = [r["gamma"] for r in runs]
        markout_series = [
            compute_markouts(r["trades"], r["ts"], horizon_steps or 1) for r in runs
        ]

        positions = list(range(len(gammas)))
        box = ax.boxplot(markout_series, positions=positions, patch_artist=True)
        for patch, g in zip(box["boxes"], gammas):
            patch.set_facecolor(gamma_colors[g])
            patch.set_alpha(0.5)
        for median in box["medians"]:
            median.set_color("black")

        ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
        ax.set_title(f"{scenario_title_with_params(scenario)} ({horizon_suffix})")
        ax.set_xlabel("Risikoaversion γ")
        ax.set_ylabel("Markout")
        ax.set_xticks(positions)
        ax.set_xticklabels([f"{g:g}" for g in gammas], rotation=0)
        ax.grid(True, axis="y", alpha=0.2)

    add_shared_gamma_legend(fig, gamma_values, gamma_colors)
    plt.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(OUTDIR / "05_markout_boxplot_2x2.png", dpi=180)
    plt.close(fig)

# -----------------------------
# Figure 1: Quoting (r + band only; mid removed)
# -----------------------------
def plot_quoting(gamma_values: list[float], gamma_colors: dict[float, tuple]) -> None:
    fig, axes, ax_map = scenario_axes_grid(
        "1) Wie wird gequoted? (Reservation Price r, Bid/Ask-Band)"
    )

    y_min, y_max = compute_global_ylim_for_quoting()

    for scenario in SCENARIOS:
        ax = ax_map[scenario]
        runs = read_all_runs_for_scenario(scenario)
        if not runs:
            ax.set_axis_off()
            continue

        for run in runs:
            g = run["gamma"]
            ts = run["ts"]
            if "r" in ts.columns:
                ax.plot(ts["t"], ts["r"], linewidth=1.1, color=gamma_colors[g])
            if {"bid", "ask"}.issubset(ts.columns):
                ax.fill_between(ts["t"], ts["bid"], ts["ask"], alpha=0.10, color=gamma_colors[g])

        ax.set_title(scenario_title_with_params(scenario))
        ax.set_xlabel("Zeit (Schritte)")
        ax.set_ylabel("Preis")
        ax.grid(True, alpha=0.2)

        if y_min is not None and y_max is not None:
            ax.set_ylim(y_min, y_max)

    add_shared_gamma_legend(fig, gamma_values, gamma_colors)
    plt.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(OUTDIR / "01_quoting_2x2.png", dpi=180)
    plt.close(fig)


# -----------------------------
# Figures 2 & 3: PnL / Inventory timeseries
# -----------------------------
def plot_timeseries_metric(
    fig_title: str,
    col: str,
    y_label: str,
    outname: str,
    gamma_values: list[float],
    gamma_colors: dict[float, tuple],
) -> None:
    fig, axes, ax_map = scenario_axes_grid(fig_title)
    y_min, y_max = compute_global_ylim_for_timeseries(col)

    for scenario in SCENARIOS:
        ax = ax_map[scenario]
        runs = read_all_runs_for_scenario(scenario)
        if not runs:
            ax.set_axis_off()
            continue

        for run in runs:
            g = run["gamma"]
            ts = run["ts"]
            if col not in ts.columns:
                continue
            ax.plot(ts["t"], ts[col], linewidth=1.1, color=gamma_colors[g])

        ax.set_title(scenario_title_with_params(scenario))
        ax.set_xlabel("Zeit (Schritte)")
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.2)

        if y_min is not None and y_max is not None:
            ax.set_ylim(y_min, y_max)

    add_shared_gamma_legend(fig, gamma_values, gamma_colors)
    plt.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(OUTDIR / outname, dpi=180)
    plt.close(fig)


# -----------------------------
# Figure 4: VaR bars (95/99 on x, bars=gamma colors)
# -----------------------------
def plot_var_bars(gamma_values: list[float], gamma_colors: dict[float, tuple]) -> None:
    fig, axes, ax_map = scenario_axes_grid(
        "4) Tail Risk (VaR) als Balken (VaR 95% / VaR 99%, Farben = γ)"
    )

    sample_kpi = None
    for sc in SCENARIOS:
        runs = read_all_runs_for_scenario(sc)
        if runs:
            sample_kpi = runs[0]["kpi"]
            break
    if sample_kpi is None:
        raise RuntimeError("No runs found. Did you run the experiments and write summary.json?")

    v95_key, v99_key = find_var_cols(sample_kpi)
    y_max = compute_global_ylim_for_var()

    for scenario in SCENARIOS:
        ax = ax_map[scenario]
        runs = read_all_runs_for_scenario(scenario)
        if not runs:
            ax.set_axis_off()
            continue

        gammas = [r["gamma"] for r in runs]
        var95 = [float(r["kpi"].get(v95_key, float("nan"))) for r in runs]
        var99 = [float(r["kpi"].get(v99_key, float("nan"))) for r in runs]

        n = len(gammas)
        group_x = [0, 1]
        total_w = 0.80
        bar_w = total_w / max(n, 1)
        start = -total_w / 2

        for i, g in enumerate(gammas):
            x95 = group_x[0] + start + i * bar_w + bar_w / 2
            x99 = group_x[1] + start + i * bar_w + bar_w / 2
            ax.bar(x95, var95[i], width=bar_w, color=gamma_colors[g])
            ax.bar(x99, var99[i], width=bar_w, color=gamma_colors[g])

        ax.set_title(scenario_title_with_params(scenario))
        ax.set_xticks(group_x)
        ax.set_xticklabels(["VaR 95%", "VaR 99%"])
        ax.set_ylabel("VaR (pro VaR-Horizont)")
        ax.grid(True, axis="y", alpha=0.2)

        if y_max is not None:
            ax.set_ylim(0, y_max)

    add_shared_gamma_legend(fig, gamma_values, gamma_colors)
    plt.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(OUTDIR / "04_var_bars_2x2.png", dpi=180)
    plt.close(fig)


def main():
    gamma_values = collect_all_gammas()
    if not gamma_values:
        raise RuntimeError("No gamma folders found under results/experiment/<scenario>/gamma_<...>.")

    gamma_colors = build_gamma_color_map(gamma_values)

    # NEW: Mid overview figure
    plot_market_price_overview()

    # 1) Quoting (without mid)
    plot_quoting(gamma_values, gamma_colors)

    # 2) PnL
    plot_timeseries_metric(
        fig_title="2) Gewinn (PnL) über Zeit — Vergleich aller γ je Marktsituation",
        col="pnl",
        y_label="Mark-to-Market PnL",
        outname="02_pnl_2x2.png",
        gamma_values=gamma_values,
        gamma_colors=gamma_colors,
    )

    # 3) Inventory
    plot_timeseries_metric(
        fig_title="3) Bestand (Inventory) über Zeit — Vergleich aller γ je Marktsituation",
        col="inventory",
        y_label="Inventory (Bestand q)",
        outname="03_inventory_2x2.png",
        gamma_values=gamma_values,
        gamma_colors=gamma_colors,
    )

    # 4) VaR bars
    plot_var_bars(gamma_values, gamma_colors)

    # 5) Markout distributions
    plot_markout_distributions(gamma_values, gamma_colors)

    print("Wrote figures to:", OUTDIR)


if __name__ == "__main__":
    main()
