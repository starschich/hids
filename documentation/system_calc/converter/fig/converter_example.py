"""Worked example of the converter chapter: the converter of the station example at the rectifier point of the
station chapter (valve-side voltage, Q and DC voltage from the station calculation).

Writes arm_waveforms.pdf, losses_table.tex, capacitor_table.tex. Run from the document folder:
    python converter/fig/converter_example.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from example_data import STATION_POINT, arm_reactor, converter, cs, num, st, station, write  # noqa: E402

res = st.calculate(station, **STATION_POINT).result
c = res.station.converter
inp = cs.input(u_valve_kv=c.u_valve_kv, q_ac_mvar=c.q_ac_mvar, u_dc_kv=c.u_dc_kv, p_ac_mw=c.p_ac_mw)

rows = [f"  {r['part']} & {num(r['mw'], 3)} & {'' if r['pct'] is None else num(r['pct'], 3)} \\\\"
        for r in cs.losses(converter, arm_reactor, inp)]
write(HERE / "losses_table.tex", "\n".join(rows[:4]) + "\n  \\midrule\n" + rows[4] + "\n  \\midrule\n"
      + "\n".join(rows[5:]) + "\n")

pt = cs.calculate(converter, arm_reactor, inp).result
vals = [("modulation index $m$", num(pt.modulation_index, 4), ""),
        ("inner modulation index $a$", num(pt.a_inner, 4), ""),
        ("$U_{arm\\_max} / (N \\cdot u_{sm})$", num(pt.u_arm_max_kv / (converter.n_sm_per_arm * converter.u_sm_kv), 4), ""),
        ("stored energy $W_0$, six arms", num(pt.w_stored_mj, 2), "MJ"),
        ("stored energy per MV$\\cdot$A", num(pt.w_stored_kj_per_mva, 1), "kJ/(MV$\\cdot$A)"),
        ("energy variation of one arm, peak-to-peak", num(pt.dw_arm_mj, 3), "MJ"),
        ("capacitor voltage, lowest", num(pt.u_sm_min_kv, 3), "kV"),
        ("capacitor voltage, highest", num(pt.u_sm_max_kv, 3), "kV"),
        ("ripple, peak-to-peak", num(pt.du_sm_pct, 2), "\\%"),
        ("margin of the arm voltage to $N \\cdot u_c$", num(pt.u_arm_margin_kv, 1), "kV")]
write(HERE / "capacitor_table.tex", "\n".join(f"  {a} & {b} & {u} \\\\" for a, b, u in vals) + "\n")
write(HERE / "converter_values.tex",
      f"\\newcommand{{\\cvUv}}{{{num(c.u_valve_kv, 2)}}}\n\\newcommand{{\\cvQ}}{{{num(c.q_ac_mvar, 1)}}}\n"
      f"\\newcommand{{\\cvUdc}}{{{num(c.u_dc_kv, 2)}}}\n\\newcommand{{\\cvP}}{{{num(c.p_ac_mw, 2)}}}\n"
      f"\\newcommand{{\\cvIrms}}{{{num(pt.i_arm_rms_ka, 4)}}}\n\\newcommand{{\\cvIpk}}{{{num(pt.i_arm_peak_ka, 4)}}}\n")

w = cs.waveforms(converter, arm_reactor, inp, samples=360)
ang = [r["angle_deg"] for r in w]
fig, ax = plt.subplots(1, 3, figsize=(12, 3.4))
ax[0].plot(ang, [r["u_upper_kv"] for r in w], label="upper arm")
ax[0].plot(ang, [r["u_lower_kv"] for r in w], label="lower arm")
ax[0].set(title="arm voltage [kV]")
ax[1].plot(ang, [r["i_upper_ka"] for r in w], label="upper arm")
ax[1].plot(ang, [r["i_lower_ka"] for r in w], label="lower arm")
ax[1].set(title="arm current [kA]")
ax[2].plot(ang, [r["u_c_upper_kv"] for r in w], label="upper arm")
ax[2].plot(ang, [r["u_c_lower_kv"] for r in w], label="lower arm")
ax[2].axhline(converter.u_sm_kv, color="grey", ls=":", lw=1, label="$u_{sm}$")
ax[2].set(title="submodule capacitor voltage [kV]")
for a in ax:
    a.set_xlabel("ωt [°]"); a.set_xticks(range(0, 361, 90)); a.grid(alpha=0.3); a.legend(fontsize=7)
fig.tight_layout()
fig.savefig(HERE / "arm_waveforms.pdf")
print("wrote", HERE / "arm_waveforms.pdf")
