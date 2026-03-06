"""
Bond Pricing & Risk Analytics Tool
Day 1: Core bond pricing — PV of cash flows, YTM, clean/dirty price

Formula:
    P = C * [1 - (1+y)^(-N)] / y  +  F * (1+y)^(-N)
"""


class Bond:
    """
    A fixed coupon bond.

    Parameters
    ----------
    face        : float  — face (par) value, e.g. 1000
    coupon_rate : float  — annual coupon rate as decimal, e.g. 0.05 for 5%
    periods     : int    — number of periods to maturity
    freq        : int    — coupon payments per year (1=annual, 2=semi-annual)
    """

    def __init__(self, face: float, coupon_rate: float, periods: int, freq: int = 2):
        self.face = face
        self.coupon_rate = coupon_rate
        self.periods = periods          # total number of coupon periods
        self.freq = freq                # payments per year

    # ── Cash flows ────────────────────────────────────────────────────────────

    def cash_flows(self) -> list[tuple[int, float]]:
        """Return list of (period, cash_flow) for every payment."""
        coupon = (self.coupon_rate / self.freq) * self.face
        flows = [(t, coupon) for t in range(1, self.periods + 1)]
        # Add face value at final period
        flows[-1] = (self.periods, coupon + self.face)
        return flows

    # ── Pricing ───────────────────────────────────────────────────────────────

    def price(self, ytm: float) -> float:
        """
        Full (dirty) price — PV of all cash flows discounted at YTM.

        ytm : annual YTM as decimal (e.g. 0.06 for 6%)
        """
        y = ytm / self.freq          # per-period yield
        total = 0.0
        for t, cf in self.cash_flows():
            total += cf / (1 + y) ** t
        return total

    def price_closed_form(self, ytm: float) -> float:
        """
        Same result as price() via the geometric-series closed form.
        Useful to verify the long-form sum is correct.

        P = C * [1 - (1+y)^(-N)] / y  +  F * (1+y)^(-N)
        """
        y = ytm / self.freq
        C = (self.coupon_rate / self.freq) * self.face
        N = self.periods
        if y == 0:
            return C * N + self.face
        pv_coupons = C * (1 - (1 + y) ** -N) / y
        pv_face = self.face / (1 + y) ** N
        return pv_coupons + pv_face

    # ── Accrued interest & clean price ────────────────────────────────────────

    def accrued_interest(self, days_since_coupon: int, days_in_period: int) -> float:
        """
        Accrued = Coupon * (days since last coupon / days in coupon period)
        """
        coupon = (self.coupon_rate / self.freq) * self.face
        return coupon * (days_since_coupon / days_in_period)

    def clean_price(self, ytm: float, days_since_coupon: int, days_in_period: int) -> float:
        """Clean price = Dirty price - Accrued interest."""
        dirty = self.price(ytm)
        accrued = self.accrued_interest(days_since_coupon, days_in_period)
        return dirty - accrued

    # ── YTM solver ────────────────────────────────────────────────────────────

    def ytm(self, price: float, tol: float = 1e-10, max_iter: int = 500) -> float:
        """
        Solve for YTM given a market price (Newton-Raphson).
        Returns annual YTM as a decimal.
        """
        # Initial guess: coupon rate
        y = self.coupon_rate

        for _ in range(max_iter):
            p = self.price(y)
            # Numerical derivative dp/dy
            dp = (self.price(y + 1e-6) - self.price(y - 1e-6)) / 2e-6
            delta = (p - price) / dp
            y -= delta
            if abs(delta) < tol:
                break

        return y

    # ── Display ───────────────────────────────────────────────────────────────

    def __repr__(self):
        return (
            f"Bond(face={self.face}, coupon={self.coupon_rate:.2%}, "
            f"periods={self.periods}, freq={self.freq})"
        )
