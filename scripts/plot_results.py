from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def plot_scenario(folder: Path) -> None:
    ts = pd.read_csv(folder / "timeseries.csv")
    trades = pd.read_csv(folder / "trades.csv")

    # Mid price
    plt.figure()
    plt.plot(ts["t"], ts["mid"])
    plt.xlabel("t")
    plt.ylabel("mid")
    plt.title(f"{folder.name} - Mid Price")
    plt.savefig(folder / "mid.png", dpi=150)
    plt.close()

    # Trade count over time (simple)
    plt.figure()
    if not trades.empty:
        counts = trades.groupby("t").size()
        plt.plot(counts.index, counts.values)
    plt.xlabel("t")
    plt.ylabel("trades")
    plt.title(f"{folder.name} - Trades per timestep")
    plt.savefig(folder / "trades.png", dpi=150)
    plt.close()


def main():
    root = Path("results/scenarios")
    for folder in root.iterdir():
        if folder.is_dir() and (folder / "timeseries.csv").exists():
            plot_scenario(folder)


if __name__ == "__main__":
    main()
