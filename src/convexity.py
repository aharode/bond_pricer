"""
Bond Pricing & Risk Analytics Tool
Day 3: Convexity & Taylor Expansion

Formulas:
    Convexity = (1/P) × (1/(1+y)²) × Σ[ t(t+1) × CF / (1+y)ᵗ ]

    Taylor expansion (full price change approximation):
    ΔP ≈ -D_mod × P × Δy  +  ½ × Convexity × P × (Δy)²
          └── duration term ┘   └──── convexity term ────┘

    Convexity adjustment (dollar P&L from convexity):
    Conv. P&L = ½ × Convexity × P × (Δy)²

Key insight:
    - Convexity term is ALWAYS positive for option-free bonds
    - It adds to gains when yields fall
    - It cushions losses when yields rise
    - This asymmetry is why investors pay for convexity
"""

from src.bond import Bond
from src.risk import modified_duration, macaulay_duration


# ── Convexity ─────────────────────────────────────────────────────────────────

def convexity(bond: Bond, ytm: float) -> float:
    """
    Second derivative of price w.r.t. yield, scaled by price.

    Convexity = (1/P) × d²P/dy²
              = (1/P) × (1/(1+y)²) × Σ[ t(t+1) × CF / (1+y)ᵗ ]

    For semi-annual bonds: divide by freq² to convert to annual convexity.

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal

    Returns
    -------
    float — convexity in years² (dimensionless after scaling)
    """
    y = ytm / bond.freq
    P = bond.price(ytm)

    # bond.periods already counts coupon periods, so iterate over the actual
    # cash flows (t in periods) and convert to annual units with 1/freq².
    total = 0.0
    for t, cf in bond.cash_flows():
        total += (t * (t + 1) * cf) / (1 + y) ** (t + 2)

    return total / (P * bond.freq ** 2)


def convexity_exact(bond: Bond, ytm: float) -> float:
    """
    Convexity via finite difference — cross-check for the formula above.

    Convexity ≈ [P(y+h) - 2P(y) + P(y-h)] / (P × h²)

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal

    Returns
    -------
    float — convexity (should match convexity() closely)
    """
    h  = 0.0001
    p  = bond.price(ytm)
    p_up   = bond.price(ytm + h)
    p_down = bond.price(ytm - h)
    return (p_up - 2 * p + p_down) / (p * h ** 2)


# ── Taylor Expansion ──────────────────────────────────────────────────────────

def duration_term(bond: Bond, ytm: float, dy: float) -> float:
    """
    First-order (duration) term of the Taylor expansion.

    Duration term = -D_mod × P × Δy

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal
    dy   : float — yield change as decimal (e.g. 0.01 for +100bps)

    Returns
    -------
    float — dollar price change from duration term
    """
    mod = modified_duration(bond, ytm)
    p   = bond.price(ytm)
    return -mod * p * dy


def convexity_term(bond: Bond, ytm: float, dy: float) -> float:
    """
    Second-order (convexity) term of the Taylor expansion.

    Convexity term = ½ × Convexity × P × (Δy)²

    Always positive for option-free bonds regardless of direction of Δy.

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal
    dy   : float — yield change as decimal

    Returns
    -------
    float — dollar price change from convexity term (always >= 0)
    """
    conv = convexity(bond, ytm)
    p    = bond.price(ytm)
    return 0.5 * conv * p * dy ** 2


def taylor_price_change(bond: Bond, ytm: float, dy: float) -> dict:
    """
    Full Taylor approximation of price change.

    ΔP ≈ duration_term + convexity_term

    Returns a dict with each component for easy display.

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal
    dy   : float — yield change as decimal

    Returns
    -------
    dict with keys:
        dur_term    : float — duration contribution
        conv_term   : float — convexity contribution (always positive)
        taylor_total: float — sum of both terms
        exact_change: float — actual price change from repricing
        residual    : float — exact - taylor (higher-order error)
        new_ytm     : float — ytm + dy
        new_price   : float — exact new price
    """
    p          = bond.price(ytm)
    dur        = duration_term(bond, ytm, dy)
    conv       = convexity_term(bond, ytm, dy)
    taylor     = dur + conv
    new_ytm    = max(0.0001, ytm + dy)
    new_price  = bond.price(new_ytm)
    exact      = new_price - p

    return {
        "dur_term":     dur,
        "conv_term":    conv,
        "taylor_total": taylor,
        "exact_change": exact,
        "residual":     exact - taylor,
        "new_ytm":      new_ytm,
        "new_price":    new_price,
    }


# ── Scenario Builder ──────────────────────────────────────────────────────────

def scenario_analysis(bond: Bond, ytm: float,
                      shocks_bps: list = None) -> list[dict]:
    """
    Run Taylor decomposition across a range of yield shocks.

    Parameters
    ----------
    bond       : Bond
    ytm        : float — annual YTM as decimal
    shocks_bps : list of ints — yield shocks in basis points
                 default: [-200, -100, -50, -25, 25, 50, 100, 200]

    Returns
    -------
    list of dicts, one per shock, each containing:
        bp, dy, dur_term, conv_term, taylor_total,
        exact_change, residual, new_ytm, new_price
    """
    if shocks_bps is None:
        shocks_bps = [-200, -100, -50, -25, 25, 50, 100, 200]

    results = []
    for bp in shocks_bps:
        dy  = bp / 10000
        row = taylor_price_change(bond, ytm, dy)
        row["bp"] = bp
        row["dy"] = dy
        results.append(row)

    return results


# ── Summary ───────────────────────────────────────────────────────────────────

def convexity_summary(bond: Bond, ytm: float) -> dict:
    """
    Return all convexity metrics in one dict.

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal

    Returns
    -------
    dict with keys: price, convexity, convexity_exact,
                    conv_adj_100bp, conv_adj_200bp
    """
    p     = bond.price(ytm)
    conv  = convexity(bond, ytm)
    conv_x = convexity_exact(bond, ytm)

    return {
        "price":          p,
        "convexity":      conv,
        "convexity_exact": conv_x,
        "conv_adj_100bp": 0.5 * conv * p * 0.01 ** 2,
        "conv_adj_200bp": 0.5 * conv * p * 0.02 ** 2,
    }


# ── Internal helper ───────────────────────────────────────────────────────────

def _cash_flows_with_pv(bond: Bond, ytm: float):
    """Internal: return cash flows with PV for use in duration calculations."""
    y = ytm / bond.freq
    flows = []
    for t, cf in bond.cash_flows():
        pv = cf / (1 + y) ** t
        flows.append((t, cf, pv))
    return flows
