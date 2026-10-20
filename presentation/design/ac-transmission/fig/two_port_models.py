#!/usr/bin/env python3
"""
Figure for documentation/design/sections/06-reference-line.tex (tp_*.pdf).
Kept here with the other ac-transmission figure scripts; no slide uses it
yet, but wave-representation.tex is where it would go.

How far the lumped models depart from the exact two-port of the
500 kV reference line, and how cascading shorter sections closes the
gap (same line constants as angular_stability_figures.py):
  tp_model_error.pdf  (a) deviation of |A|, |B|, |C| and P_max of the
                          single nominal pi against line length
                      (b) deviation of |B| for n cascaded nominal pi
                          sections, n = 1, 2, 4, 8
numpy + matplotlib only (no scipy).  Run from this directory.
Prints every value quoted in the report tables.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 11, "axes.labelsize": 11,
    "legend.fontsize": 10, "axes.grid": True, "grid.color": "#d9d9d9",
    "grid.linewidth": 0.8, "axes.edgecolor": "#8a8a8a", "axes.linewidth": 0.8,
    "legend.framealpha": 1.0, "legend.edgecolor": "#c9c7c2", "pdf.fonttype": 42,
})
RED, BLUE, GREEN, ORANGE, GRAY = "#c0392b", "#1f77b4", "#2e8b57", "#e08a1e", "#5c5c5c"

MI_TO_KM, FT_TO_M, IN_TO_M = 1.609344, 0.3048, 0.0254
U_n, f = 500e3, 60.0
omega = 2*np.pi*f

# ---- line constants ---------------------------------------------------
# The published per-unit-length values of the reference line, so that the
# tables below reproduce exactly from the parameters the report quotes.
# angular_stability_figures.py derives the same constants from the tower
# geometry instead; that shifts every result here by less than 0.2 %.
R_per_m, X_per_m, C_per_m = 56.9e-6, 0.336e-3, 12.7e-12     # Ohm/m, Ohm/m, F/m
L_per_m = X_per_m/omega
z, y = R_per_m + 1j*X_per_m, 1j*omega*C_per_m
gamma, Z_w = np.sqrt(z*y), np.sqrt(z/y)
beta = np.imag(gamma)


def exact(l_m):
    """Exact (distributed) A, B, C of a line of length l_m."""
    gl = gamma*l_m
    return np.cosh(gl), Z_w*np.sinh(gl), np.sinh(gl)/Z_w


def nominal_pi(l_m):
    """A, B, C of one nominal pi covering the whole length."""
    Z, Y = z*l_m, y*l_m
    return 1 + Z*Y/2, Z, Y*(1 + Z*Y/4)


def cascade(l_m, n):
    """n nominal pi sections of length l_m/n in cascade."""
    Z, Y = z*(l_m/n), y*(l_m/n)
    T = np.array([[1 + Z*Y/2, Z], [Y*(1 + Z*Y/4), 1 + Z*Y/2]])
    M = np.linalg.matrix_power(T, n)
    return M[0, 0], M[0, 1], M[1, 0]


def equivalent_pi(l_m):
    """The exact two-port rendered as one pi (long-line correction)."""
    gl = gamma*l_m
    return Z_w*np.sinh(gl), np.tanh(gl/2)/Z_w          # Z_eq, Y_eq/2


def p_max(A, B, U=U_n):
    """Crest of the power-angle curve, both terminals at U."""
    return (U*U/abs(B) - abs(A)*U*U*np.cos(np.angle(B)-np.angle(A))/abs(B))/1e6


dev = lambda approx, ref: 100*(abs(approx)-abs(ref))/abs(ref)
LENGTHS = (100, 200, 300, 400, 600)

# ---------------- printed values --------------------------------------
print("line: R' = %.1f mOhm/km  X' = %.3f Ohm/km  C' = %.1f nF/km"
      % (R_per_m*1e6, X_per_m*1e3, C_per_m*1e12))
print("      Z_w = %.1f %+.1fj Ohm   beta = %.3e rad/km\n"
      % (Z_w.real, Z_w.imag, beta*1e3))

print("Table: nominal pi against exact, absolute values")
print(" l/mi  beta*l   |A|pi   |A|ex    |B|pi    |B|ex   |C|pi  |C|ex")
for lmi in LENGTHS:
    l = lmi*MI_TO_KM*1e3
    Ap, Bp, Cp = nominal_pi(l); Ae, Be, Ce = exact(l)
    print("%5d %7.1f  %6.3f  %6.3f  %7.1f  %7.1f  %5.3f  %5.3f"
          % (lmi, np.degrees(beta*l), abs(Ap), abs(Ae),
             abs(Bp), abs(Be), abs(Cp)*1e3, abs(Ce)*1e3))

print("\nTable: deviation of the nominal pi, per cent")
print(" l/mi    |A|     |B|     |C|   P_max      P_pi   P_exact")
for lmi in LENGTHS:
    l = lmi*MI_TO_KM*1e3
    Ap, Bp, Cp = nominal_pi(l); Ae, Be, Ce = exact(l)
    pp, pe = p_max(Ap, Bp), p_max(Ae, Be)
    print("%5d  %+6.1f  %+6.1f  %+6.1f  %+6.1f    %6.0f    %6.0f"
          % (lmi, dev(Ap, Ae), dev(Bp, Be), dev(Cp, Ce),
             100*(pp-pe)/pe, pp, pe))

print("\nTable: n sections in cascade, deviation of |B| per cent")
print("   n  section/mi " + "".join("%8d" % l for l in LENGTHS))
for n in (1, 2, 4, 8, 16):
    row = []
    for lmi in LENGTHS:
        _, B, _ = cascade(lmi*MI_TO_KM*1e3, n)
        _, Be, _ = exact(lmi*MI_TO_KM*1e3)
        row.append(dev(B, Be))
    print("%4d  %8s   " % (n, "l/%d" % n) + "".join("%+8.2f" % v for v in row))

print("\nTable: n sections at 600 mi, |A| and |B| deviation")
for n in (1, 2, 4, 8, 16):
    l = 600*MI_TO_KM*1e3
    A, B, C = cascade(l, n); Ae, Be, Ce = exact(l)
    print("  n=%2d  section %3.0f mi  |A| %+6.2f %%  |B| %+6.2f %%"
          % (n, 600/n, dev(A, Ae), dev(B, Be)))

print("\nEquivalent pi (exact, as one section)")
for lmi in (300, 600):
    l = lmi*MI_TO_KM*1e3
    Zeq, Yeq2 = equivalent_pi(l)
    Zn, Yn2 = z*l, y*l/2
    print("  %3d mi  Z_eq = %5.1f %+6.1fj Ohm  (nominal %5.1f %+6.1fj)   "
          "Y_eq/2 = %.4f mS  (nominal %.4f mS)"
          % (lmi, Zeq.real, Zeq.imag, Zn.real, Zn.imag,
             abs(Yeq2)*1e3, abs(Yn2)*1e3))

# ---------------- figure ----------------------------------------------
L = np.linspace(20, 650, 400)*MI_TO_KM*1e3
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.1))

Ap, Bp, Cp = nominal_pi(L); Ae, Be, Ce = exact(L)
Pp = np.array([p_max(a, b) for a, b in zip(Ap, Bp)])
Pe = np.array([p_max(a, b) for a, b in zip(Ae, Be)])
ax1.plot(L/1e3/MI_TO_KM, dev(Bp, Be), color=RED,    label=r"$|B|$")
ax1.plot(L/1e3/MI_TO_KM, dev(Cp, Ce), color=BLUE,   label=r"$|C|$")
ax1.plot(L/1e3/MI_TO_KM, dev(Ap, Ae), color=GREEN,  label=r"$|A| = |D|$")
ax1.plot(L/1e3/MI_TO_KM, 100*(Pp-Pe)/Pe, color=ORANGE, ls="--", label=r"$P_{max}$")
ax1.axhline(0, color=GRAY, lw=0.8)
ax1.axvline(300, color=GRAY, lw=0.8, ls=":")
ax1.annotate("reference line\n300 mi", xy=(300, -28), xytext=(316, -28),
             fontsize=9, color=GRAY, va="center")
ax1.set_xlabel("line length (mi)"); ax1.set_ylabel("deviation from exact (%)")
ax1.set_title("(a) one nominal $\\pi$ for the whole line")
ax1.set_xlim(0, 650); ax1.set_ylim(-34, 40); ax1.legend(loc="upper left")

for n, col, ls in ((1, RED, "-"), (2, ORANGE, "-"), (4, BLUE, "-"), (8, GREEN, "-")):
    e = np.array([dev(cascade(l, n)[1], exact(l)[1]) for l in L])
    ax2.semilogy(L/1e3/MI_TO_KM, e, color=col, ls=ls,
                 label=r"$n = %d$" % n)
ax2.axhline(1.0, color=GRAY, lw=0.8, ls="--")
ax2.annotate("1 %", xy=(30, 1.15), fontsize=9, color=GRAY)
ax2.axvline(300, color=GRAY, lw=0.8, ls=":")
ax2.set_xlabel("line length (mi)")
ax2.set_ylabel(r"deviation of $|B|$ from exact (%)")
ax2.set_title("(b) $n$ nominal $\\pi$ sections in cascade")
ax2.set_xlim(0, 650); ax2.set_ylim(1e-3, 1e2); ax2.legend(loc="lower right")

fig.tight_layout()
fig.savefig("tp_model_error.pdf")
print("\nwrote tp_model_error.pdf")
