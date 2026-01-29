from __future__ import annotations
import math
import numpy as np


def simulate_rw_paper(
    *,
    s0: float,
    mu: float,
    sigma: float,
    dt: float,
    n_steps: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Midpreis Bildung abhänig von gewähltem Drift
    s_{t+dt} = s_t + mu*dt + sign * sigma*sqrt(dt)

    - mu*dt: Drift in Preis-Einheiten (z.B. Uptrend/Downtrend)
    - sign: +1 oder -1 mit 50/50 Wahrscheinlichkeit
    - sigma*sqrt(dt): typische Schrittgröße (Paper beschreibt ±σ√dt)

    Ergebnis: Mid-Preis-Zeitreihe als numpy array der Länge n_steps.
    """
    s = np.empty(n_steps, dtype=float)
    s[0] = s0

    step = sigma * math.sqrt(dt)
    for t in range(1, n_steps):
        sign = 1.0 if rng.random() < 0.5 else -1.0
        s[t] = s[t - 1] + mu * dt + sign * step

    return s
