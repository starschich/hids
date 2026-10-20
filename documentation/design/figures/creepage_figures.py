#!/usr/bin/env python3
"""
Figures for design/transmission-line/creepage-distance/creepage-distance.tex (cd_*.pdf).

cd_creepage_voltage.pdf : required total creepage L = USCD * U_dpe versus
pole-to-earth DC voltage for the indicative USCD bands of ceramic/glass and
composite insulators (light / medium / heavy pollution), with the 400 kV
study voltage marked.
Indicative USCD values only (IEC TS 60815-4, CIGRE TB 518), not agreed
design constants.  numpy + matplotlib only.  Run from this directory.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 11, "axes.labelsize": 11,
    "legend.fontsize": 9.5, "axes.grid": True, "grid.color": "#d9d9d9",
    "grid.linewidth": 0.8, "axes.edgecolor": "#8a8a8a", "axes.linewidth": 0.8,
    "legend.framealpha": 1.0, "legend.edgecolor": "#c9c7c2", "pdf.fonttype": 42,
})
BLUE, GREEN, GRAY, RED = "#1f77b4", "#2e8b57", "#5c5c5c", "#c0392b"

U = np.linspace(150, 850, 200)          # kV, pole-to-earth
U_proj = 400.0                          # kV, study DC voltage

# indicative USCD bands in mm/kV: (low, high) for medium pollution,
# plus the light and heavy limits drawn as thin lines
bands = {
    "Ceramic / glass": dict(color=BLUE, light=30, med=(40, 50), heavy=60),
    "Composite":       dict(color=GREEN, light=25, med=(30, 38), heavy=45),
}

fig, ax = plt.subplots(figsize=(5.2, 4.0))
for name, b in bands.items():
    lo, hi = b["med"]
    ax.fill_between(U, lo*U/1000, hi*U/1000, color=b["color"], alpha=0.22, lw=0,
                    label=f"{name}, medium ({lo}–{hi} mm/kV)")
    ax.plot(U, b["light"]*U/1000, color=b["color"], lw=1.0, ls="--")
    ax.plot(U, b["heavy"]*U/1000, color=b["color"], lw=1.0, ls=":")
ax.plot([], [], color=GRAY, lw=1.0, ls="--", label="light limit")
ax.plot([], [], color=GRAY, lw=1.0, ls=":", label="heavy limit")

ax.axvline(U_proj, color=RED, lw=1.2)
ax.text(U_proj + 12, 49, "400 kV", color=RED, fontsize=10, va="top")
for name, b in bands.items():
    for v in b["med"]:
        ax.plot(U_proj, v*U_proj/1000, "o", color=b["color"], ms=4)

ax.set_xlim(150, 850)
ax.set_ylim(0, 52)
ax.set_xlabel(r"Pole-to-earth DC voltage $U_{dpe}$ in kV")
ax.set_ylabel(r"Total creepage $L$ in m")
fig.legend(loc="lower center", ncol=2, fontsize=8.5, frameon=False)
fig.tight_layout(rect=(0, 0.16, 1, 1))
fig.savefig("cd_creepage_voltage.pdf")
