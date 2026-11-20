"""Worked example of the station chapter: chain, losses and the single-line diagram with the results.

Writes chain_table.tex, losses_table.tex, procedures_table.tex and loadflow_station.pdf (Glyphwright, source
examples/sld/loadflow_station.yaml; the repository is found through GLYPHWRIGHT, default ~/Projects/glyphwright).
Run from the document folder:  python station/fig/station_example.py
"""

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from example_data import STATION_POINT, num, st, station, write  # noqa: E402

pt = st.calculate(station, **STATION_POINT)
res = pt.result
lf = res.loadflow

rows = []
for r in st.chain(res):
    q = "" if r["q_mvar"] is None else num(r["q_mvar"], 1)
    loss = "" if r["p_loss_mw"] is None else num(r["p_loss_mw"], 3)
    rows.append(f"  {r['element']} & {num(r['u_kv'], 2)} & {num(r['p_mw'], 2)} & {q} & {num(r['i_ka'], 4)} & {loss} \\\\")
write(HERE / "chain_table.tex", "\n".join(rows) + "\n")

rows = [f"  {r['part']} & {num(r['mw'], 3)} & {num(r['pct'], 3)} \\\\" for r in st.losses(res)]
write(HERE / "losses_table.tex", "\n".join(rows[:-1]) + "\n  \\midrule\n" + rows[-1] + "\n")

# the same operating point with the power given at the DC terminal: secant iterations
dc = st.calculate(station, **{**STATION_POINT, "p_mw": None, "p_dc_mw": lf.p_dc_mw}).result.loadflow
inv = st.calculate(station, **{**STATION_POINT, "p_mw": None, "p_dc_mw": 990.0}).result.loadflow
rows = [f"  $P_{{pcc}}$ given & {num(lf.p_ac_mw, 3)} & {num(lf.p_dc_mw, 3)} & {num(lf.i_dc_ka, 5)} & "
        f"{num(lf.u_dc_conv_kv, 3)} & {lf.iterations} \\\\",
        f"  $P_{{dc}}$ given, rectifier & {num(dc.p_ac_mw, 3)} & {num(dc.p_dc_mw, 3)} & {num(dc.i_dc_ka, 5)} & "
        f"{num(dc.u_dc_conv_kv, 3)} & {dc.iterations} \\\\",
        f"  $P_{{dc}}$ given, inverter & {num(inv.p_ac_mw, 3)} & {num(inv.p_dc_mw, 3)} & {num(inv.i_dc_ka, 5)} & "
        f"{num(inv.u_dc_conv_kv, 3)} & {inv.iterations} \\\\"]
write(HERE / "procedures_table.tex", "\n".join(rows) + "\n")
write(HERE / "station_values.tex",
      f"\\newcommand{{\\exPdc}}{{{num(lf.p_dc_mw, 2)}}}\n\\newcommand{{\\exId}}{{{num(lf.i_dc_ka, 4)}}}\n"
      f"\\newcommand{{\\exLoss}}{{{num(lf.p_loss_mw, 3)}}}\n\\newcommand{{\\exEta}}{{{num(lf.efficiency_pct, 3)}}}\n"
      f"\\newcommand{{\\exM}}{{{num(res.station.converter.modulation_index, 4)}}}\n"
      f"\\newcommand{{\\exUconv}}{{{num(lf.u_dc_conv_kv, 3)}}}\n")

gw = Path(os.environ.get("GLYPHWRIGHT", Path.home() / "Projects/glyphwright"))
sys.path.insert(0, str(gw))
out = Path(os.environ.get("GW_OUT", HERE / "_sld"))
files = st.single_line(station, res, gw / "examples/sld/loadflow_station.yaml", out_dir=out)
shutil.copy(files["pdf"], HERE / "loadflow_station.pdf")
print("wrote", HERE / "loadflow_station.pdf")
