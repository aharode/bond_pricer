"""
Duration and DV01 examples: Macaulay/modified duration, DV01, position DV01.
Run from the repository root: python examples/duration_dv01.py

Example bond: 5% annual coupon, face $1,000, 5 years, YTM = 6%
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bond import Bond
from src.risk import (
    macaulay_duration,
    modified_duration,
    dv01,
    dv01_exact,
    position_dv01,
    risk_summary,
)


def separator(title):
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print('─' * 55)


# ── Base bond ────────────────────────────────────────────────────────────────
bond = Bond(face=1000, coupon_rate=0.05, periods=5, freq=1)
ytm  = 0.06


# ── Problem 1 ─────────────────────────────────────────────────────────────────
separator("Problem 1 — Macaulay Duration (5% annual, 5Y, YTM=6%)")

y     = ytm / bond.freq
price = bond.price(ytm)

print(f"\n  {'Period':<8} {'CF':>8} {'PV(CF)':>10} {'t (yr)':>8} {'Weight':>8} {'t × w':>10}")
print(f"  {'─'*8} {'─'*8} {'─'*10} {'─'*8} {'─'*8} {'─'*10}")

total_dur = 0.0
for t, cf in bond.cash_flows():
    pv     = cf / (1 + y) ** t
    w      = pv / price
    t_yr   = t / bond.freq
    dc     = t_yr * w
    total_dur += dc
    print(f"  {t:<8} {cf:>8.2f} {pv:>10.4f} {t_yr:>8.1f} {w:>8.4f} {dc:>10.4f}")

print(f"\n  {'':>46} {'─'*10}")
print(f"  {'Macaulay Duration':>46} {total_dur:>10.4f} yr")
print(f"\n  Function result: {macaulay_duration(bond, ytm):.4f} yr")
print(f"  Match: {abs(total_dur - macaulay_duration(bond, ytm)) < 1e-8}")


# ── Problem 2 ─────────────────────────────────────────────────────────────────
separator("Problem 2 — Modified Duration + 50bp price change estimate")

mac = macaulay_duration(bond, ytm)
mod = modified_duration(bond, ytm)

print(f"\n  Macaulay Duration : {mac:.4f} yr")
print(f"  Modified Duration : {mod:.4f}  (= {mac:.4f} / (1 + {ytm:.2f}))")

dy           = 0.005   # 50 bps
approx_delta = -mod * price * dy
new_price_approx = price + approx_delta
new_price_exact  = bond.price(ytm + dy)

print("\n  YTM shift: +50 bps")
print(f"  ΔP (duration approx) : {approx_delta:+.4f}  → price = {new_price_approx:.4f}")
print(f"  ΔP (exact reprice)   : {new_price_exact - price:+.4f}  → price = {new_price_exact:.4f}")
print(f"  Approximation error  : {(new_price_exact - new_price_approx):.4f}  (the convexity term, see convexity_taylor.py)")


# ── Problem 3 ─────────────────────────────────────────────────────────────────
separator("Problem 3 — DV01 per bond + $10M position")

dv01_bond = dv01(bond, ytm)
dv01_chk  = dv01_exact(bond, ytm)
notional  = 10_000_000
pos_dv01  = position_dv01(bond, ytm, notional)

print(f"\n  Price            : ${price:.4f}")
print(f"  Modified Duration: {mod:.4f}")
print(f"  DV01 (formula)   : ${dv01_bond:.4f}  per ${bond.face} face")
print(f"  DV01 (finite Δ)  : ${dv01_chk:.4f}  ← cross-check (should match)")
print(f"  Match            : {abs(dv01_bond - dv01_chk) < 1e-6}")
print(f"\n  Position: ${notional:,.0f} face  ({notional // bond.face:,.0f} bonds)")
print(f"  Position DV01    : ${pos_dv01:,.2f}")
print(f"  Interpretation   : a 1bp move costs/earns ${pos_dv01:,.2f}")


# ── Problem 4 ─────────────────────────────────────────────────────────────────
separator("Problem 4 — Zero coupon bond, 10Y, YTM=5%")

zero = Bond(face=1000, coupon_rate=0.0, periods=10, freq=1)
ytm_z = 0.05

# Zero coupon: D_mac = maturity (all cash flow at final period)
mac_z = macaulay_duration(zero, ytm_z)
mod_z = modified_duration(zero, ytm_z)
dv01_z = dv01(zero, ytm_z)
price_z = zero.price(ytm_z)

print("\n  Zero coupon bond: 10Y, YTM=5%, face $1,000")
print(f"  Price            : ${price_z:.4f}")
print(f"  Macaulay Duration: {mac_z:.4f} yr  (should equal maturity = 10)")
print(f"  Modified Duration: {mod_z:.4f}      (= 10 / 1.05)")
print(f"  DV01             : ${dv01_z:.4f} per $1,000 face")


# ── Problem 5 ─────────────────────────────────────────────────────────────────
separator("Problem 5 — Low vs high coupon duration comparison")

bond_low  = Bond(face=1000, coupon_rate=0.02, periods=10, freq=1)
bond_high = Bond(face=1000, coupon_rate=0.08, periods=10, freq=1)
ytm_c = 0.05

mac_low  = macaulay_duration(bond_low,  ytm_c)
mac_high = macaulay_duration(bond_high, ytm_c)

print("\n  Both bonds: 10Y maturity, YTM=5%")
print(f"\n  Bond A (2% coupon):  D_mac = {mac_low:.4f} yr")
print(f"  Bond B (8% coupon):  D_mac = {mac_high:.4f} yr")
print(f"\n  Bond A has HIGHER duration by {mac_low - mac_high:.4f} yr")
print("  Why: lower coupon → less weight on early cash flows")
print("       → more weight concentrated at final principal payment")


# ── Full summary (risk_summary helper) ───────────────────────────────────────
separator("Bonus — risk_summary() for the example bond")

summary = risk_summary(bond, ytm, notional=10_000_000)
print()
for k, v in summary.items():
    print(f"  {k:<20} {v:>14.6f}")
