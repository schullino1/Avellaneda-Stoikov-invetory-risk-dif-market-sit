# Market Making Sandbox (Synthetic, Reproducible)
## 1. Background & Research Question
Market making provides liquidity by continuously quoting bid and ask prices. The core trade-off is between earning the spread and managing inventory risk and adverse selection. This repository implements a simplified, fully reproducible sandbox to study how risk aversion (γ) and market regimes influence that trade-off in a controlled setting, based on the Avellaneda–Stoikov framework.

**Research question:** How does changing the market maker’s risk aversion (γ) affect quoting behavior, inventory risk, and adverse selection across different synthetic market regimes?

## 2. Basics & Project Structure (incl. Limitations)

### 2.1 Conceptual model (high level)
The simulation follows a stylized Avellaneda–Stoikov setup:
- A synthetic mid-price process (random walk with drift/volatility) is simulated per scenario.
- Quotes are computed each step based on risk aversion, volatility, and remaining horizon.
- Fills occur stochastically as a function of quote distance to mid (arrival-rate model).
- PnL is marked-to-market; inventory and risk metrics are recorded.

### 2.2 Scenario design and parameters
We simulate four market regimes using different drift/volatility pairs:
- Calm: μ=0, σ=2
- Turbulent: μ=0, σ=10
- Uptrend: μ=+10, σ=2
- Downtrend: μ=−10, σ=2
Risk aversion is swept over γ ∈ {0.001, 0.01, 0.05, 0.1, 0.3}. All other parameters are held constant to isolate the impact of γ on strategy behavior.

### 2.3 Repository structure (key files)
- `src/mm_sandbox/` — core simulation, strategy, and metrics logic.
- `config/` — scenario configurations (market regimes & risk settings).
- `scripts/run_scenarios.py` — batch runs for scenario comparison.
- `scripts/plot_4fig_story.py` — figure generation for the narrative plots.
- `results/` — output artifacts (config, timeseries, trades, summary).

### 2.4 Limitations (explicit and intentional)
This is a didactic sandbox, not a production trading system:
- **No real order book**: no queue priority, latency, or microstructure frictions.
- **Synthetic price process**: simplified dynamics (no jumps, no regime switches unless configured).
- **Simplified fill model**: Poisson/arrival-rate approximation tied to quote distance.
- **Risk metrics are illustrative**: VaR and adverse selection proxies are simplified.

These choices are deliberate to keep experiments transparent and reproducible while highlighting the main mechanisms.

## 3. Results, Conclusions & Outlook
### 3.1 Results (from the provided figures)
**Quoting behavior (Figure 1):** Spreads widen as γ increases across all regimes. In turbulent markets, the higher-volatility environment leads to visibly wider quote bands for the same γ, while calm and trending regimes show tighter bands overall. This indicates that both σ and γ contribute to more conservative quoting.

**PnL over time (Figure 2):** Lower γ generally yields higher average PnL in calm and uptrend regimes, consistent with tighter quoting and higher trade frequency. In turbulent regimes, low γ produces higher variability (more volatile PnL paths). In the downtrend scenario, moderate γ values show more stable growth, while very low γ can underperform due to inventory exposure during adverse drift.

**Inventory dynamics (Figure 3):** Lower γ leads to wider inventory swings across regimes, especially in turbulent conditions, indicating higher exposure. Higher γ keeps inventory closer to zero and reduces amplitude in all scenarios, reflecting more aggressive inventory control.

**Tail risk (VaR, Figure 4):** VaR levels decrease as γ increases in every regime, with the sharpest improvements in the turbulent market. This demonstrates that higher risk aversion materially reduces downside tail exposure, albeit at the cost of reduced trading activity and lower average PnL.

**Per-trade markout (Figure 5):** Low γ strategies show wider markout distributions (both upside and downside), indicating larger adverse-selection tails. Higher γ compresses the distribution, reducing extreme negative outcomes but also limiting upside. Moderate γ values balance dispersion and median performance across regimes.

### 3.2 Conclusions (neutral)
- Lower γ produces tighter quotes, higher trading intensity, and larger inventory swings, which can improve mean PnL but increases tail risk and adverse selection exposure.
- Higher γ reduces inventory variance and downside tail risk, with more stable (but typically lower) PnL.
- The optimal γ is regime-dependent: calm and uptrend regimes tolerate lower γ, while turbulent and downtrend regimes benefit from higher γ to control risk.

### 3.3 Outlook (extensions)
- Replace synthetic mid-price paths with real data and compare regimes.
- Extend the fill model with order book depth and queue dynamics.
- Add regime switching, jumps, and volatility clustering to the price process.
- Introduce explicit risk limits and inventory-based hedging.

## 5. Setup & Execution
### 5.1 Installation
```bash
pip install -r requirements.txt
pip install -e .
```

### 5.2 Run a single backtest
```bash 
python scripts/run_backtest.py --config config/base.yaml --outdir results/run_001```

### 5.3 Run all scenarios
```bash
python scripts/run_scenarios.py --config_dir config --outdir results/scenarios```

### 5.4 Generate figures
```bash
python scripts/plot_4fig_story.py
```
### 5.5 Tests
```bash
pytest -q
```

## References
- Avellaneda, M.; Stoikov, S. (2008). *High-frequency trading in a limit order book*. Quantitative Finance. DOI: 10.1080/14697680701381228
- Madhavan, A. (2000). *Market microstructure: A survey*. Journal of Financial Markets. DOI: 10.1016/S1386-4181(00)00007-0
- SEC Investor.gov: Bid/Ask Spread and market making overviews.
- SEC (Division of Trading and Markets, 2015): Maker–taker fee discussion.