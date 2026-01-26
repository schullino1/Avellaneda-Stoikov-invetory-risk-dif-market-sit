from __future__ import annotations
from pathlib import Path
import yaml
import json

from .config import MMConfig


def load_config(path: str | Path) -> MMConfig:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return MMConfig(**data)


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_outputs(outdir: str | Path, cfg: MMConfig, timeseries_df, trades_df, summary: dict) -> Path:
    out = ensure_dir(outdir)
    (out / "config_used.yaml").write_text(yaml.safe_dump(cfg.model_dump()), encoding="utf-8")
    timeseries_df.to_csv(out / "timeseries.csv", index=False)
    trades_df.to_csv(out / "trades.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out
