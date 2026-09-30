#!/usr/bin/env python3
"""
Figures for design/ac-transmission/transmission-limits.tex  (tl_*.pdf).

Loadability of the 500 kV reference line (same constants as
series_compensation_figures.py) versus length, from the exact two-port
equations, against the three classical limits:
  thermal    : conductor rating, P_th = sqrt(3) U_n I_th (flat)
  voltage    : U_S = 1.0 p.u., unity-pf load at the receiving end, U_R >= 0.95 p.u.
  stability  : both terminals at 1.0 p.u., transmission angle delta <= 30 deg
Series compensation is a midpoint bank with degree k.
numpy + matplotlib only.  Run from this directory.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import brentq

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
L_ref_mi = 300.0

# ---- line constants (identical to series_compensation_figures.py) -----
r_ac_75_per_kft, d_cond_in, GMR_cond_ft = 0.0520, 1.762, 0.0588
n_sub, s_bundle, D_ph = 3, 18*IN_TO_M, 35*FT_TO_M
r_cond, GMR_cond = d_cond_in*IN_TO_M/2, GMR_cond_ft*FT_TO_M
GMR_b = (GMR_cond*s_bundle**2)**(1/3); r_b = (r_cond*s_bundle**2)**(1/3)
GMD = (D_ph*D_ph*2*D_ph)**(1/3)
mu0, eps0 = 4e-7*np.pi, 8.854e-12
R_per_m = r_ac_75_per_kft/(1000*FT_TO_M)/n_sub
L_per_m = mu0/(2*np.pi)*np.log(GMD/GMR_b)
C_per_m = 2*np.pi*eps0/np.log(GMD/r_b)
z, y = R_per_m + 1j*omega*L_per_m, 1j*omega*C_per_m
gamma, Z_c = np.sqrt(z*y), np.sqrt(z/y)
P_nat = U_n**2/np.real(Z_c)

I_th = 3*1300.0                   # A, 3 x Bluebird at 75 C (approx. ampacity)
P_th = np.sqrt(3)*U_n*I_th        # thermal limit at 1.0 p.u.
U_R_min, delta_max = 0.95, 30.0

def abcd_line(length_m):
    gl = gamma*length_m
    return np.array([[np.cosh(gl), Z_c*np.sinh(gl)], [np.sinh(gl)/Z_c, np.cosh(gl)]])

def abcd_series(Z):
    return np.array([[1, Z], [0, 1]], dtype=complex)

def abcd(length_m, k):
    if k == 0:
        return abcd_line(length_m)
    X_L = omega*L_per_m*length_m
    return abcd_line(length_m/2) @ abcd_series(-1j*k*X_L) @ abcd_line(length_m/2)

def P_receiving(M, Us, Ur, delta_deg):
    A, B, C, D = M.ravel()
    d = np.radians(delta_deg); aA, bB = np.angle(A), np.angle(B)
    return Us*Ur/abs(B)*np.cos(bB - d) - abs(A)*Ur**2/abs(B)*np.cos(bB - aA)

def sending_current(M, Us, Ur, delta_deg):
    """|I_S| for U_S = Us e^{j delta}, U_R = Ur (line-line magnitudes)."""
    A, B, C, D = M.ravel()
    Usph = Us/np.sqrt(3)*np.exp(1j*np.radians(delta_deg)); Urph = Ur/np.sqrt(3)
    Ir = (Usph - A*Urph)/B
    Is = C*Urph + D*Ir
    return abs(Is)

def limit_stability(M):
    return P_receiving(M, U_n, U_n, delta_max)

def limit_thermal(M):
    # thermal rating of the conductor at nominal voltage; independent of length
    return P_th

def limit_voltage(M):
    # U_S = 1.0 p.u., unity-pf load at R; find P with |U_R| = 0.95 p.u.
    A, B, C, D = M.ravel()
    Ur = U_R_min*U_n/np.sqrt(3)
    def g(P):
        Ir = P/(3*Ur)                     # unity pf, in phase with U_R
        Us = A*Ur + B*Ir
        return abs(Us) - U_n/np.sqrt(3)
    lo, hi = 0.0, 5*P_th
    if g(lo) > 0:                          # Ferranti: 0.95 at R impossible with no load
        return np.nan
    return brentq(g, lo, hi)

lengths_mi = np.linspace(25, 600, 116)
def curves(k):
    th, vo, st = [], [], []
    for Lmi in lengths_mi:
        M = abcd(Lmi*MI_TO_KM*1e3, k)
        th.append(limit_thermal(M)); vo.append(limit_voltage(M)); st.append(limit_stability(M))
    return np.array(th), np.array(vo), np.array(st)

def save(fig, name):
    fig.tight_layout(pad=0.4); fig.savefig(name, format="pdf"); plt.close(fig); print("wrote", name)

# ---- Figure 1: the three limits, uncompensated -------------------------
th0, vo0, st0 = curves(0.0)
load_a = np.nanmin(np.vstack([th0, vo0, st0]), axis=0)     # (a) load at receiving end
load_b = np.minimum(th0, st0)                               # (b) two stiff systems
fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.plot(lengths_mi, th0/P_nat, color=ORANGE, lw=1.6, ls="--", label="thermal, $P_{th}$")
ax.plot(lengths_mi, vo0/P_nat, color=BLUE, lw=1.6, ls="--", label="voltage drop, $U_R \\geq 0.95$ p.u.")
ax.plot(lengths_mi, st0/P_nat, color=GREEN, lw=1.6, ls="--", label="stability, $\\delta \\leq 30^\\circ$")
ax.plot(lengths_mi, load_a/P_nat, color=RED, lw=2.6, label="loadability (a): load at R")
ax.plot(lengths_mi, load_b/P_nat, color=GRAY, lw=2.0, label="loadability (b): stiff systems")
ax.axvline(L_ref_mi, color=GRAY, ls=":", lw=1.0); ax.text(L_ref_mi+5, 0.12, "300 mi", color=GRAY, fontsize=10)
ax.set_xlim(0, 600); ax.set_ylim(0, 5.4)
ax.set_xlabel("Line length  [mi]"); ax.set_ylabel("Transfer limit  [$P_{nat}$]")
ax.legend(loc="upper right")
save(fig, "tl_loadability.pdf")

# ---- Figure 2: loadability (b) with series compensation ----------------
fig, ax = plt.subplots(figsize=(6.4, 4.0))
res = {}
for k, c in [(0.0, GRAY), (0.3, BLUE), (0.5, RED), (0.7, GREEN)]:
    th, vo, st = curves(k)
    res[k] = (th, vo, st, np.minimum(th, st), np.nanmin(np.vstack([th, vo, st]), axis=0))
    ax.plot(lengths_mi, res[k][3]/P_nat, color=c, lw=2.0, label=f"$k = {k:.1f}$")
ax.axvline(L_ref_mi, color=GRAY, ls=":", lw=1.0)
ax.set_xlim(0, 600); ax.set_ylim(0, 4.4)
ax.set_xlabel("Line length  [mi]"); ax.set_ylabel("Loadability (b)  [$P_{nat}$]")
ax.legend(loc="upper right")
save(fig, "tl_loadability_k.pdf")

# ---- numbers for the slides --------------------------------------------
print(f"P_nat = {P_nat/1e6:.0f} MW, P_th = {P_th/1e6:.0f} MW ({P_th/P_nat:.2f} P_nat), I_th = {I_th:.0f} A")
i = np.argmin(abs(lengths_mi - L_ref_mi))
for k, (th, vo, st, lb, la) in res.items():
    print(f"k={k:.1f} @300 mi: voltage {vo[i]/1e6:.0f}  stability {st[i]/1e6:.0f}  "
          f"-> (a) {la[i]/1e6:.0f} MW ({la[i]/P_nat:.2f})  (b) {lb[i]/1e6:.0f} MW ({lb[i]/P_nat:.2f})")
    tb = lengths_mi[np.isclose(lb, th, rtol=1e-3)]
    print(f"      (b) thermal binding up to {tb.max() if tb.size else 0:.0f} mi; "
          f"(b) below 1 P_nat from {lengths_mi[lb < P_nat].min():.0f} mi; "
          f"(a) below 1 P_nat from {lengths_mi[la < P_nat].min():.0f} mi")
