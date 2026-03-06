# Bond Pricing & Risk Analytics Tool

Built incrementally across the 25-Day Fixed Income Career Accelerator.

## Project Structure

```
bond_pricer/
├── src/
│   ├── __init__.py
│   ├── bond.py          ← Day 1: core pricing, clean/dirty price, YTM solver
│   ├── risk.py          ← Day 2: duration, DV01               (coming Day 2)
│   ├── convexity.py     ← Day 3: convexity, Taylor approx     (coming Day 3)
│   └── curves.py        ← Day 4–5: yield curves, bootstrapper (coming Day 4)
├── day1_problems.py     ← Day 1 practice problem verification
├── README.md
└── requirements.txt
```

## Progress

| Day | Module        | Status      |
|-----|---------------|-------------|
| 1   | Bond pricing  | ✅ Complete |
| 2   | Duration/DV01 | 🔒 Locked   |
| 3   | Convexity     | 🔒 Locked   |
| 4–5 | Yield curves  | 🔒 Locked   |

## Running

```bash
# From the bond_pricer/ directory
python day1_problems.py
```
