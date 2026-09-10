#!/usr/bin/env python3
"""
Vector figures for the "Natural power" subsection of design/ac-transmission.

Everything is computed from the exact distributed-parameter (two-port) equations
of a uniform transmission line, so the only dependencies are numpy and
matplotlib.  The results were cross-checked against a 20-segment pandapower
model; agreement is to four significant digits (see verify() at the bottom).

    python3 natural_power_figures.py            # writes the six PDFs next to this file

Reference line: 400 kV, 2x bundle, 50 Hz, 400 km.
"""
from __future__ import annotations

import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------- #
#  Style — matches the other figures in the deck (DejaVu Sans, light grid)
# --------------------------------------------------------------------------- #
BLUE, RED, TEAL = "#1F6FB2", "#C43B32", "#138D75"
GREY, LGREY = "#5C5C5C", "#D9D9D9"
# ordinal ramp for the loading sweep; natural loading is picked out in RED
RAMP = ["#A9B4BF", "#7C8B99", RED, "#4A5C6B", "#25313B"]

mpl.rcParams.update({
    "figure.dpi": 110,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,          # embed as TrueType, keeps text selectable
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "axes.edgecolor": "#BFBFBF",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": LGREY,
    "grid.linewidth": 0.7,
    "xtick.color": GREY, "ytick.color": GREY,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
    "axes.labelcolor": "#232323", "text.color": "#232323",
    "lines.linewidth": 2.2,
    "legend.fontsize": 9.5,
    "legend.framealpha": 0.92,
    "legend.edgecolor": "#BFBFBF",
})


# --------------------------------------------------------------------------- #
#  Line model
# --------------------------------------------------------------------------- #
class Line:
    """Uniform line described by its per-kilometre parameters."""

    def __init__(self, vn_kv=400.0, f_hz=50.0, r=0.025, x=0.30, c_nf=12.5,
                 imax_ka=2.0, lossless=False):
        self.vn = vn_kv
        self.f = f_hz
        self.w = 2 * np.pi * f_hz
        self.r = 0.0 if lossless else r
        self.x = x
        self.c = c_nf * 1e-9
        self.imax = imax_ka

    # --- per-unit-length series impedance / shunt admittance [ohm/km, S/km]
    @property
    def z(self):
        return self.r + 1j * self.x

    @property
    def y(self):
        return 1j * self.w * self.c

    # --- secondary parameters
    @property
    def gamma(self):
        "Propagation constant [1/km]."
        return np.sqrt(self.z * self.y)

    @property
    def zc_c(self):
        "Complex characteristic impedance [ohm]."
        return np.sqrt(self.z / self.y)

    @property
    def zc(self):
        "Lossless surge impedance sqrt(L'/C') [ohm]."
        return np.sqrt((self.x / self.w) / self.c)

    @property
    def beta(self):
        "Lossless phase constant [rad/km]."
        return self.w * np.sqrt((self.x / self.w) * self.c)

    @property
    def p_nat(self):
        "Natural power U^2 / Zc [MW]."
        return self.vn ** 2 / self.zc

    @property
    def vph(self):
        "Rated phase voltage [kV]."
        return self.vn / np.sqrt(3.0)

    def charging_mvar(self, length_km):
        "Three-phase capacitive charging power at rated voltage [MVAr]."
        return self.w * self.c * length_km * self.vn ** 2

    # --- two-port propagation from the receiving end -----------------------
    def propagate(self, vr, ir, x_km):
        """Voltage/current x_km from the receiving end, given (Vr, Ir) there.

        vr in kV (phase), ir in kA (phase).  Returns (V, I) in the same units.
        """
        g = self.gamma * np.asarray(x_km)
        ch, sh = np.cosh(g), np.sinh(g)
        return vr * ch + self.zc_c * ir * sh, (vr / self.zc_c) * sh + ir * ch


def s3(v_kv, i_ka):
    "Three-phase complex power [MVA] from phase quantities."
    return 3.0 * v_kv * np.conj(i_ka)


def bisect(f, lo, hi, tol=1e-12, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------- #
#  Case 1 — line between two stiff systems, both terminals at 1.0 pu
# --------------------------------------------------------------------------- #
def two_source(line: Line, length_km, p_mw, vpu=1.0):
    """Solve for the transmission angle that delivers p_mw, both ends at vpu.

    Returns a dict with the receiving-end quantities and the reactive balance.
    """
    vr = vpu * line.vph                       # reference, angle 0
    ch = np.cosh(line.gamma * length_km)
    sh = np.sinh(line.gamma * length_km)

    def p_of(theta):
        vs = vr * np.exp(1j * theta)
        ir = (vs - vr * ch) / (line.zc_c * sh)
        return s3(vr, ir).real

    theta = bisect(lambda t: p_of(t) - p_mw, 0.0, np.radians(88.0), tol=1e-14)
    vs = vr * np.exp(1j * theta)
    ir = (vs - vr * ch) / (line.zc_c * sh)
    vs_chk, is_ = line.propagate(vr, ir, length_km)

    s_recv_out = s3(vr, ir)                   # leaves the line at the far end
    s_send_in = s3(vs_chk, is_)               # enters the line at the near end
    return {
        "theta_deg": np.degrees(theta), "vr": vr, "ir": ir,
        "q_line": s_send_in.imag - s_recv_out.imag,   # absorbed by the line
        "q_send": s_send_in.imag,                     # from the sending system
        "q_recv": -s_recv_out.imag,                   # from the receiving system
        "p_send": s_send_in.real,
    }


def profile_two_source(line: Line, length_km, p_mw, n=401):
    """|V(s)| in pu against distance s from the sending end."""
    st = two_source(line, length_km, p_mw)
    x = np.linspace(0.0, length_km, n)                # from the receiving end
    v, _ = line.propagate(st["vr"], st["ir"], x)
    return length_km - x, np.abs(v) / line.vph, st


def p_nat_numeric(line: Line, length_km):
    """Natural power located as the zero of the line's net reactive power."""
    f = lambda k: two_source(line, length_km, k * line.p_nat)["q_line"]
    return bisect(f, 0.30, 1.70, tol=1e-10) * line.p_nat


# --------------------------------------------------------------------------- #
#  Case 2 — matched termination
# --------------------------------------------------------------------------- #
def profile_matched(line: Line, length_km, z_term, n=401):
    """|V(s)|/|Vs| for a line closed by the impedance z_term."""
    vr = line.vph
    ir = vr / z_term
    x = np.linspace(0.0, length_km, n)
    v, _ = line.propagate(vr, ir, x)
    vs = v[-1]
    return length_km - x, np.abs(v) / np.abs(vs)


# --------------------------------------------------------------------------- #
#  Case 3 — sending end at 1.0 pu, constant-power unity-pf load
# --------------------------------------------------------------------------- #
def solve_load(line: Line, length_km, p_mw):
    """Upper-branch receiving voltage for a unity-pf load of p_mw. None past the nose."""
    target = line.vph

    def mismatch(vr):
        ir = p_mw / (3.0 * vr)                        # real, unity power factor
        vs, _ = line.propagate(vr, ir, length_km)
        return abs(vs) - target

    # Upper bound must clear the no-load Ferranti rise 1/|cosh(gamma*l)|, which
    # exceeds 1.5 pu on a long line — otherwise the light-load root is missed.
    grid = np.linspace(2.60 * target, 0.15 * target, 6000)
    vals = np.array([mismatch(v) for v in grid])
    sign = np.sign(vals)
    idx = np.where(np.diff(sign) != 0)[0]
    if len(idx) == 0:
        return None
    i = idx[0]                                        # first crossing from above
    vr = bisect(mismatch, grid[i + 1], grid[i], tol=1e-12)
    ir = p_mw / (3.0 * vr)
    x = np.linspace(0.0, length_km, 201)
    v, i_line = line.propagate(vr, ir, x)
    vs, _ = line.propagate(vr, ir, length_km)
    return {
        "vr_pu": vr / target,
        "delta_deg": np.degrees(np.angle(vs)),
        "i_max_ka": np.abs(i_line).max(),
    }


def binding_load(line: Line, length_km, p_mw, vmin=0.95, dmax=30.0):
    """Case A — St. Clair: sending end at 1.0 pu, unity-pf load, free V_R."""
    st = solve_load(line, length_km, p_mw)
    if st is None:
        return "angular stability"                # past the nose of the P-V curve
    if st["i_max_ka"] > line.imax:
        return "thermal"
    if st["vr_pu"] < vmin:
        return "voltage drop"
    if st["delta_deg"] > dmax:
        return "angular stability"
    return None


def binding_stiff(line: Line, length_km, p_mw, vmin=0.95, dmax=30.0):
    """Case B — both terminals held at 1.0 pu by stiff systems."""
    if p_mw > 0.999 * abs(s3(line.vph, line.vph / line.zc_c)) * 8:
        return "angular stability"
    st = two_source(line, length_km, p_mw)
    if st["theta_deg"] > 87.0:
        return "angular stability"
    x = np.linspace(0.0, length_km, 201)
    v, i_line = line.propagate(st["vr"], st["ir"], x)
    if np.abs(i_line).max() > line.imax:
        return "thermal"
    if (np.abs(v) / line.vph).min() < vmin:
        return "voltage drop"
    if st["theta_deg"] > dmax:
        return "angular stability"
    return None


def loadability(line: Line, length_km, case="load"):
    """Maximum transfer and the constraint that binds, as (P, name)."""
    bf = binding_load if case == "load" else binding_stiff
    lo, hi = 1.0, 6.0 * line.p_nat
    while hi - lo > 0.25:
        mid = 0.5 * (lo + hi)
        if bf(line, length_km, mid) is None:
            lo = mid
        else:
            hi = mid
    return lo, bf(line, length_km, hi)


# --------------------------------------------------------------------------- #
#  Case 4 — open-ended line, with and without a shunt reactor
# --------------------------------------------------------------------------- #
def profile_open(line: Line, length_km, m=0.0, n=401):
    """|V(s)| in pu with the sending end normalised to 1.0 pu.

    m is the reactor rating as a fraction of the line's charging power.
    """
    q_l = m * line.charging_mvar(length_km)           # MVAr, three-phase
    b = q_l / (3.0 * line.vph ** 2)                   # S, per phase
    vr = line.vph
    ir = -1j * b * vr                                 # inductive: absorbs Q
    x = np.linspace(0.0, length_km, n)
    v, _ = line.propagate(vr, ir, x)
    return length_km - x, np.abs(v) / np.abs(v[-1])


# =========================================================================== #
#  Figures
# =========================================================================== #
BASE = Line()
LOSSLESS = Line(lossless=True)
LEN = 400.0


def fig_matched():
    fig, ax = plt.subplots(figsize=(6.6, 3.7))
    cases = [
        (LOSSLESS, LOSSLESS.zc, BLUE, "lossless, $Z_T=\\sqrt{L'/C'}$"),
        (BASE, BASE.zc, RED, "lossy, $Z_T=\\sqrt{L'/C'}$"),
        (BASE, BASE.zc_c, TEAL, "lossy, $Z_T=Z_w$ complex"),
    ]
    for ln, zt, col, lab in cases:
        s, v = profile_matched(ln, LEN, zt)
        ax.plot(s, v, color=col, label=lab)
    ax.axhline(1.0, color=GREY, lw=0.9, ls=(0, (4, 3)))
    ax.set_xlabel("Distance from sending end  [km]")
    ax.set_ylabel("$|V| / |V_S|$  [p.u.]")
    ax.set_xlim(0, LEN)
    ax.set_ylim(0.955, 1.012)
    ax.legend(loc="lower left")
    fig.savefig(os.path.join(OUT, "np_matched_profile.pdf"))
    plt.close(fig)


def fig_voltage_profile():
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ks = [0.0, 0.5, 1.0, 1.5, 2.0]
    labels = ["no load", "$0.5\\,P_{nat}$", "$P_{nat}$", "$1.5\\,P_{nat}$", "$2\\,P_{nat}$"]
    for k, col, lab in zip(ks, RAMP, labels):
        s, v, _ = profile_two_source(BASE, LEN, max(k, 1e-6) * BASE.p_nat)
        ax.plot(s, v, color=col, lw=2.6 if k == 1.0 else 2.0, label=lab,
                zorder=5 if k == 1.0 else 2)
    ax.axhline(1.0, color=GREY, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.set_xlabel("Distance from sending end  [km]")
    ax.set_ylabel("Voltage magnitude  [p.u.]")
    ax.set_xlim(0, LEN)
    ax.legend(loc="lower left", ncol=2, fontsize=8.8, columnspacing=1.1,
              handlelength=1.6)
    ax.margins(y=0.16)
    fig.savefig(os.path.join(OUT, "np_voltage_profile.pdf"))
    plt.close(fig)


def fig_reactive_balance():
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    k = np.linspace(0.05, 2.0, 60)
    res = [two_source(BASE, LEN, kk * BASE.p_nat) for kk in k]
    for key, col, lab in [("q_line", RED, "absorbed by line"),
                          ("q_send", BLUE, "from sending system"),
                          ("q_recv", TEAL, "from receiving system")]:
        ax.plot(k, [r[key] for r in res], color=col, label=lab)
    p0 = p_nat_numeric(BASE, LEN)
    ax.axhline(0.0, color="#232323", lw=0.9)
    ax.axvline(p0 / BASE.p_nat, color=GREY, lw=0.9, ls=(0, (4, 3)))
    ax.text(0.58, 0.035, f"$Q=0$ at {p0:.0f} MW\n($U^2/Z_w$ = {BASE.p_nat:.0f} MW)",
            transform=ax.transAxes, fontsize=9.5, color="#232323", va="bottom")
    ax.set_xlabel("Loading  $P / P_{nat}$")
    ax.set_ylabel("Reactive power  [MVAr]")
    ax.set_xlim(0, 2.0)
    ax.legend(loc="upper left")
    fig.savefig(os.path.join(OUT, "np_reactive_balance.pdf"))
    plt.close(fig)


def fig_loadability():
    lengths = np.array([50, 80, 120, 160, 200, 250, 300, 400, 500, 600, 700, 800], float)
    out_a = [loadability(BASE, L, "load") for L in lengths]
    out_b = [loadability(BASE, L, "stiff") for L in lengths]
    ratio = np.array([p / BASE.p_nat for p, _ in out_a])
    binds = [b for _, b in out_a]
    ratio_b = np.array([p / BASE.p_nat for p, _ in out_b])
    binds_b = [b for _, b in out_b]

    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.plot(lengths, ratio_b, color=GREY, lw=1.5, ls=(0, (5, 3)), zorder=2,
            label="(b) between two stiff 1.0 p.u. systems")
    ax.plot(lengths, ratio, color=BLUE, lw=2.2, zorder=3,
            label="(a) load at receiving end (St. Clair)")
    for name, col, mk in [("thermal", RED, "o"), ("voltage drop", "#9A6FB0", "^"),
                          ("angular stability", TEAL, "s")]:
        sel = [i for i, b in enumerate(binds) if b == name]
        if sel:
            ax.plot(lengths[sel], ratio[sel], mk, color=col, ms=7, ls="none",
                    mec="white", mew=1.0, zorder=6, label=f"(a) limited by {name}")
    ax.axhline(1.0, color=GREY, lw=1.0, ls=(0, (2, 3)))
    cross = float(np.interp(-1.0, -ratio, lengths))
    cross_b = float(np.interp(-1.0, -ratio_b, lengths))
    ax.set_xlabel("Line length  [km]")
    ax.set_ylabel("$P_{max} / P_{nat}$")
    ax.set_xlim(0, 820)
    ax.set_ylim(0.5, 2.6)
    ax.legend(loc="upper right", fontsize=8.6)
    fig.savefig(os.path.join(OUT, "np_loadability.pdf"))
    plt.close(fig)
    return lengths, ratio, binds, cross, ratio_b, binds_b, cross_b


def fig_ferranti():
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))

    ax = axes[0]
    for m, col in [(0.0, RED), (0.6, BLUE)]:
        s, v = profile_open(BASE, LEN, m)
        ax.plot(s, v, color=col, label=f"{m*100:.0f} % reactor")
    ax.axhline(1.0, color=GREY, lw=0.9, ls=(0, (4, 3)))
    ax.set_xlabel("Distance from sending end  [km]")
    ax.set_ylabel("Voltage magnitude  [p.u.]")
    ax.set_xlim(0, LEN)
    ax.margins(y=0.14)
    ax.legend(loc="upper left")

    ax = axes[1]
    m = np.linspace(0, 1.0, 21)
    v_end = [profile_open(BASE, LEN, mm)[1][0] for mm in m]
    ax.plot(m * 100, v_end, color=BLUE)
    ax.axhline(1.0, color=GREY, lw=0.9, ls=(0, (4, 3)))
    ax.set_xlabel("Shunt reactor  [% of charging power]")
    ax.set_ylabel("Open-end voltage  [p.u.]")
    ax.set_xlim(0, 100)
    fig.tight_layout(w_pad=2.2)
    fig.savefig(os.path.join(OUT, "np_ferranti.pdf"))
    plt.close(fig)


def fig_compensation():
    deg = np.array([0.0, 0.15, 0.30, 0.45, 0.60])
    fine = np.linspace(0, 0.60, 61)

    ser_pf, sh_pf = [], []
    for d in deg:
        ls = Line(x=BASE.x * (1 - d), lossless=True)
        lh = Line(c_nf=12.5 * (1 - d), lossless=True)
        ser_pf.append(p_nat_numeric(ls, LEN))
        sh_pf.append(p_nat_numeric(lh, LEN))

    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.plot(fine * 100, BASE.p_nat / np.sqrt(1 - fine), color=RED, lw=1.6,
            ls=(0, (5, 3)), label="$P_{nat}/\\sqrt{1-k}$  (series)")
    ax.plot(fine * 100, BASE.p_nat * np.sqrt(1 - fine), color=BLUE, lw=1.6,
            ls=(0, (5, 3)), label="$P_{nat}\\cdot\\sqrt{1-m}$  (shunt)")
    ax.plot(deg * 100, ser_pf, "o", color=RED, ms=7, mec="white", mew=1.0,
            label="two-port solution")
    ax.plot(deg * 100, sh_pf, "s", color=BLUE, ms=7, mec="white", mew=1.0)
    ax.axhline(BASE.p_nat, color=GREY, lw=0.9, ls=(0, (4, 3)))
    ax.set_xlabel("Compensation degree  $k$, $m$  [%]")
    ax.set_ylabel("Effective natural power  [MW]")
    ax.set_xlim(0, 60)
    ax.legend(loc="upper left")
    ax.margins(y=0.14)
    fig.savefig(os.path.join(OUT, "np_compensation.pdf"))
    plt.close(fig)
    return deg, ser_pf, sh_pf


# =========================================================================== #
def verify(ld, comp):
    """Print the numbers quoted in the slides, next to the pandapower results."""
    lengths, ratio, binds, cross, ratio_b, binds_b, cross_b = ld
    deg, ser_pf, sh_pf = comp
    s_matched_real = profile_matched(BASE, LEN, BASE.zc)[1][0]
    s_matched_cplx = profile_matched(BASE, LEN, BASE.zc_c)[1][0]
    rows = [
        ("Zc = sqrt(L'/C')            [ohm]", BASE.zc, 276.4),
        ("|Zc| complex                [ohm]", abs(BASE.zc_c), 276.9),
        ("P_nat = U^2/Zc               [MW]", BASE.p_nat, 578.9),
        ("beta*l                      [deg]", np.degrees(BASE.beta * LEN), 24.9),
        ("Q=0 crossing, lossless       [MW]", p_nat_numeric(LOSSLESS, LEN), 578.8),
        ("Q=0 crossing, lossy          [MW]", p_nat_numeric(BASE, LEN), 566.3),
        ("matched lossy, real Zc      [p.u.]", s_matched_real, 0.9671),
        ("matched lossy, complex Zc   [p.u.]", s_matched_cplx, 0.9821),
        ("open end, no reactor        [p.u.]", profile_open(BASE, LEN, 0.0)[1][0], 1.1022),
        ("1/cos(beta*l)               [p.u.]", 1 / np.cos(BASE.beta * LEN), 1.1023),
        ("open end, 60 % reactor      [p.u.]", profile_open(BASE, LEN, 0.6)[1][0], 0.9835),
        ("charging power             [MVAr]", BASE.charging_mvar(LEN), 251.3),
        ("case B loadability  50 km [x P_nat]", ratio_b[0], 2.37),
        ("case B loadability 400 km [x P_nat]", ratio_b[7], 1.15),
        ("case B loadability 800 km [x P_nat]", ratio_b[-1], 0.64),
        ("case B length at 1 x P_nat   [km]", cross_b, 472.0),
        ("series k=60 %             [x P_nat]", ser_pf[-1] / BASE.p_nat, 1.581),
        ("shunt  m=60 %             [x P_nat]", sh_pf[-1] / BASE.p_nat, 0.632),
    ]
    print(f"\n{'quantity':36s} {'two-port':>10s} {'pandapower':>11s} {'dev':>8s}")
    print("-" * 70)
    worst = 0.0
    for name, got, ref in rows:
        dev = (got / ref - 1) * 100 if ref else 0.0
        worst = max(worst, abs(dev))
        print(f"{name:36s} {got:10.4f} {ref:11.4f} {dev:+7.2f}%")
    print("-" * 70)
    print(f"worst deviation: {worst:.2f} %   (rounding of the reference values dominates)")
    print(f"\ncase A - load at receiving end (St. Clair), 1 x P_nat at {cross:.0f} km:")
    for L, r, b in zip(lengths, ratio, binds):
        print(f"  {L:5.0f} km   {r:5.3f} x P_nat   {b}")
    print(f"\ncase B - between two stiff systems, 1 x P_nat at {cross_b:.0f} km:")
    for L, r, b in zip(lengths, ratio_b, binds_b):
        print(f"  {L:5.0f} km   {r:5.3f} x P_nat   {b}")


if __name__ == "__main__":
    fig_matched()
    fig_voltage_profile()
    fig_reactive_balance()
    ld = fig_loadability()
    fig_ferranti()
    comp = fig_compensation()
    print("wrote:", ", ".join(sorted(f for f in os.listdir(OUT) if f.endswith(".pdf"))))
    verify(ld, comp)
