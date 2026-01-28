from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


def plot_panels(folder: Path) -> None:
    ts = pd.read_csv(folder / "timeseries.csv")
    trades = pd.read_csv(folder / "trades.csv")

    # trades per timestep (include zeros)
    if trades.empty:
        counts = pd.Series(0, index=ts["t"])
    else:
        counts = trades.groupby("t").size().reindex(ts["t"], fill_value=0)

    rolling = counts.rolling(60, min_periods=1).mean()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(folder.name)

    # 1) Mid + quoted spread band
    axes[0, 0].plot(ts["t"], ts["mid"])
    axes[0, 0].fill_between(ts["t"], ts["bid"], ts["ask"], alpha=0.2)

    # y-axis formatting: no scientific notation, no offset, 2 decimals
    axes[0, 0].ticklabel_format(style="plain", axis="y", useOffset=False)
    axes[0, 0].yaxis.get_offset_text().set_visible(False)
    axes[0, 0].yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))

    axes[0, 0].set_title("Mid price + quoted spread (bid/ask band)")
    axes[0, 0].set_xlabel("t")
    axes[0, 0].set_ylabel("mid")

    # 2) Trade intensity
    axes[0, 1].plot(ts["t"], rolling.values)
    axes[0, 1].set_title("Trade intensity (rolling mean, 60 steps)")
    axes[0, 1].set_xlabel("t")
    axes[0, 1].set_ylabel("trades / step")

    # 3) Inventory
    if "inventory" in ts.columns:
        axes[1, 0].plot(ts["t"], ts["inventory"])
        axes[1, 0].set_title("Inventory over time")
        axes[1, 0].set_xlabel("t")
        axes[1, 0].set_ylabel("inventory")
    else:
        axes[1, 0].text(0.5, 0.5, "inventory not logged", ha="center", va="center")
        axes[1, 0].set_axis_off()

    # 4) PnL
    if "pnl" in ts.columns:
        axes[1, 1].plot(ts["t"], ts["pnl"])
        axes[1, 1].set_title("Mark-to-market PnL over time")
        axes[1, 1].set_xlabel("t")
        axes[1, 1].set_ylabel("PnL")
    else:
        axes[1, 1].text(0.5, 0.5, "pnl not logged", ha="center", va="center")
        axes[1, 1].set_axis_off()

    plt.tight_layout()
    fig.savefig(folder / "panel_2x2.png", dpi=160)
    plt.close(fig)


def main():
    root = Path("results/scenarios")
    for folder in root.iterdir():
        if folder.is_dir() and (folder / "timeseries.csv").exists():
            plot_panels(folder)


if __name__ == "__main__":
    main()
