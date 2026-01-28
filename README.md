# Market Making Sandbox (Synthetic, Reproducible)

## TL;DR (in 30 Sekunden)
Ich habe dieses Repository gebaut, um die Kernkonzepte von **Market Making** verständlich und reproduzierbar zu demonstrieren:
- Ich stelle gleichzeitig einen **Kaufpreis (Bid)** und **Verkaufspreis (Ask)**.
- Ich verdiene (potenziell) am **Spread** – trage aber Risiko durch **Inventory** und **Adverse Selection**.
- Ich simuliere Mid-Prices synthetisch (kontrolliert & auditierbar) und messe die Strategie mit **KPIs**.

Dieses Projekt ist bewusst **einfach**, um die Mechanik klar zu erklären, aber **strukturiert**, um wissenschaftlich prüfbar zu sein (Config + deterministische Seeds + Outputs + Tests).

---

## Was ist Market Making? 
Stell dir vor, ein Kiosk kauft und verkauft Süßigkeiten:
- Er sagt: „Ich kaufe für 0,95€“ (Bid) und „ich verkaufe für 1,00€“ (Ask).
- Die Differenz (0,05€) ist der **Spread** – daraus kann Gewinn entstehen.
- Risiko: Vielleicht kaufen viele Leute gleichzeitig, dann sitzt der Kiosk auf viel Ware (**Inventory**).
- Oder: Kunden kaufen genau dann, wenn der Großhandelspreis gleich fällt (**Adverse Selection**).

In Märkten ist das ähnlich: Market Maker stellen ständig Bid/Ask, damit andere schnell handeln können.

---

## Warum synthetische Daten?
Für ein erstes, auditierbares Projekt sind synthetische Daten ideal:
- **Reproduzierbar**: Gleicher Seed ⇒ gleiche Preisreihe ⇒ gleiche Trades/KPIs.
- **Kontrollierbar**: Ich kann Regime (ruhig/volatil/trend) gezielt erzeugen.
- **Fokus auf Konzepte** statt Daten-Edge-Cases (fehlende Timestamps, API-Ausfälle, Orderbook-Rekonstruktion).

Später kann man die Mid-Price-Zeitreihe durch echte Daten ersetzen (siehe “Extensions”).

---

## Wissenschaftliche Basis
Dieses Repo folgt der Grundidee der Market-Making-Literatur: Quotes werden so gewählt, dass ein Trade-off entsteht zwischen:
- **Liquidität bereitstellen** (eng quoten ⇒ mehr Fills)
- **Risiko kontrollieren** (volatil ⇒ Spread breiter; Inventory steuern)
- **Adverse Selection reduzieren** (nach Fill bewegt sich der Preis oft „gegen“ den Maker)

Als Referenz verwende ich u.a.:
- Avellaneda & Stoikov (Optimal Market Making / LOB), DOI: 10.1080/14697680701381228  
- Madhavan (Market Microstructure Survey), DOI: 10.1016/S1386-4181(00)00007-0  
- SEC/Investor.gov Erklärungen zu Spread & Maker-Taker (siehe References)

---

## Projekt-Architektur (übersichtlich)

---

## Wie funktioniert die Simulation? (leicht verständlich)
1) **Ich simuliere** eine Mid-Price-Zeitreihe (synthetisch).
2) In jedem Zeitschritt berechne ich eine Quote:
   - Basis-Spread (Entlohnung fürs Bereitstellen von Liquidität)
   - Volatilitäts-Aufschlag (in unsicheren Märkten: breiter quoten)
   - Inventory-Skew (wenn ich zu “long” bin, will ich eher verkaufen)
3) **Fills passieren stochastisch**: Je näher mein Quote am Mid ist, desto wahrscheinlicher ein Fill.
4) Ich tracke **Inventory** und **Cash**, daraus ergibt sich **Mark-to-Market PnL** am Ende.

---

## KPIs (was ich messen will und warum)
Die KPIs sind so gewählt, dass man die typischen Market-Making Trade-offs erkennt:

- **final_pnl (Mark-to-Market)**: Gesamtleistung inkl. Inventory-Bewertung am letzten Mid.
- **n_trades**: Aktivität / Fill-Intensität (eng quoten ⇒ oft mehr Trades).
- **final_inventory**: Risiko-Exposure (zu viel Inventory ist riskant).
- **adverse_selection_rate (Proxy)**:
  - Nach einem **BUY-Fill**: Wenn der Mid nach X Schritten darunter liegt, war der Fill tendenziell „schlecht“ (picked off).
  - Nach einem **SELL-Fill**: Wenn der Mid nach X Schritten darüber liegt, analog.
  - Das ist bewusst ein **einfacher Proxy**, aber transparent & auditierbar.

---

## Reproduzierbarkeit & Audit Trail (wichtig!)
Jeder Run schreibt einen vollständigen Audit-Ordner:
- `config_used.yaml`  – exakt verwendete Parameter
- `timeseries.csv`    – Mid-Price Zeitreihe
- `trades.csv`        – alle Trades (Zeit, Seite, Preis, Größe)
- `summary.json`      – KPIs

Damit kann jeder Dritte den Run nachvollziehen und die Ergebnisse überprüfen.

---

## Quickstart
### 1) Installation
```bash
pip install -r requirements.txt
pip install -e .

---
## Single Run
python scripts/run_backtest.py --config config/base.yaml --outdir results/run_001

---
## Run mit Szenarien 
python scripts/run_scenarios.py --config_dir config --outdir results/scenarios

Ich nutze mehrere Configs, um verständliche Aussagen zu machen:
- Low Vol + tight spread: mehr Fills, aber ggf. mehr adverse selection
- High Vol + wider spread: weniger Fills, aber (oft) stabileres Profil
- Trend-Regime: zeigt, warum Inventory-Skew wichtig sein kann
- Ziel ist nicht „max PnL“ in dieser Toy-Welt, sondern Mechanik + Trade-offs sichtbar zu machen.

---

### Tests (wissenschaftlich sauber)

Ich prüfe mindestens:
- Determinismus: gleicher Seed ⇒ gleiche Ergebnisse
- Invarianten: z.B. bid < ask

### Um die Test durchzuführen
pytest -q 

---
Limitierungen (ehrlich und wichtig)

Dieses Repo ist eine didaktische Simulation, kein Produktions-HFT-System:
- Kein echtes Orderbook, keine echte Latenz-/Execution-Engine
- Synthetischer Mid (GBM) ist ein Baseline-Modell (konstante Volatilität, keine Jumps)
- Fill-Modell ist vereinfacht (Poisson/Intensität als Funktion der Quote-Distanz)
- Diese Vereinfachungen sind bewusst gewählt, um Konzepte klar und reproduzierbar zu demonstrieren.

---
Extensions
- Mid-Price durch echte Daten ersetzen (CSV Loader)
- echtes L2 Orderbook + Snapshot/Diff-Rekonstruktion
- bessere Vol-Schätzung, Regime-Switching, Jumps
- Risiko: Inventory Value-at-Risk, Limits, Hedging

---
References
Market Making & Microstructure
    - Avellaneda, M.; Stoikov, S. (2008): High-frequency trading in a limit order book. Quantitative Finance. DOI: 10.1080/14697680701381228
    - Madhavan, A. (2000): Market microstructure: A survey. Journal of Financial Markets. DOI: 10.1016/S1386-4181(00)00007-0

Spread / Maker-Taker (Overviews)
    - U.S. SEC: Spread (Definition Bid/Ask/Spread; market makers earn the spread).
    - U.S. SEC (Division of Trading and Markets memo, 2015): Maker-Taker Fees on Equities Exchanges.

Synthetic price process (GBM background)
    - Standard lecture notes on Geometric Brownian Motion (GBM) / Black-Scholes assumptions.