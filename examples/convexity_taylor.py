"""
Convexity examples: convexity, Taylor decomposition of price changes, scenario analysis.
Run from the repository root: python examples/convexity_taylor.py

Example bond: 5% annual coupon, face $1,000, 5 years, YTM = 6%
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bond import Bond
from src.risk import modified_duration, macaulay_duration
from src.convexity import (
    convexity,
    convexity_exact,
    duration_term,
    convexity_term,
    taylor_price_change,
    scenario_analysis,
    convexity_summary,
)


def separator(title):
    print(f"\n{'─' * 58}")
    print(f"  {title}")
    print('─' * 58)


bond = Bond(face=1000, coupon_rate=0.05, periods=5, freq=1)
ytm  = 0.06


# ── Problem 1 ─────────────────────────────────────────────────────────────────
separator("Problem 1 — Convexity calculation (5% annual, 5Y, YTM=6%)")

y = ytm / bond.freq
N = bond.periods * bond.freq
P = bond.price(ytm)
C = (bond.coupon_rate / bond.freq) * bond.face

print(f"\n  {'t':<6} {'CF':>8} {'t(t+1)':>8} {'CF/(1+y)^(t+2)':>18} {'t(t+1)·CF/(1+y)^(t+2)':>24}")
print(f"  {'─'*6} {'─'*8} {'─'*8} {'─'*18} {'─'*24}")

total = 0.0
for t in range(1, N + 1):
    cf     = C if t < N else C + bond.face
    term   = (t * (t + 1) * cf) / (1 + y) ** (t + 2)
    total += term
    print(f"  {t:<6} {cf:>8.2f} {t*(t+1):>8} {cf/(1+y)**(t+2):>18.4f} {term:>24.4f}")

conv_manual = total / (P * bond.freq ** 2)
conv_fn     = convexity(bond, ytm)
conv_fd     = convexity_exact(bond, ytm)

print(f"\n  Σ = {total:.4f}")
print(f"  Convexity (manual)         : {conv_manual:.4f}")
print(f"  convexity() function       : {conv_fn:.4f}")
print(f"  convexity_exact() finite Δ : {conv_fd:.4f}")
print(f"  All match: {abs(conv_manual - conv_fn) < 1e-6 and abs(conv_fn - conv_fd) < 1e-4}")


# ── Problem 2 ─────────────────────────────────────────────────────────────────
separator("Problem 2 — +100bp: duration only vs duration + convexity vs exact")

dy    = 0.01
p     = bond.price(ytm)
mod   = modified_duration(bond, ytm)
conv  = convexity(bond, ytm)
result = taylor_price_change(bond, ytm, dy)

print(f"\n  Base price          : ${p:.4f}")
print(f"  YTM shift           : +100 bps")
print(f"\n  Duration term       : {result['dur_term']:+.4f}")
print(f"  Convexity term      : {result['conv_term']:+.4f}  (always positive)")
print(f"  Taylor total        : {result['taylor_total']:+.4f}")
print(f"  Exact ΔP            : {result['exact_change']:+.4f}")
print(f"  Residual            : {result['residual']:+.4f}  (higher-order terms)")
print(f"\n  Duration only price : ${p + (-mod * p * dy):.4f}")
print(f"  Taylor approx price : ${p + result['taylor_total']:.4f}")
print(f"  Exact new price     : ${result['new_price']:.4f}")


# ── Problem 3 ─────────────────────────────────────────────────────────────────
separator("Problem 3 — -100bp: asymmetry of convexity")

dy_down = -0.01
result_down = taylor_price_change(bond, ytm, dy_down)
result_up   = taylor_price_change(bond, ytm,  0.01)

print(f"\n  Comparing +100bp vs -100bp:")
print(f"\n  {'':30} {'−100bp':>12} {'+ 100bp':>12}")
print(f"  {'─'*30} {'─'*12} {'─'*12}")
print(f"  {'Duration term':30} {result_down['dur_term']:>+12.4f} {result_up['dur_term']:>+12.4f}")
print(f"  {'Convexity term':30} {result_down['conv_term']:>+12.4f} {result_up['conv_term']:>+12.4f}")
print(f"  {'Taylor total':30} {result_down['taylor_total']:>+12.4f} {result_up['taylor_total']:>+12.4f}")
print(f"  {'Exact ΔP':30} {result_down['exact_change']:>+12.4f} {result_up['exact_change']:>+12.4f}")
print(f"\n  Gain on −100bp ({abs(result_down['exact_change']):.4f}) > Loss on +100bp ({abs(result_up['exact_change']):.4f})")
print(f"  Asymmetry = {abs(result_down['exact_change']) - abs(result_up['exact_change']):.4f}  ← this is convexity's value")


# ── Problem 4 ─────────────────────────────────────────────────────────────────
separator("Problem 4 — 30Y zero coupon convexity comparison")

zero_30 = Bond(face=1000, coupon_rate=0.0, periods=30, freq=1)
ytm_z   = 0.05

conv_5y  = convexity(bond, ytm)
conv_30z = convexity(zero_30, ytm_z)

# Simplified zero-coupon formula: Convexity ≈ N(N+1)/(1+y)²
N = 30
conv_approx = N * (N + 1) / (1 + ytm_z) ** 2

print(f"\n  5Y 5% coupon bond (YTM=6%):   Convexity = {conv_5y:.4f}")
print(f"  30Y zero coupon  (YTM=5%):   Convexity = {conv_30z:.4f}")
print(f"  30Y zero approx N(N+1)/(1+y)²: {conv_approx:.4f}")
print(f"\n  30Y zero has {conv_30z/conv_5y:.1f}x more convexity than 5Y coupon bond")
print(f"  Higher maturity + zero coupon = maximum convexity")


# ── Problem 5 ─────────────────────────────────────────────────────────────────
separator("Problem 5 — High vs low convexity in volatile rates")

bond_hi_conv = Bond(face=1000, coupon_rate=0.02, periods=10, freq=1)
bond_lo_conv = Bond(face=1000, coupon_rate=0.08, periods=10, freq=1)
ytm_c = 0.05

conv_hi = convexity(bond_hi_conv, ytm_c)
conv_lo = convexity(bond_lo_conv, ytm_c)

print(f"\n  Bond A (2% coupon, 10Y):  Convexity = {conv_hi:.4f}")
print(f"  Bond B (8% coupon, 10Y):  Convexity = {conv_lo:.4f}")
print(f"\n  Bond A has {conv_hi/conv_lo:.2f}x more convexity")
print(f"  In volatile rate environments: prefer Bond A (higher convexity)")
print(f"  You gain more on rallies and lose less on sell-offs")


# ── Full scenario table ───────────────────────────────────────────────────────
separator("Full scenario analysis — Taylor decomposition")

scenarios = scenario_analysis(bond, ytm)
print(f"\n  {'Shock':>8} {'Dur term':>10} {'Conv term':>10} {'Taylor':>10} {'Exact ΔP':>10} {'Residual':>10}")
print(f"  {'─'*8} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")
for s in scenarios:
    label = f"{s['bp']:+d} bps"
    print(f"  {label:>8} {s['dur_term']:>+10.4f} {s['conv_term']:>+10.4f} {s['taylor_total']:>+10.4f} {s['exact_change']:>+10.4f} {s['residual']:>+10.4f}")


# ── Summary ───────────────────────────────────────────────────────────────────
separator("convexity_summary() helper")

summary = convexity_summary(bond, ytm)
print()
for k, v in summary.items():
    print(f"  {k:<22} {v:>14.6f}")
