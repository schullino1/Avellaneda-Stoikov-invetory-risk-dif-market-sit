from __future__ import annotations
import numpy as np


def simulate_gbm(
    *,
    s0: float,
    mu: float,
    sigma: float,
    dt_seconds: float,
    n_steps: int,
    seconds_per_year: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Geometric Brownian Motion (GBM) for a synthetic mid price series.
    --> Is used in Finace as:
    - simple, standard baseline price model
    - fully reproducible given a random seed
    
    """
    dt = dt_seconds / float(seconds_per_year)

    # standard normal increments
    z = rng.standard_normal(n_steps)

    # log price increments for GBM:
    # log(S_t) evolves with drift (mu - 0.5*sigma^2) and diffusion sigma*sqrt(dt)*z
    increments = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z

    log_s = np.log(s0) + np.cumsum(increments)
    return np.exp(log_s)
