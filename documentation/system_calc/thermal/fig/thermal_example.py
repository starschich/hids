"""Worked example of the thermal chapter: on-state model against the datasheet, temperatures of the cold plate,
modules and dies at the converter point of the converter chapter, junction temperatures over one period, and the
highest junction temperature against water flow and inlet temperature.

Writes onstate_table.tex, modules_table.tex, dies_table.tex, flow_table.tex, junction_waveforms.pdf.
Run from the document folder:  python thermal/fig/thermal_example.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from example_data import STATION_POINT, arm_reactor, converter, cs, igbt, num, st, station, write  # noqa: E402
from hvdc_lf.services import SemiconductorService  # noqa: E402

ss = SemiconductorService()
# datasheet points at Tj = 125 °C: 1000 A from the tables (pages 2, 3), the others read from the typical curves (page 4)
IGBT_125 = [(0.25, 1.85), (0.5, 2.35), (1.0, 3.25), (1.5, 3.95), (2.0, 4.55)]
DIODE_125 = [(0.25, 1.80), (0.5, 2.20), (1.0, 2.80), (1.5, 3.30), (2.0, 3.75)]
rows = [f"  {'IGBT' if r['device'] == 'igbt' else 'diode'} & {num(r['i_ka'], 2)} & {num(r['datasheet_v'], 2)} & "
        f"{num(r['model_v'], 2)} & {num(r['deviation_v'], 2)} \\\\"
        for r in ss.compare(igbt, igbt_points=IGBT_125, diode_points=DIODE_125)]
write(HERE / "onstate_table.tex", "\n".join(rows) + "\n")

res = st.calculate(station, **STATION_POINT).result
c = res.station.converter
inp = cs.input(u_valve_kv=c.u_valve_kv, q_ac_mvar=c.q_ac_mvar, u_dc_kv=c.u_dc_kv, p_ac_mw=c.p_ac_mw,
               t_water_in_c=50.0, q_water_l_per_min=10.0)
t = cs.temperatures(converter, arm_reactor, inp)
write(HERE / "modules_table.tex", "\n".join(
    f"  {m['position']} & {m['order']} & {num(m['p_kw'], 3)} & {num(m['t_water_c'], 1)} & {num(m['t_heatsink_c'], 1)} & "
    f"{num(m['t_case_c'], 1)} \\\\" for m in t["modules"]) + "\n")
write(HERE / "dies_table.tex", "\n".join(
    f"  {d['die']} & {num(d['p_mean_kw'], 3)} & {num(d['p_max_kw'], 3)} & {num(d['t_j_mean_c'], 1)} & "
    f"{num(d['t_j_max_c'], 1)} & {num(d['dt_j_pp_k'], 2)} \\\\" for d in t["dies"]) + "\n")
cool = {r["quantity"]: r["value"] for r in t["cooling"]}
write(HERE / "thermal_values.tex",
      f"\\newcommand{{\\thTout}}{{{num(cool['water outlet'], 2)}}}\n"
      f"\\newcommand{{\\thPplate}}{{{num(cool['losses per cold plate (submodule)'], 3)}}}\n"
      f"\\newcommand{{\\thTjmax}}{{{num(cool['highest junction temperature'], 1)}}}\n"
      f"\\newcommand{{\\thHot}}{{{cool['hottest die']}}}\n\\newcommand{{\\thArm}}{{{cool['arm (the hotter one of phase a)']}}}\n")

flows, inlets = (5.0, 7.5, 10.0, 15.0, 20.0), (40.0, 50.0, 60.0)
rows = []
for q in flows:
    cells = []
    for t_in in inlets:
        th = cs.calculate(converter, arm_reactor, cs.input(inp, t_water_in_c=t_in, q_water_l_per_min=q)).result.thermal
        cells.append(num(th.t_j_max_c, 1))
    rows.append(f"  {num(q, 1)} & " + " & ".join(cells) + " \\\\")
write(HERE / "flow_table.tex", "\n".join(rows) + "\n")

jw = cs.junction_waveforms(converter, arm_reactor, inp)
ang = [r["angle_deg"] for r in jw]
fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
for d in ("T1", "D1", "T2", "D2"):
    ax[0].plot(ang, [r[f"p_{d}_kw"] for r in jw], label=d)
    ax[1].plot(ang, [r[f"t_j_{d}_c"] for r in jw], label=d)
ax[0].set(title="losses of the dies of one module [kW]")
ax[1].set(title="junction temperature [°C]")
for a in ax:
    a.set_xlabel("ωt [°]"); a.set_xticks(range(0, 361, 90)); a.grid(alpha=0.3); a.legend(fontsize=7, ncol=2)
fig.tight_layout()
fig.savefig(HERE / "junction_waveforms.pdf")
print("wrote", HERE / "junction_waveforms.pdf")
