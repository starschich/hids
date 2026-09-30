#!/usr/bin/env python3
"""
Figures for design/ac-transmission/series-compensation.tex  (sc_*.pdf).

Exact two-port (ABCD) model of a uniform line, midpoint series capacitor
inserted as a cascaded series element. numpy + matplotlib only; same model
as the notebook ac_ohl_series_compensation.ipynb.

Reference line: 500 kV, 60 Hz, 300 mi (482.8 km), flat configuration,
3 x Bluebird ACSR 2156 kcmil per phase, 18 in bundle spacing, 35 ft phase
spacing, R at 75 C.  Run from this directory:  python3 series_compensation_figures.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- plot style, matches np_*.pdf -------------------------------------
plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 11, "axes.labelsize": 11,
    "legend.fontsize": 10, "axes.grid": True, "grid.color": "#d9d9d9",
    "grid.linewidth": 0.8, "axes.edgecolor": "#8a8a8a", "axes.linewidth": 0.8,
    "legend.framealpha": 1.0, "legend.edgecolor": "#c9c7c2",
    "pdf.fonttype": 42,
})
RED, BLUE, GREEN, ORANGE, GRAY = "#c0392b", "#1f77b4", "#2e8b57", "#e08a1e", "#5c5c5c"
K_COLORS = {0.0: GRAY, 0.3: BLUE, 0.5: RED, 0.7: GREEN}

MI_TO_KM, FT_TO_M, IN_TO_M = 1.609344, 0.3048, 0.0254

# ---- system and line ----------------------------------------------------
U_n, f = 500e3, 60.0
omega = 2*np.pi*f
L_mi = 300.0
L_m = L_mi*MI_TO_KM*1e3

r_ac_75_per_kft, d_cond_in, GMR_cond_ft = 0.0520, 1.762, 0.0588   # Bluebird, Southwire 11-4
n_sub, s_bundle, D_ph = 3, 18*IN_TO_M, 35*FT_TO_M

r_cond, GMR_cond = d_cond_in*IN_TO_M/2, GMR_cond_ft*FT_TO_M
GMR_b = (GMR_cond*s_bundle**2)**(1/3)
r_b   = (r_cond*s_bundle**2)**(1/3)
GMD   = (D_ph*D_ph*2*D_ph)**(1/3)
mu0, eps0 = 4e-7*np.pi, 8.854e-12

R_per_m = r_ac_75_per_kft/(1000*FT_TO_M)/n_sub
L_per_m = mu0/(2*np.pi)*np.log(GMD/GMR_b)
C_per_m = 2*np.pi*eps0/np.log(GMD/r_b)

z, y = R_per_m + 1j*omega*L_per_m, 1j*omega*C_per_m
gamma, Z_c = np.sqrt(z*y), np.sqrt(z/y)
X_L_total = omega*L_per_m*L_m
SIL = U_n**2/np.real(Z_c)

def abcd_line(length_m):
    gl = gamma*length_m
    return np.array([[np.cosh(gl), Z_c*np.sinh(gl)], [np.sinh(gl)/Z_c, np.cosh(gl)]])

def abcd_series(Z):
    return np.array([[1, Z], [0, 1]], dtype=complex)

def abcd_comp(k, position=0.5):
    return abcd_line(position*L_m) @ abcd_series(-1j*k*X_L_total) @ abcd_line((1-position)*L_m)

def power_transfer(M, Us, Ur, delta_deg):
    A, B, C, D = M.ravel()
    d = np.radians(delta_deg); aA, bB = np.angle(A), np.angle(B)
    Pr = Us*Ur/abs(B)*np.cos(bB - d) - abs(A)*Ur**2/abs(B)*np.cos(bB - aA)
    return Pr

def voltage_profile(k, P_load, pf=0.95, npts=241, position=0.5):
    U_r = U_n/np.sqrt(3)
    S = P_load/pf*np.exp(1j*np.arccos(pf))
    I_r = np.conj(S/(3*U_r))
    x = np.linspace(0, 1, npts)                     # from receiving end
    U = np.empty(npts, dtype=complex)
    for i, xi in enumerate(x):
        if xi > 1-position:
            M = abcd_line((xi-(1-position))*L_m) @ abcd_series(-1j*k*X_L_total) @ abcd_line((1-position)*L_m)
        else:
            M = abcd_line(xi*L_m)
        U[i] = M[0, 0]*U_r + M[0, 1]*I_r
    return x, np.abs(U)/U_r

def save(fig, name):
    fig.tight_layout(pad=0.4)
    fig.savefig(name, format="pdf")
    plt.close(fig)
    print("wrote", name)

# ---- numbers for the slides ---------------------------------------------
print(f"R' = {R_per_m*1e3:.4f} Ohm/km  X' = {omega*L_per_m*1e3:.4f} Ohm/km  "
      f"C' = {C_per_m*1e12:.2f} nF/km  B' = {omega*C_per_m*1e9:.3f} uS/km")
print(f"X_L = {X_L_total:.1f} Ohm  R = {R_per_m*L_m:.1f} Ohm  Z_c = {Z_c:.1f}  SIL = {SIL/1e6:.0f} MW  "
      f"beta*l = {np.degrees(np.imag(gamma)*L_m):.1f} deg")
delta = np.linspace(0, 90, 901)
for k in K_COLORS:
    P = power_transfer(abcd_comp(k), U_n, U_n, delta)
    i = P.argmax()
    d1500 = np.interp(1500e6, P[:i], delta[:i]) if P.max() > 1500e6 else float("nan")
    print(f"k={k:.1f}: X_C={k*X_L_total:6.1f} Ohm  Pmax={P.max()/1e6:6.0f} MW at {delta[i]:.0f} deg  "
          f"P(30deg)={np.interp(30, delta, P)/1e6:5.0f} MW  delta(1500 MW)={d1500:5.1f} deg  "
          f"Pmax lossless U^2/((1-k)X_L)={U_n**2/((1-k)*X_L_total)/1e6:.0f} MW")

# ---- Figure 1: power-angle curves ----------------------------------------
fig, ax = plt.subplots(figsize=(6.4, 4.0))
for k, c in K_COLORS.items():
    P = power_transfer(abcd_comp(k), U_n, U_n, delta)/1e6
    ax.plot(delta, P, color=c, lw=2.0, label=f"$k = {k:.1f}$")
ax.axhline(SIL/1e6, color=GRAY, ls="--", lw=1.0)
ax.text(1, SIL/1e6 + 30, "$P_{nat}$", color=GRAY, fontsize=10)
ax.axhline(1500, color=GRAY, ls=":", lw=1.0)
ax.text(1, 1530, "1500 MW", color=GRAY, fontsize=10)
ax.set_xlim(0, 90); ax.set_ylim(0, 2600)
ax.set_xlabel(r"Transmission angle $\delta$  [$^\circ$]")
ax.set_ylabel(r"Receiving-end power $P_R$  [MW]")
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.98))
save(fig, "sc_power_angle.pdf")

# ---- Figure 2: voltage profile -------------------------------------------
P_load = 900e6
fig, ax = plt.subplots(figsize=(6.4, 4.0))
for k, c in K_COLORS.items():
    x, u = voltage_profile(k, P_load)
    ax.plot((1-x)*L_mi, u, color=c, lw=2.0, label=f"$k = {k:.1f}$")
ax.axvline(L_mi/2, color=GRAY, ls=":", lw=1.0)
ax.text(L_mi/2 + 3, 1.005, "series bank", color=GRAY, fontsize=10)
ax.set_xlim(0, L_mi); ax.set_ylim(0.98, 1.24)
ax.set_xlabel("Distance from sending end  [mi]")
ax.set_ylabel(r"$|U|$  [p.u.]")
ax.legend(loc="upper right")
save(fig, "sc_voltage_profile.pdf")
for k in K_COLORS:
    x, u = voltage_profile(k, P_load)
    m = len(u)//2
    print(f"profile k={k:.1f}: U_S = {u[-1]:.3f} p.u.  rise across bank = {u[m-1]-u[m+1]:+.3f} p.u.")

# ---- Figure 3: SSR screening ---------------------------------------------
X_source = 0.15*U_n**2/1500e6
k_grid = np.linspace(0.1, 0.8, 141)
k_eff = k_grid*X_L_total/(X_L_total + X_source)
f_er = f*np.sqrt(k_eff)
torsional = [14.5, 22.0, 31.0, 43.5]

fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.plot(k_grid, f_er, color=BLUE, lw=2.0, label=r"$f_{er}$ electrical resonance")
ax.plot(k_grid, f - f_er, color=RED, lw=2.0, label=r"$f_0 - f_{er}$ complement")
for i, fm in enumerate(torsional):
    ax.axhline(fm, color=GRAY, ls=":", lw=1.0, label="torsional modes (example)" if i == 0 else None)
ax.set_xlim(0.1, 0.8); ax.set_ylim(0, 60)
ax.set_xlabel("Degree of compensation $k$")
ax.set_ylabel("Frequency  [Hz]")
ax.legend(loc="lower left")
save(fig, "sc_ssr_screening.pdf")
fe = f*np.sqrt(0.5*X_L_total/(X_L_total + X_source))
print(f"SSR k=0.5: f_er = {fe:.1f} Hz, complement = {f-fe:.1f} Hz; X_source = {X_source:.1f} Ohm")

# ---- bank rating -----------------------------------------------------------
I_rated, k_d = 2000.0, 0.5
X_C = k_d*X_L_total
print(f"bank k=0.5: X_C = {X_C:.1f} Ohm, C = {1/(omega*X_C)*1e6:.1f} uF, U_C = {I_rated*X_C/1e3:.1f} kV, "
      f"Q_C = {3*I_rated**2*X_C/1e6:.0f} Mvar, MOV 2.3x = {2.3*I_rated*X_C/1e3:.0f} kV")
