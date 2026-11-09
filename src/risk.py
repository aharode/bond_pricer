"""
Bond Analytics — duration and DV01

Formulas:
    D_mac = Σ [ t × PV(CFₜ) ] / P
    D_mod = D_mac / (1 + y/freq)
    Dollar Duration = D_mod × P
    DV01 = Dollar Duration × 0.0001
    Position DV01 = DV01 × (notional / face)
"""

from src.bond import Bond


# ── Macaulay Duration ─────────────────────────────────────────────────────────

def macaulay_duration(bond: Bond, ytm: float) -> float:
    """
    Weighted-average time to receive each cash flow.
    Weights = PV(CFₜ) / Price.

    D_mac = Σ [ t × PV(CFₜ) / P ]

    Where t is measured in years (period / freq).

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal

    Returns
    -------
    float — Macaulay duration in years
    """
    y     = ytm / bond.freq          # per-period yield
    price = bond.price(ytm)

    weighted_time = 0.0
    for t, cf in bond.cash_flows():
        pv             = cf / (1 + y) ** t
        t_years        = t / bond.freq
        weighted_time += t_years * pv

    return weighted_time / price


# ── Modified Duration ─────────────────────────────────────────────────────────

def modified_duration(bond: Bond, ytm: float) -> float:
    """
    First-order price sensitivity to yield changes.
    Answers: for a 1% move in yield, price changes by ~D_mod%.

    D_mod = D_mac / (1 + y/freq)

    For annual coupons:     D_mod = D_mac / (1 + y)
    For semi-annual coupons: D_mod = D_mac / (1 + y/2)

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal

    Returns
    -------
    float — Modified duration (unit: years, dimensionless sensitivity)
    """
    mac = macaulay_duration(bond, ytm)
    return mac / (1 + ytm / bond.freq)


# ── Dollar Duration ───────────────────────────────────────────────────────────

def dollar_duration(bond: Bond, ytm: float) -> float:
    """
    Dollar price change for a 1-unit (100%) move in yield.
    Rarely used directly — DV01 is the practical version.

    Dollar Duration = D_mod × Price

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal

    Returns
    -------
    float — dollar duration in $ per $face
    """
    mod  = modified_duration(bond, ytm)
    price = bond.price(ytm)
    return mod * price


# ── DV01 ──────────────────────────────────────────────────────────────────────

def dv01(bond: Bond, ytm: float) -> float:
    """
    Dollar Value of a Basis Point — the P&L change for a 1bp yield move.
    This is the unit rates traders use day to day.

    DV01 = D_mod × P × 0.0001
         = Dollar Duration × 0.0001

    Also computable directly as:
        DV01 = |dP/dy| × 0.0001
             ≈ (P(y - 0.0001) - P(y + 0.0001)) / 2

    Parameters
    ----------
    bond : Bond
    ytm  : float — annual YTM as decimal

    Returns
    -------
    float — DV01 in $ per $face notional
    """
    return dollar_duration(bond, ytm) * 0.0001


def dv01_exact(bond: Bond, ytm: float) -> float:
    """
    DV01 computed via finite difference (cross-check for the formula above).
    Uses a symmetric 1bp shock: (P(y-1bp) - P(y+1bp)) / 2
    """
    p_down = bond.price(ytm - 0.0001)
    p_up   = bond.price(ytm + 0.0001)
    return (p_down - p_up) / 2


# ── Position DV01 ─────────────────────────────────────────────────────────────

def position_dv01(bond: Bond, ytm: float, notional: float) -> float:
    """
    Scale DV01 to a position size.

    If you hold $10M face value of a bond with DV01 = $0.045 per $1000 face:
        Position DV01 = 0.045 × (10,000,000 / 1000) = $450

    A 1bp move costs or earns $450 on that position.

    Parameters
    ----------
    bond     : Bond
    ytm      : float — annual YTM as decimal
    notional : float — total face value held (e.g. 10_000_000)

    Returns
    -------
    float — total position DV01 in $
    """
    dv01_per_bond = dv01(bond, ytm)
    return dv01_per_bond * (notional / bond.face)


# ── Summary ───────────────────────────────────────────────────────────────────

def risk_summary(bond: Bond, ytm: float, notional: float | None = None) -> dict:
    """
    Return all risk metrics in one dict.
    Convenient for display and testing.

    Parameters
    ----------
    bond     : Bond
    ytm      : float — annual YTM as decimal
    notional : float — optional position size for position DV01

    Returns
    -------
    dict with keys: price, mac_dur, mod_dur, dollar_dur, dv01,
                    dv01_exact, position_dv01 (if notional provided)
    """
    price    = bond.price(ytm)
    mac      = macaulay_duration(bond, ytm)
    mod      = modified_duration(bond, ytm)
    dol      = dollar_duration(bond, ytm)
    dv01_val = dv01(bond, ytm)
    dv01_ex  = dv01_exact(bond, ytm)

    result = {
        "price":        price,
        "mac_dur":      mac,
        "mod_dur":      mod,
        "dollar_dur":   dol,
        "dv01":         dv01_val,
        "dv01_exact":   dv01_ex,
    }

    if notional is not None:
        result["position_dv01"] = position_dv01(bond, ytm, notional)

    return result
