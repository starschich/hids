"""Worked example of the link and DC line chapters: the link of the link notebook, the power given at each of the
four points and the reverse direction, and the cable resistance.

Writes points_table.tex, link_values.tex. Run from the document folder:  python link/fig/link_example.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from example_data import LINK_POINT, dc_line, dl, link, ls, num, write  # noqa: E402

base = ls.calculate(link, **LINK_POINT).result
lf = base.loadflow


def by_station(r):
    a_rec = r.rectifier.name == link.station_a.name
    l = r.loadflow
    pa, pb = (l.p_ac_rec_mw, l.p_ac_inv_mw) if a_rec else (l.p_ac_inv_mw, l.p_ac_rec_mw)
    da, db = (l.p_dc_rec_mw, l.p_dc_inv_mw) if a_rec else (l.p_dc_inv_mw, l.p_dc_rec_mw)
    return r.rectifier.name[-1], pa, da, db, pb, l.i_d_ka, l.p_loss_total_mw, l.iterations


cases = [("$P_{pcc\\_a} = -1000$\\,MW", dict(p_a_mw=-1000.0)),
         ("$P_{dc\\_a}$ of row 1", dict(p_dc_a_mw=lf.p_dc_rec_mw)),
         ("$P_{dc\\_b}$ of row 1", dict(p_dc_b_mw=lf.p_dc_inv_mw)),
         ("$P_{pcc\\_b}$ of row 1", dict(p_b_mw=lf.p_ac_inv_mw)),
         ("$P_{pcc\\_a} = +1000$\\,MW", dict(p_a_mw=1000.0)),
         ("$P_{pcc\\_b} = -1000$\\,MW", dict(p_b_mw=-1000.0))]
rows = []
for label, power in cases:
    r = ls.calculate(link, ls.input(ls.input(**LINK_POINT), **power)).result
    rec, pa, da, db, pb, i_d, loss, it = by_station(r)
    rows.append(f"  {label} & {rec} & {num(pa, 2)} & {num(da, 2)} & {num(db, 2)} & {num(pb, 2)} & {num(i_d, 4)} & "
                f"{num(loss, 2)} & {it} \\\\")
write(HERE / "points_table.tex", "\n".join(rows) + "\n")
write(HERE / "link_values.tex",
      f"\\newcommand{{\\lkRtwenty}}{{{num(dl.resistance(dc_line, t_c=20.0), 3)}}}\n"
      f"\\newcommand{{\\lkRseventy}}{{{num(dl.resistance(dc_line, t_c=70.0), 3)}}}\n"
      f"\\newcommand{{\\lkUinv}}{{{num(lf.u_dpe_inv_kv, 3)}}}\n\\newcommand{{\\lkId}}{{{num(lf.i_d_ka, 4)}}}\n"
      f"\\newcommand{{\\lkLine}}{{{num(2 * base.dc_line.p_loss_mw, 3)}}}\n"
      f"\\newcommand{{\\lkLoss}}{{{num(lf.p_loss_total_mw, 3)}}}\n\\newcommand{{\\lkEta}}{{{num(lf.efficiency_pct, 3)}}}\n")
