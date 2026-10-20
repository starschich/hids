#!/usr/bin/env python3
"""
Figures for design/ac-transmission/angular-stability.tex  (as_*.pdf).

Steady-state angular stability of the 500 kV reference line (same
constants as transmission_limits_figures.py / series_compensation_figures.py):
  as_power_angle.pdf       P(delta) and the synchronising power coefficient
  as_electrical_length.pdf P_max vs length: exact, distributed, lumped
  as_contingency.pdf       two parallel circuits, intact and after N-1
  as_equal_area.pdf        equal-area criterion (generic machine p.u.)
numpy + matplotlib only (no scipy).  Run from this directory.
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
beta = np.imag(gamma)                       # rad/m
lam_km = 2*np.pi/beta/1e3                   # wavelength
quarter_mi = (np.pi/2)/beta/1e3/MI_TO_KM    # quarter-wave length


def abcd_line(length_m):
    gl = gamma*length_m
    return np.array([[np.cosh(gl), Z_c*np.sinh(gl)],
                     [np.sinh(gl)/Z_c, np.cosh(gl)]])


def abcd_parallel(M, n):
    """n identical two-ports in parallel."""
    A, B, C, D = M.ravel()
    return np.array([[A, B/n], [n*C, D]])


def P_receiving(M, Us, Ur, delta_deg):
    A, B, C, D = M.ravel()
    d = np.radians(delta_deg); aA, bB = np.angle(A), np.angle(B)
    return Us*Ur/abs(B)*np.cos(bB - d) - abs(A)*Ur**2/abs(B)*np.cos(bB - aA)


def delta_for(M, P_target, Us=U_n, Ur=U_n):
    """Smallest delta giving P_target, by scan + refinement (no scipy)."""
    d = np.linspace(0, 120, 24001)
    P = P_receiving(M, Us, Ur, d)
    i = np.argmax(P >= P_target)
    return np.nan if P[i] < P_target else d[i]


# ---- Figure 1: power-angle relation and synchronising power -----------
M300 = abcd_line(L_ref_mi*MI_TO_KM*1e3)
d = np.linspace(0, 90, 2001)
P = P_receiving(M300, U_n, U_n, d)/P_nat
Ks = np.gradient(P, d)                      # d(P/P_nat)/d(delta), per degree
d_pmax = d[np.argmax(P)]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.4, 4.6), sharex=True,
                               gridspec_kw={"height_ratios": [2.0, 1.0]})
ax1.plot(d, P, color=RED, lw=2.0)
ax1.axvline(30, color=GREEN, ls="--", lw=1.2)
ax1.axvline(d_pmax, color=GRAY, ls=":", lw=1.2)
ax1.plot([30], [np.interp(30, d, P)], "o", color=GREEN, ms=5)
ax1.annotate(r"$\delta = 30^\circ$", xy=(30, np.interp(30, d, P)),
             xytext=(33, 0.55), color=GREEN, fontsize=10)
ax1.annotate(r"$P_{max}$", xy=(d_pmax, P.max()), xytext=(d_pmax-20, P.max()+0.06),
             color=GRAY, fontsize=10)
ax1.set_ylabel(r"$P$  [$P_{nat}$]"); ax1.set_ylim(0, P.max()*1.18)
ax2.plot(d, Ks, color=BLUE, lw=2.0)
ax2.axhline(0, color=GRAY, lw=0.8)
ax2.axvline(30, color=GREEN, ls="--", lw=1.2)
ax2.axvline(d_pmax, color=GRAY, ls=":", lw=1.2)
ax2.set_ylabel(r"$K_s$  [$P_{nat}/^\circ$]")
ax2.set_xlabel(r"Transmission angle  $\delta$  [$^\circ$]")
ax2.set_xlim(0, 90)
fig.tight_layout(pad=0.4)
fig.savefig("as_power_angle.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

# ---- Figure 2: P_max against electrical length ------------------------
L_mi = np.linspace(10, 800, 400)
P_exact, P_dist, P_lump = [], [], []
for Lm in L_mi*MI_TO_KM*1e3:
    M = abcd_line(Lm)
    dd = np.linspace(0, 150, 6001)
    P_exact.append(P_receiving(M, U_n, U_n, dd).max()/P_nat)
    bl = beta*Lm
    P_dist.append(1.0/np.sin(bl))
    P_lump.append(1.0/bl)
P_exact, P_dist, P_lump = map(np.array, (P_exact, P_dist, P_lump))

fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.plot(L_mi, P_lump, color=GRAY, ls="--", lw=1.6, label=r"lumped  $1/\beta l$")
ax.plot(L_mi, P_dist, color=BLUE, lw=1.8, label=r"lossless  $1/\sin\beta l$")
ax.plot(L_mi, P_exact, color=RED, lw=2.2, label="exact two-port")
ax.axhline(1.0, color=GREEN, ls=":", lw=1.2)
ax.axvline(L_ref_mi, color=GRAY, ls=":", lw=1.0)
ax.annotate(r"$\beta l = 90^\circ$", xy=(quarter_mi, 1.0), xytext=(quarter_mi-150, 1.5),
            color=GREEN, fontsize=10,
            arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.0))
ax.set_xlim(0, 800); ax.set_ylim(0, 6)
ax.set_xlabel("Line length  [mi]"); ax.set_ylabel(r"$P_{max}$  [$P_{nat}$]")
ax.legend(loc="upper right")
fig.savefig("as_electrical_length.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

# ---- Figure 3: intact and post-contingency ----------------------------
M1 = abcd_line(L_ref_mi*MI_TO_KM*1e3)
M2 = abcd_parallel(M1, 2)
d = np.linspace(0, 90, 2001)
P2 = P_receiving(M2, U_n, U_n, d)/1e6
P1 = P_receiving(M1, U_n, U_n, d)/1e6
P1max, P2max = P1.max(), P2.max()
P_op, P_crit = 1200.0, 0.70*P1max
d_op, d_crit = delta_for(M2, P_op*1e6), delta_for(M2, P_crit*1e6)

fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.plot(d, P2, color=BLUE, lw=2.2, label="intact, 2 circuits")
ax.plot(d, P1, color=RED, lw=2.2, label="after N$-$1, 1 circuit")
ax.axhline(P1max, color=RED, ls=":", lw=1.0)
ax.axhline(P_crit, color=GREEN, ls="--", lw=1.4)
ax.plot([d_op], [P_op], "o", color=GRAY, ms=6)
ax.plot([d_crit], [P_crit], "o", color=GREEN, ms=6)
ax.text(2, P1max+70, f"{P1max:.0f} MW $= P_{{max}}$ after N$-$1", color=RED, fontsize=10)
ax.text(d_op+3, P_op+45, f"{P_op:.0f} MW", color=GRAY, fontsize=10)
ax.text(d_crit+3, P_crit-200, f"{P_crit:.0f} MW  (30% margin)", color=GREEN, fontsize=10)
ax.set_xlim(0, 90); ax.set_ylim(0, P2max*1.1)
ax.set_xlabel(r"Transmission angle  $\delta$  [$^\circ$]")
ax.set_ylabel(r"$P$  [MW]")
ax.legend(loc="lower right")
fig.savefig("as_contingency.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

# ---- Figure 4: equal-area criterion (generic machine p.u.) ------------
Pm, Pa, Pb, Pc = 0.60, 1.00, 0.30, 0.70       # pre-fault, during, post-fault
d0 = np.arcsin(Pm/Pa)
dmax = np.pi - np.arcsin(Pm/Pc)
cos_dcc = (Pm*(dmax - d0) + Pc*np.cos(dmax) - Pb*np.cos(d0))/(Pc - Pb)
dcc = np.arccos(cos_dcc)
dd = np.linspace(0, np.pi, 1001)

fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.plot(np.degrees(dd), Pa*np.sin(dd), color=GRAY, lw=1.6, label="pre-fault")
ax.plot(np.degrees(dd), Pb*np.sin(dd), color=ORANGE, lw=2.0, label="during fault")
ax.plot(np.degrees(dd), Pc*np.sin(dd), color=BLUE, lw=2.0, label="post-fault")
ax.axhline(Pm, color=RED, lw=1.6)
s1 = np.linspace(d0, dcc, 200)
s2 = np.linspace(dcc, dmax, 200)
ax.fill_between(np.degrees(s1), Pb*np.sin(s1), Pm, color=ORANGE, alpha=0.25)
ax.fill_between(np.degrees(s2), Pm, Pc*np.sin(s2), color=BLUE, alpha=0.25)
ax.annotate(r"$A_{acc}$", xy=(np.degrees((d0+dcc)/2), 0.42), xytext=(11, 0.50),
            color=ORANGE, fontsize=11,
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.0))
ax.text(np.degrees((dcc+dmax)/2)-6, Pm+0.035, r"$A_{dec}$", color=BLUE, fontsize=11)
for x, lab, col, dx in [(d0, r"$\delta_0$", GRAY, -7.0),
                        (dcc, r"$\delta_{cc}$", GREEN, 1.5),
                        (dmax, r"$\delta_{max}$", GRAY, 1.5)]:
    ax.axvline(np.degrees(x), color=col, ls="--", lw=1.0)
    ax.text(np.degrees(x)+dx, 0.03, lab, color=col, fontsize=10)
ax.text(2, Pm+0.03, r"$P_m$", color=RED, fontsize=10)
ax.set_xlim(0, 180); ax.set_ylim(0, 1.12)
ax.set_xlabel(r"Rotor angle  $\delta$  [$^\circ$]")
ax.set_ylabel(r"$P$  [p.u.]")
ax.legend(loc="upper right")
fig.savefig("as_equal_area.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

# ---- numbers for the slides -------------------------------------------
print(f"Z_c = {np.real(Z_c):.1f} ohm, P_nat = {P_nat/1e6:.0f} MW")
print(f"beta = {beta*1e3:.4e} rad/km, lambda = {lam_km:.0f} km, "
      f"quarter wave = {quarter_mi:.0f} mi ({quarter_mi*MI_TO_KM:.0f} km)")
bl = beta*L_ref_mi*MI_TO_KM*1e3
print(f"300 mi: beta*l = {np.degrees(bl):.1f} deg, 1/sin = {1/np.sin(bl):.2f}, "
      f"1/(beta l) = {1/bl:.2f}, exact P_max = {P1max:.0f} MW "
      f"({P1max*1e6/P_nat:.2f} P_nat) at delta = {d[np.argmax(P1)]:.1f} deg")
print(f"X_lumped(300 mi) = {omega*L_per_m*L_ref_mi*MI_TO_KM*1e3:.1f} ohm, "
      f"X_dist = {np.real(Z_c)*np.sin(bl):.1f} ohm")
print(f"two circuits: P_max = {P2max:.0f} MW, N-1 P_max = {P1max:.0f} MW, "
      f"30% margin -> {P_crit:.0f} MW ({P_crit*1e6/P_nat:.2f} P_nat) "
      f"at delta = {d_crit:.1f} deg; 1200 MW sits at delta = {d_op:.1f} deg")
print(f"equal area: d0 = {np.degrees(d0):.1f}, dcc = {np.degrees(dcc):.1f}, "
      f"dmax = {np.degrees(dmax):.1f} deg")

# ---- extra numbers quoted on the slides --------------------------------
dd = np.linspace(0, 90, 9001)
PP = P_receiving(M300, U_n, U_n, dd)/P_nat
KK = np.gradient(PP, dd)
print(f"at delta = 30 deg: P = {np.interp(30, dd, PP):.2f} P_nat, "
      f"K_s/K_s(0) = {np.interp(30, dd, KK)/KK[0]:.2f}")
X_line = np.real(Z_c)*np.sin(beta*L_ref_mi*MI_TO_KM*1e3)
print("source strength at both ends (lossless U^2/X_tot, X_line = "
      f"{X_line:.1f} ohm):")
for S_sc in [5e9, 10e9, 20e9, np.inf]:
    X_th = U_n**2/S_sc if np.isfinite(S_sc) else 0.0
    X_tot = X_line + 2*X_th
    print(f"  SCL {S_sc/1e9:>5} GVA: X_th = {X_th:5.1f} ohm, X_tot = {X_tot:6.1f} ohm, "
          f"P_max = {U_n**2/X_tot/1e6:6.0f} MW ({X_line/X_tot:.2f} of line-only)")
P_th_pair = 2*np.sqrt(3)*U_n*3*1300.0
print(f"thermal rating of the pair = {P_th_pair/1e6:.0f} MW "
      f"= {P_th_pair/1e6/954.0:.1f} x the N-1 stability limit")
