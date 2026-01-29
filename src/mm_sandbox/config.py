from __future__ import annotations
from pydantic import BaseModel, Field


class MMConfig(BaseModel):
    # --- Reproduzierbarkeit ---
    seed: int = 42  # fixiert die Zufallszahlen -> identische Ergebnisse bei gleicher Config

    # --- Zeitdiskretisierung (Paper) ---
    dt_seconds: float = Field(gt=0)   # dt > 0: Zeitschritt in Sekunden (Paper nutzt sehr kleines dt)
    n_steps: int = Field(gt=1)        # Anzahl Zeitschritte
    T_seconds: float = Field(gt=0)    # Gesamthorizont T in Sekunden (Paper: T=1)

    tau_mode: str = "session"
    # "session": tau = max(T - t*dt, 0) fällt gegen 0
    # (rolling wäre eine Extension; im Paper wird session betrachtet)

    # --- Execution / Ordergröße ---
    trade_size: float = Field(gt=0)   # Stückzahl pro Fill (Paper: 1)

    # --- Markt/Preisprozess (Paper: additive Random Walk mit Drift) ---
    s0: float = Field(gt=0)           # Startpreis s(0)
    mu: float                         # Drift μ in Preis-Einheiten pro Sekunde (arithmetisch)
    sigma: float = Field(ge=0)        # σ in Preis-Einheiten; Step ~ ±σ*sqrt(dt) (Paper)

    # --- Avellaneda–Stoikov Risikoaversion ---
    gamma: float = Field(gt=0)        # γ > 0 (steht im AS-Reservation-Price + Spread-Term)

    # --- Orderflow-Modell (Paper: λ(δ)=A*exp(-k*δ)) ---
    A: float = Field(gt=0)            # Basisintensität (Orderflow-Level)
    k: float = Field(gt=0)            # Exponential-Decay (Liquidität/Depth im Paper)

    # --- Fees (im Paper-Basissetup häufig 0, aber als Parameter ok) ---
    fee_bps: float = Field(ge=0)      # Gebühren in bps

    # --- KPI / Risk ---
    adverse_horizon_steps: int = Field(ge=1)  # Markout-Horizont in Steps (z.B. 10)
    var_horizon_seconds: float = Field(gt=0)  # VaR-Horizont in Sekunden (z.B. 0.05 = 10 Steps bei dt=0.005)
    var_levels: list[float] = Field(default_factory=lambda: [0.95, 0.99])  # 95% und 99%
