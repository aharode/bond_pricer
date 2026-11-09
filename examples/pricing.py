"""
Pricing examples: PV of cash flows, closed form, YTM, accrued interest and clean/dirty price.
Run from the repository root: python examples/pricing.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bond import Bond


def separator(title):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print('─' * 50)


# ── Problem 1 ─────────────────────────────────────────────────────────────────
separator("Problem 1 — 5% annual, 5Y, YTM=6%")

bond = Bond(face=1000, coupon_rate=0.05, periods=5, freq=1)

print("\nCash flow breakdown:")
y = 0.06
total = 0
for t, cf in bond.cash_flows():
    pv = cf / (1 + y) ** t
    print(f"  t={t}: CF={cf:.2f}  →  PV={pv:.4f}")
    total += pv

print(f"\n  Sum of PVs (long form):  {total:.4f}")
print(f"  Closed form:             {bond.price_closed_form(0.06):.4f}")
print(f"  Match: {abs(total - bond.price_closed_form(0.06)) < 0.0001}")


# ── Problem 2 ─────────────────────────────────────────────────────────────────
separator("Problem 2 — Same bond, YTM=5% (at par?)")

p = bond.price(0.05)
print(f"\n  Price at YTM=5%: {p:.4f}")
print(f"  Explanation: coupon rate = YTM → bond prices at par (face value)")


# ── Problem 3 ─────────────────────────────────────────────────────────────────
separator("Problem 3 — Price vs YTM pattern")

for ytm in [0.04, 0.05, 0.06]:
    p = bond.price(ytm)
    label = "above par" if p > 1000 else ("at par" if p == 1000 else "below par")
    print(f"  YTM={ytm:.0%}  →  Price={p:.4f}  ({label})")

print("\n  Pattern: as YTM rises, price falls (inverse relationship)")


# ── Problem 4 ─────────────────────────────────────────────────────────────────
separator("Problem 4 — Semi-annual bond, 3Y, YTM=5% annual")

# $25 semi-annual coupon on $1000 face = 5% annual coupon rate
semi_bond = Bond(face=1000, coupon_rate=0.05, periods=6, freq=2)  # 6 semi-annual periods

print(f"\n  Per-period YTM: {0.05/2:.4f} (= 5% annual / 2)")
p = semi_bond.price(0.05)
print(f"  Price: {p:.4f}")


# ── Problem 5 ─────────────────────────────────────────────────────────────────
separator("Problem 5 — Accrued interest, 6% bond, 30 days in")

bond_6pct = Bond(face=1000, coupon_rate=0.06, periods=6, freq=2)
ai = bond_6pct.accrued_interest(days_since_coupon=30, days_in_period=180)
print(f"\n  Semi-annual coupon: {bond_6pct.coupon_rate / bond_6pct.freq * bond_6pct.face:.2f}")
print(f"  Accrued interest (30/180 days): {ai:.4f}")


# ── YTM solver check ──────────────────────────────────────────────────────────
separator("Bonus — YTM solver round-trip check")

known_price = bond.price(0.06)
solved_ytm = bond.ytm(known_price)
print(f"\n  Price at YTM=6%: {known_price:.6f}")
print(f"  Solved YTM back from price: {solved_ytm:.6f}")
print(f"  Round-trip error: {abs(solved_ytm - 0.06):.2e}")
