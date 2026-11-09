# Bond Analytics

A fixed income pricing and risk tool built from first principles. Prices fixed coupon bonds between coupon dates, computes duration, DV01 and convexity, and decomposes price changes under yield shocks. Implemented from scratch in Python (no external dependencies) and in a React dashboard.

**Live demo → [bond-pricer.vercel.app](https://bond-pricer.vercel.app)**

---

## What it does

| Tab | What it shows |
|---|---|
| **Pricing** | Dirty and clean price between coupon dates, accrued interest, cash flow schedule with PV weights; solves YTM from a quoted (clean) price |
| **Risk & Duration** | Macaulay, modified and dollar duration · DV01 per bond and per position |
| **Convexity** | Price/yield curve · Taylor decomposition · duration-only vs. duration + convexity vs. exact repricing |

---

## Math implemented

**Pricing**
```
P(coupon date) = Σ CFₜ / (1 + y/f)ᵗ            t = 1..N coupon periods
Dirty price    = Σ CFₜ / (1 + y/f)^(t − a)     a = days since last coupon / days in period
Accrued        = (C/f) × a
Clean price    = Dirty price − Accrued
```
The clean price does not jump on a coupon date: just before a coupon it equals the price just after.

**Duration & DV01**
```
D_mac = Σ [ (t/f) × PV(CFₜ) ] / P
D_mod = D_mac / (1 + y/f)
DV01  = D_mod × P × 0.0001
Position DV01 = DV01 × (Notional / Face)
```

**Convexity & Taylor expansion**
```
Convexity = (1/P) × (1/(1+y/f)²) × Σ [ t(t+1) × CFₜ / (1+y/f)ᵗ ] / f²
ΔP ≈ −D_mod × P × Δy  +  ½ × Convexity × P × (Δy)²
```
Analytical DV01 and convexity are cross-checked against finite differences in the library (`dv01_exact`, `convexity_exact`). Duration and convexity are measured from the last coupon date.

---

## Project structure

```
bond_pricer/
├── src/
│   ├── bond.py             ← pricing, dirty/clean price, YTM solvers
│   ├── risk.py             ← duration, DV01, position DV01
│   ├── convexity.py        ← convexity, Taylor expansion, scenarios
│   ├── App.jsx             ← React dashboard (Vite + recharts)
│   └── main.jsx
├── examples/
│   ├── pricing.py          ← pricing, closed form, YTM, accrued interest
│   ├── duration_dv01.py    ← duration, DV01, position DV01
│   └── convexity_taylor.py ← convexity, Taylor decomposition, scenarios
├── index.html
├── vite.config.js
├── vercel.json
└── package.json
```

---

## Running locally

**Python library** (standard library only), from the repository root:
```bash
python examples/pricing.py
python examples/duration_dv01.py
python examples/convexity_taylor.py
```

**Dashboard**
```bash
npm install
npm run dev     # http://localhost:5173
```

---

## Python usage

```python
from src.bond import Bond
from src.risk import risk_summary
from src.convexity import convexity, scenario_analysis

# 5% annual coupon, 5 years, YTM = 6%  (periods = number of coupon periods)
bond = Bond(face=1000, coupon_rate=0.05, periods=5, freq=1)

print(bond.price(ytm=0.06))          # 957.8764
print(bond.ytm(price=957.8764))      # 0.06 (round-trip)

summary = risk_summary(bond, ytm=0.06, notional=10_000_000)
# price 957.88 | mac_dur 4.53 | mod_dur 4.28 | dv01 0.41 | position_dv01 4097.77

print(convexity(bond, ytm=0.06))     # 23.41

for s in scenario_analysis(bond, ytm=0.06, shocks_bps=[-100, 100]):
    print(f"{s['bp']:+4d}bp | dur {s['dur_term']:+.2f} | conv {s['conv_term']:+.2f} | exact {s['exact_change']:+.2f}")
# -100bp | dur +40.98 | conv +1.12 | exact +42.12
# +100bp | dur -40.98 | conv +1.12 | exact -39.88

# Between coupon dates: 5% semi-annual, 5 years (10 periods), 30 of 180 days accrued
semi = Bond(face=1000, coupon_rate=0.05, periods=10, freq=2)
print(semi.dirty_price(0.06, 30, 180))           # 962.0770
print(semi.clean_price(0.06, 30, 180))           # 957.9103
print(semi.ytm_from_clean(957.9103, 30, 180))    # 0.06
```

---

## Example results

5% annual coupon · face $1,000 · 5 years · YTM = 6%

| Metric | Value |
|---|---|
| Price | $957.8764 |
| Macaulay duration | 4.5347 yr |
| Modified duration | 4.2780 |
| DV01 (per $1,000 face) | $0.4098 |
| Position DV01 ($10M) | $4,097.77 |
| Convexity | 23.4103 |
| Convexity adjustment (±100bp) | $1.12 |
| Gain at −100bp | +$42.12 |
| Loss at +100bp | −$39.88 |
| Asymmetry (convexity value) | $2.24 |

---

## Related projects

- **[Yield Curve Suite](https://github.com/aharode/yield_curve)** — Treasury bootstrapping, Nelson-Siegel, PCA, Vasicek
