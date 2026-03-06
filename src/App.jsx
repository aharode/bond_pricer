import { useState, useEffect, useCallback } from "react";

/* ─────────────────────────────────────────────────────────────────────────────
   MATH ENGINE  (mirrors src/bond.py exactly)
───────────────────────────────────────────────────────────────────────────── */

function calcPrice(face, couponRate, periods, freq, ytm) {
  const C = (couponRate / freq) * face;
  const y = ytm / freq;
  const N = periods * freq;
  if (Math.abs(y) < 1e-12) return C * N + face;
  const pvC = C * (1 - Math.pow(1 + y, -N)) / y;
  const pvF = face / Math.pow(1 + y, N);
  return pvC + pvF;
}

function solveYTM(face, couponRate, periods, freq, price) {
  let y = couponRate;
  for (let i = 0; i < 500; i++) {
    const p  = calcPrice(face, couponRate, periods, freq, y);
    const dp = (calcPrice(face, couponRate, periods, freq, y + 1e-6) -
                calcPrice(face, couponRate, periods, freq, y - 1e-6)) / 2e-6;
    if (Math.abs(dp) < 1e-14) break;
    const delta = (p - price) / dp;
    y -= delta;
    if (Math.abs(delta) < 1e-10) break;
  }
  return y;
}

function calcAccrued(face, couponRate, freq, daysSince, daysInPeriod) {
  const coupon = (couponRate / freq) * face;
  return coupon * (daysSince / daysInPeriod);
}

function buildCashFlows(face, couponRate, periods, freq, ytm) {
  const C   = (couponRate / freq) * face;
  const y   = ytm / freq;
  const N   = periods * freq;
  const P   = calcPrice(face, couponRate, periods, freq, ytm);
  const rows = [];
  for (let t = 1; t <= N; t++) {
    const cf  = t < N ? C : C + face;
    const pv  = cf / Math.pow(1 + y, t);
    const w   = pv / P;
    const tYr = t / freq;
    rows.push({ t, tYr, cf, pv, w, durContrib: tYr * w });
  }
  return rows;
}

/* ─────────────────────────────────────────────────────────────────────────────
   TINY REUSABLE COMPONENTS
───────────────────────────────────────────────────────────────────────────── */

const AMBER   = "#F0A500";
const GREEN   = "#4CAF92";
const RED     = "#E05A4E";
const BG      = "#070709";
const SURFACE = "#0C0C0F";
const BORDER  = "#18181C";
const MUTED   = "#333340";
const DIM     = "#55556A";
const TEXT    = "#E2E2EE";

function Label({ children }) {
  return (
    <div style={{
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: 9,
      letterSpacing: "0.18em",
      textTransform: "uppercase",
      color: DIM,
      marginBottom: 5,
    }}>
      {children}
    </div>
  );
}

function KpiCard({ label, value, sub, highlight, delay = 0 }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  return (
    <div style={{
      background: SURFACE,
      border: `1px solid ${highlight ? AMBER + "44" : BORDER}`,
      padding: "14px 18px",
      opacity: visible ? 1 : 0,
      transform: visible ? "translateY(0)" : "translateY(8px)",
      transition: "opacity 0.4s ease, transform 0.4s ease",
      position: "relative",
      overflow: "hidden",
    }}>
      {highlight && (
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: 1,
          background: `linear-gradient(90deg, transparent, ${AMBER}, transparent)`,
        }} />
      )}
      <Label>{label}</Label>
      <div style={{
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 20,
        fontWeight: 600,
        color: highlight ? AMBER : TEXT,
        letterSpacing: "-0.02em",
        lineHeight: 1,
      }}>
        {value}
      </div>
      {sub && (
        <div style={{
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: 10,
          color: MUTED,
          marginTop: 5,
        }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function FieldGroup({ label, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <Label>{label}</Label>
      {children}
    </div>
  );
}

const inputStyle = {
  width: "100%",
  background: "#0A0A0D",
  border: `1px solid ${BORDER}`,
  color: TEXT,
  fontFamily: "'IBM Plex Mono', monospace",
  fontSize: 13,
  padding: "7px 10px",
  outline: "none",
  transition: "border-color 0.15s",
  boxSizing: "border-box",
};

function NumInput({ value, onChange, step, min, max, disabled }) {
  return (
    <input
      type="number"
      value={value}
      onChange={e => onChange(e.target.value)}
      step={step}
      min={min}
      max={max}
      disabled={disabled}
      style={{ ...inputStyle, opacity: disabled ? 0.4 : 1, cursor: disabled ? "not-allowed" : "text" }}
      onFocus={e => { if (!disabled) e.target.style.borderColor = AMBER; }}
      onBlur={e => { e.target.style.borderColor = BORDER; }}
    />
  );
}

function ToggleGroup({ value, onChange, options }) {
  return (
    <div style={{ display: "flex", gap: 1 }}>
      {options.map(opt => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          style={{
            flex: 1,
            padding: "7px 4px",
            background: value === opt.value ? AMBER : "#0A0A0D",
            color: value === opt.value ? "#070709" : DIM,
            border: `1px solid ${value === opt.value ? AMBER : BORDER}`,
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 11,
            fontWeight: value === opt.value ? 600 : 400,
            cursor: "pointer",
            letterSpacing: "0.1em",
            transition: "all 0.15s",
          }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function SectionDivider({ children }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      margin: "22px 0 18px",
    }}>
      <div style={{ width: 4, height: 4, background: AMBER, transform: "rotate(45deg)" }} />
      <span style={{
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 9,
        letterSpacing: "0.22em",
        textTransform: "uppercase",
        color: AMBER,
      }}>
        {children}
      </span>
      <div style={{ flex: 1, height: 1, background: BORDER }} />
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   SOLVE MODE TOGGLE
───────────────────────────────────────────────────────────────────────────── */

function SolveToggle({ mode, onChange }) {
  return (
    <div style={{
      display: "flex",
      background: "#0A0A0D",
      border: `1px solid ${BORDER}`,
      marginBottom: 22,
      position: "relative",
    }}>
      {[
        { id: "price", label: "YTM → Price" },
        { id: "ytm",   label: "Price → YTM"  },
      ].map(opt => (
        <button
          key={opt.id}
          onClick={() => onChange(opt.id)}
          style={{
            flex: 1,
            padding: "9px 0",
            background: mode === opt.id ? AMBER + "15" : "transparent",
            color: mode === opt.id ? AMBER : DIM,
            border: "none",
            borderBottom: mode === opt.id ? `2px solid ${AMBER}` : "2px solid transparent",
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 10,
            letterSpacing: "0.15em",
            textTransform: "uppercase",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   CASH FLOW TABLE
───────────────────────────────────────────────────────────────────────────── */

function CashFlowTable({ rows, totalDur }) {
  const maxPV = Math.max(...rows.map(r => r.pv));

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{
        width: "100%",
        borderCollapse: "collapse",
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 11,
      }}>
        <thead>
          <tr>
            {["Period", "Time (yr)", "Cash Flow ($)", "PV of CF ($)", "PV Weight", "Duration Contrib (yr)"].map(h => (
              <th key={h} style={{
                padding: "8px 12px",
                textAlign: h === "Period" ? "left" : "right",
                color: DIM,
                fontSize: 9,
                letterSpacing: "0.15em",
                textTransform: "uppercase",
                borderBottom: `1px solid ${BORDER}`,
                fontWeight: 400,
                whiteSpace: "nowrap",
              }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const isFinal = i === rows.length - 1;
            return (
              <tr key={row.t} style={{ transition: "background 0.15s" }}
                onMouseEnter={e => e.currentTarget.style.background = "#FFFFFF05"}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}
              >
                <td style={{ padding: "7px 12px", color: DIM, borderBottom: `1px solid ${BORDER}88` }}>{row.t}</td>
                <td style={{ padding: "7px 12px", textAlign: "right", color: DIM, borderBottom: `1px solid ${BORDER}88` }}>{row.tYr.toFixed(1)}</td>
                <td style={{ padding: "7px 12px", textAlign: "right", color: isFinal ? AMBER : TEXT, borderBottom: `1px solid ${BORDER}88` }}>
                  {row.cf.toFixed(2)}
                </td>
                <td style={{ padding: "7px 12px", textAlign: "right", color: TEXT, borderBottom: `1px solid ${BORDER}88` }}>
                  {row.pv.toFixed(4)}
                </td>
                <td style={{ padding: "7px 12px", borderBottom: `1px solid ${BORDER}88` }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8 }}>
                    <div style={{
                      width: Math.max(2, (row.pv / maxPV) * 72),
                      height: 5,
                      background: isFinal ? AMBER : "#2A3A2A",
                      transition: "width 0.3s ease",
                    }} />
                    <span style={{ color: DIM, minWidth: 42, textAlign: "right" }}>
                      {(row.w * 100).toFixed(2)}%
                    </span>
                  </div>
                </td>
                <td style={{ padding: "7px 12px", textAlign: "right", color: MUTED, borderBottom: `1px solid ${BORDER}88` }}>
                  {row.durContrib.toFixed(4)}
                </td>
              </tr>
            );
          })}

          {/* Totals row */}
          <tr>
            <td colSpan={5} style={{ padding: "10px 12px", color: DIM, fontSize: 9, letterSpacing: "0.15em", textTransform: "uppercase", borderTop: `1px solid ${BORDER}` }}>
              Σ Duration Contributions = Macaulay Duration
            </td>
            <td style={{ padding: "10px 12px", textAlign: "right", color: AMBER, fontWeight: 600, borderTop: `1px solid ${BORDER}` }}>
              {totalDur.toFixed(4)} yr
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   MAIN APP
───────────────────────────────────────────────────────────────────────────── */

export default function App() {
  // ── Inputs ────────────────────────────────────────────────────────────────
  const [face,        setFace]        = useState(1000);
  const [couponPct,   setCouponPct]   = useState(5.0);
  const [periods,     setPeriods]     = useState(5);
  const [freq,        setFreq]        = useState(2);
  const [ytmPct,      setYtmPct]      = useState(6.0);
  const [priceInput,  setPriceInput]  = useState("");
  const [daysSince,   setDaysSince]   = useState(30);
  const [daysInPer,   setDaysInPer]   = useState(180);
  const [solveMode,   setSolveMode]   = useState("price"); // "price" | "ytm"

  // ── Derived values ────────────────────────────────────────────────────────
  const couponRate = couponPct / 100;

  const { ytm, dirtyPrice, cleanPrice, accrued, cfRows, macDur, solvedYTM } =
    useCallback(() => {
      let ytm, dirtyPrice, solvedYTM = null;

      if (solveMode === "price") {
        ytm        = ytmPct / 100;
        dirtyPrice = calcPrice(face, couponRate, periods, freq, ytm);
      } else {
        const p    = parseFloat(priceInput);
        dirtyPrice = isNaN(p) ? 0 : p;
        solvedYTM  = isNaN(p) || p <= 0
          ? null
          : solveYTM(face, couponRate, periods, freq, p);
        ytm = solvedYTM ?? couponRate;
      }

      const accrued    = calcAccrued(face, couponRate, freq, daysSince, daysInPer);
      const cleanPrice = dirtyPrice - accrued;
      const cfRows     = buildCashFlows(face, couponRate, periods, freq, ytm);
      const macDur     = cfRows.reduce((s, r) => s + r.durContrib, 0);

      return { ytm, dirtyPrice, cleanPrice, accrued, cfRows, macDur, solvedYTM };
    }, [face, couponRate, periods, freq, ytmPct, priceInput, daysSince, daysInPer, solveMode])();

  // Sync price input when switching to ytm mode
  useEffect(() => {
    if (solveMode === "ytm" && priceInput === "") {
      setPriceInput(calcPrice(face, couponRate, periods, freq, ytmPct / 100).toFixed(4));
    }
  }, [solveMode]);

  const parStatus   = dirtyPrice > face * 1.001 ? "PREMIUM" : dirtyPrice < face * 0.999 ? "DISCOUNT" : "AT PAR";
  const parColor    = dirtyPrice > face * 1.001 ? GREEN     : dirtyPrice < face * 0.999 ? RED        : AMBER;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ background: BG, minHeight: "100vh", color: TEXT }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${BG}; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: ${BG}; }
        ::-webkit-scrollbar-thumb { background: ${MUTED}; }
        input[type=number] { -moz-appearance: textfield; }
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; }
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100vh); }
        }
      `}</style>

      {/* ── HEADER ─────────────────────────────────────────────────────── */}
      <header style={{
        position: "sticky", top: 0, zIndex: 50,
        borderBottom: `1px solid ${BORDER}`,
        background: `${BG}EE`,
        backdropFilter: "blur(8px)",
        padding: "0 28px",
        height: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 2, height: 18, background: AMBER }} />
            <span style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 12,
              fontWeight: 600,
              color: TEXT,
              letterSpacing: "0.1em",
            }}>
              BOND ANALYTICS
            </span>
          </div>
          <div style={{ width: 1, height: 16, background: BORDER }} />
          <span style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 9,
            color: MUTED,
            letterSpacing: "0.2em",
          }}>
            PROJECT 1 · DAY 1
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 9,
            color: parColor,
            border: `1px solid ${parColor}44`,
            padding: "2px 8px",
            letterSpacing: "0.15em",
          }}>
            {parStatus}
          </span>
          <span style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 9,
            color: MUTED,
            letterSpacing: "0.1em",
          }}>
            {new Date().toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" }).toUpperCase()}
          </span>
        </div>
      </header>

      {/* ── BODY ───────────────────────────────────────────────────────── */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "280px 1fr",
        minHeight: "calc(100vh - 50px)",
      }}>

        {/* ── LEFT PANEL — INPUTS ─────────────────────────────────────── */}
        <aside style={{
          borderRight: `1px solid ${BORDER}`,
          padding: "24px 20px",
          overflowY: "auto",
          background: SURFACE,
        }}>
          <SectionDivider>Solve Mode</SectionDivider>
          <SolveToggle mode={solveMode} onChange={m => { setSolveMode(m); }} />

          <SectionDivider>Bond Parameters</SectionDivider>

          <FieldGroup label="Face Value ($)">
            <NumInput value={face} onChange={v => setFace(parseFloat(v) || 0)} step={100} min={100} />
          </FieldGroup>

          <FieldGroup label="Annual Coupon Rate (%)">
            <NumInput value={couponPct} onChange={v => setCouponPct(parseFloat(v) || 0)} step={0.25} min={0} max={30} />
          </FieldGroup>

          <FieldGroup label="Years to Maturity">
            <NumInput value={periods} onChange={v => setPeriods(parseInt(v) || 1)} step={1} min={1} max={50} />
          </FieldGroup>

          <FieldGroup label="Payment Frequency">
            <ToggleGroup
              value={freq}
              onChange={setFreq}
              options={[{ value: 1, label: "Annual" }, { value: 2, label: "Semi-Annual" }]}
            />
          </FieldGroup>

          {solveMode === "price" ? (
            <FieldGroup label="YTM (%) — solve for price">
              <NumInput value={ytmPct} onChange={v => setYtmPct(parseFloat(v) || 0)} step={0.1} min={0.01} max={50} />
            </FieldGroup>
          ) : (
            <FieldGroup label="Market Price ($) — solve for YTM">
              <NumInput
                value={priceInput}
                onChange={v => setPriceInput(v)}
                step={0.01}
                min={0.01}
              />
            </FieldGroup>
          )}

          <SectionDivider>Accrued Interest</SectionDivider>

          <FieldGroup label="Days Since Last Coupon">
            <NumInput value={daysSince} onChange={v => setDaysSince(parseInt(v) || 0)} step={1} min={0} />
          </FieldGroup>

          <FieldGroup label="Days in Coupon Period">
            <NumInput value={daysInPer} onChange={v => setDaysInPer(parseInt(v) || 1)} step={1} min={1} />
          </FieldGroup>

          {/* Formula reference */}
          <div style={{
            marginTop: 28,
            padding: "14px",
            border: `1px solid ${BORDER}`,
            background: BG,
          }}>
            <div style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 9,
              letterSpacing: "0.18em",
              color: MUTED,
              textTransform: "uppercase",
              marginBottom: 10,
            }}>
              Day 1 Formulas
            </div>
            {[
              ["Price",    "C·[1-(1+y)⁻ᴺ]/y + F·(1+y)⁻ᴺ"],
              ["Accrued",  "C × (t / T)"],
              ["Clean",    "Dirty − Accrued"],
              ["Mac. Dur", "Σ t · PV(CFₜ) / P"],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
                <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 9, color: AMBER, minWidth: 56 }}>{k}</span>
                <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 9, color: MUTED, lineHeight: 1.5 }}>{v}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* ── RIGHT PANEL — OUTPUT ────────────────────────────────────── */}
        <main style={{ padding: "28px 32px", overflowY: "auto" }}>

          {/* ── SOLVED YTM BANNER (Price → YTM mode) ───────────────── */}
          {solveMode === "ytm" && solvedYTM !== null && (
            <div style={{
              marginBottom: 24,
              padding: "14px 20px",
              border: `1px solid ${AMBER}33`,
              background: `${AMBER}08`,
              display: "flex",
              alignItems: "center",
              gap: 16,
            }}>
              <div style={{ width: 2, height: 28, background: AMBER }} />
              <div>
                <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 9, color: DIM, letterSpacing: "0.18em", textTransform: "uppercase", marginBottom: 4 }}>
                  Solved YTM (Newton-Raphson)
                </div>
                <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 24, fontWeight: 600, color: AMBER, letterSpacing: "-0.02em" }}>
                  {(solvedYTM * 100).toFixed(6)}%
                </div>
              </div>
              <div style={{ marginLeft: "auto", fontFamily: "'IBM Plex Mono', monospace", fontSize: 9, color: MUTED, textAlign: "right", lineHeight: 2 }}>
                <div>Spread to coupon</div>
                <div style={{ color: solvedYTM > couponRate ? RED : GREEN }}>
                  {((solvedYTM - couponRate) * 10000).toFixed(1)} bps
                </div>
              </div>
            </div>
          )}

          {/* ── KPI GRID ────────────────────────────────────────────── */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 12,
            marginBottom: 24,
          }}>
            <KpiCard
              label="Dirty Price (Full Price)"
              value={`$${dirtyPrice.toFixed(4)}`}
              sub="What you actually pay"
              highlight
              delay={0}
            />
            <KpiCard
              label="Clean Price (Quoted)"
              value={`$${cleanPrice.toFixed(4)}`}
              sub="Bloomberg-quoted price"
              delay={60}
            />
            <KpiCard
              label="Accrued Interest"
              value={`$${accrued.toFixed(4)}`}
              sub={`${daysSince}/${daysInPer} days elapsed`}
              delay={120}
            />
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 12,
            marginBottom: 32,
          }}>
            <KpiCard
              label="Macaulay Duration"
              value={`${macDur.toFixed(4)} yr`}
              sub="Weighted avg. time to CF"
              delay={180}
            />
            <KpiCard
              label="YTM"
              value={solveMode === "ytm" && solvedYTM ? `${(solvedYTM * 100).toFixed(4)}%` : `${ytmPct.toFixed(3)}%`}
              sub="Annual, per-period adjusted"
              delay={240}
            />
            <KpiCard
              label="Coupon / Period"
              value={`$${((couponRate / freq) * face).toFixed(2)}`}
              sub={`${(couponPct / freq).toFixed(3)}% per period`}
              delay={300}
            />
          </div>

          {/* ── CASH FLOW TABLE ─────────────────────────────────────── */}
          <div style={{
            border: `1px solid ${BORDER}`,
            background: SURFACE,
          }}>
            <div style={{
              padding: "14px 20px",
              borderBottom: `1px solid ${BORDER}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 4, height: 4, background: AMBER, transform: "rotate(45deg)" }} />
                <span style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 9,
                  letterSpacing: "0.2em",
                  textTransform: "uppercase",
                  color: AMBER,
                }}>
                  Cash Flow Breakdown
                </span>
              </div>
              <span style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 9,
                color: MUTED,
                letterSpacing: "0.1em",
              }}>
                {cfRows.length} periods · {freq === 1 ? "annual" : "semi-annual"}
              </span>
            </div>
            <CashFlowTable rows={cfRows} totalDur={macDur} />
          </div>

          {/* ── FOOTER NOTE ─────────────────────────────────────────── */}
          <div style={{
            marginTop: 28,
            padding: "12px 16px",
            border: `1px solid ${BORDER}`,
            display: "flex",
            gap: 24,
          }}>
            {[
              ["Price < Par",   "Coupon rate < YTM  →  bond trades at discount"],
              ["Price = Par",   "Coupon rate = YTM  →  bond trades at par"],
              ["Price > Par",   "Coupon rate > YTM  →  bond trades at premium"],
            ].map(([k, v]) => (
              <div key={k} style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 9, lineHeight: 1.8 }}>
                <span style={{ color: AMBER }}>{k}  </span>
                <span style={{ color: MUTED }}>{v}</span>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: 16,
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 9,
            color: BORDER,
            letterSpacing: "0.15em",
            textAlign: "center",
          }}>
            FIXED INCOME CAREER ACCELERATOR · PROJECT 1 · BOND PRICING & RISK ANALYTICS
          </div>
        </main>
      </div>
    </div>
  );
}
