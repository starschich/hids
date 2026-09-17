"""Regenerate tables/*.tex from the PSLF .dyd file. Run from documentation/fervo:  python3 gen_tables.py

Parse the PSLF .dyd file and emit LaTeX parameter tables (one per model type).

Values are taken verbatim from the .dyd so the document cannot drift from the source.
Two parameter sets exist: Turboden units (bus 17 id 1/2, bus 22 id 1) and
Baker Hughes units (bus 22 id 2, bus 23 id 1/2, bus 25 id 1/2). The script
verifies that every unit in a set is identical and prints one column per set,
or a single column when both sets coincide.
"""
import re, sys
from collections import OrderedDict

DYD = "references/ModelDYD_Fervo_Cape Station_Ph2_2026.09.05.dyd"
OUT = "tables"

txt = open(DYD).read()
# join continuation lines
txt = re.sub(r"/\s*\n", " ", txt)
recs = []
for line in txt.splitlines():
    line = line.strip()
    if not line or line.startswith("#") or line == "models":
        continue
    m = re.match(r'(\w+)\s+(\d+)\s+"([^"]*)"\s+([\d.]+)\s+"([^"]*)"\s*:\s*(#\d+)?\s*(.*)$', line)
    if not m:
        continue
    model, bus, name, kv, cid, ver, rest = m.groups()
    params = OrderedDict()
    for k, v in re.findall(r'(\w+)=([\d.\-]+)', rest):
        params[k] = v
    rest = re.sub(r'\w+=[\d.\-]+', '', rest)
    for k, v in re.findall(r'"(\w+)"\s+([\-\d.]+)', rest):
        params[k] = v
    recs.append(dict(model=model, bus=int(bus), name=name.strip(), cid=cid.strip(), ver=ver, params=params))

TURBODEN = {(17, "1"), (17, "2"), (22, "1")}
BAKER = {(22, "2"), (23, "1"), (23, "2"), (25, "1"), (25, "2")}

def fmt(v):
    f = float(v)
    if f == int(f) and abs(f) < 1e6:
        return f"{int(f)}"
    s = f"{f:.6f}".rstrip("0").rstrip(".")
    return s

def texname(p):
    """Parameter name as PSLF spells it, in typewriter."""
    return r"\texttt{" + p.replace("_", r"\_") + "}"

# descriptions -------------------------------------------------------------
DESC = {
 "genqec": OrderedDict([
  ("mva",   ("Machine MVA base",                       r"MV$\cdot$A")),
  ("tpdo",  ("d-axis transient open-circuit time constant $T'_{d0}$", "s")),
  ("tppdo", ("d-axis subtransient open-circuit time constant $T''_{d0}$", "s")),
  ("tpqo",  ("q-axis transient open-circuit time constant $T'_{q0}$", "s")),
  ("tppqo", ("q-axis subtransient open-circuit time constant $T''_{q0}$", "s")),
  ("h",     ("Inertia constant $H$", r"MW$\cdot$s/MV$\cdot$A")),
  ("d",     ("Damping factor $D$", "pu")),
  ("ld",    ("d-axis synchronous reactance $L_d$", "pu")),
  ("lq",    ("q-axis synchronous reactance $L_q$", "pu")),
  ("lpd",   ("d-axis transient reactance $L'_d$", "pu")),
  ("lpq",   ("q-axis transient reactance $L'_q$", "pu")),
  ("lppd",  ("d-axis subtransient reactance $L''_d$", "pu")),
  ("lppq",  ("q-axis subtransient reactance $L''_q$", "pu")),
  ("ll",    ("Stator leakage reactance $L_l$", "pu")),
  ("s1",    ("Saturation factor at 1.0 pu flux $S(1.0)$", "--")),
  ("s12",   ("Saturation factor at 1.2 pu flux $S(1.2)$", "--")),
  ("ra",    ("Stator resistance $R_a$", "pu")),
  ("rcomp", ("Compounding resistance (voltage-regulator compensation)", "pu")),
  ("xcomp", ("Compounding reactance (voltage-regulator compensation)", "pu")),
  ("kw",    ("Saturation weighting factor $K_w$", "--")),
  ("satflg",("Saturation-function selector", "--")),
 ]),
 "esac8b": OrderedDict([
  ("tr",    ("Terminal-voltage transducer time constant $T_R$", "s")),
  ("kpr",   ("Regulator proportional gain $K_{PR}$", "pu")),
  ("kir",   ("Regulator integral gain $K_{IR}$", "pu/s")),
  ("kdr",   ("Regulator derivative gain $K_{DR}$", r"pu$\cdot$s")),
  ("tdr",   ("Derivative-block time constant $T_{DR}$", "s")),
  ("vrmax", ("Regulator output upper limit $V_{RMAX}$", "pu")),
  ("vrmin", ("Regulator output lower limit $V_{RMIN}$", "pu")),
  ("ka",    ("Amplifier gain $K_A$", "pu")),
  ("ta",    ("Amplifier time constant $T_A$", "s")),
  ("te",    ("Exciter time constant $T_E$", "s")),
  ("vfemax",("Exciter field-current limit $V_{FEMAX}$", "pu")),
  ("vemin", ("Minimum exciter voltage $V_{EMIN}$", "pu")),
  ("ke",    ("Exciter self-excitation constant $K_E$", "pu")),
  ("kc",    ("Rectifier loading factor $K_C$", "pu")),
  ("kd",    ("Exciter demagnetising factor $K_D$", "pu")),
  ("e1",    ("Exciter voltage at saturation point 1 $E_1$", "pu")),
  ("se1",   ("Saturation at $E_1$, $S_E(E_1)$", "--")),
  ("e2",    ("Exciter voltage at saturation point 2 $E_2$", "pu")),
  ("se2",   ("Saturation at $E_2$, $S_E(E_2)$", "--")),
  ("vtmult",("Terminal-voltage multiplier on regulator limits (0 = off)", "--")),
  ("spdmlt",("Speed multiplier on exciter output (0 = off)", "--")),
 ]),
 "ggov1": OrderedDict([
  ("mwcap", ("Turbine MW capability (governor base)", "MW")),
  ("r",     ("Permanent droop $R$", "pu")),
  ("rselect",("Feedback signal for droop (1 = electrical power)", "--")),
  ("tpelec",("Electrical-power transducer time constant $T_{pelec}$", "s")),
  ("maxerr",("Maximum speed-error signal", "pu")),
  ("minerr",("Minimum speed-error signal", "pu")),
  ("kpgov", ("Governor proportional gain $K_{Pgov}$", "pu")),
  ("kigov", ("Governor integral gain $K_{Igov}$", "pu/s")),
  ("kdgov", ("Governor derivative gain $K_{Dgov}$", r"pu$\cdot$s")),
  ("tdgov", ("Governor derivative time constant $T_{Dgov}$", "s")),
  ("vmax",  ("Maximum valve position $V_{max}$", "pu")),
  ("vmin",  ("Minimum valve position $V_{min}$", "pu")),
  ("tact",  ("Actuator time constant $T_{act}$", "s")),
  ("kturb", ("Turbine gain $K_{turb}$", "pu")),
  ("wfnl",  ("No-load fuel flow $W_{fnl}$", "pu")),
  ("tb",    ("Turbine lag time constant $T_b$", "s")),
  ("tc",    ("Turbine lead time constant $T_c$", "s")),
  ("flag",  ("Fuel-flow speed dependence (0 = independent of speed)", "--")),
  ("teng",  ("Transport lag for diesel engine $T_{eng}$", "s")),
  ("tfload",("Load-limiter transducer time constant $T_{fload}$", "s")),
  ("kpload",("Load-limiter proportional gain $K_{Pload}$", "pu")),
  ("kiload",("Load-limiter integral gain $K_{Iload}$", "pu/s")),
  ("ldref", ("Load-limiter reference $L_{dref}$", "pu")),
  ("dm",    ("Mechanical damping / speed sensitivity $D_m$", "pu")),
  ("ropen", ("Maximum valve opening rate $R_{open}$", "pu/s")),
  ("rclose",("Maximum valve closing rate $R_{close}$", "pu/s")),
  ("kimw",  ("Power-controller (MW) integral gain $K_{imw}$", "pu/s")),
  ("pmwset",("Power-controller setpoint $P_{mwset}$", "MW")),
  ("aset",  ("Acceleration-limiter setpoint $a_{set}$", "pu/s")),
  ("ka",    ("Acceleration-limiter gain $K_a$", "pu")),
  ("ta",    ("Acceleration-limiter time constant $T_a$", "s")),
  ("db",    ("Speed governor deadband", "pu")),
  ("tsa",   ("Temperature-detection lead time constant $T_{sa}$", "s")),
  ("tsb",   ("Temperature-detection lag time constant $T_{sb}$", "s")),
  ("rup",   ("Maximum rate of load-limit increase", "pu/s")),
  ("rdown", ("Maximum rate of load-limit decrease", "pu/s")),
 ]),
 "pss2a": OrderedDict([
  ("j1",    ("Input signal 1 code (1 = rotor speed deviation)", "--")),
  ("k1",    ("Remote bus for input 1 (0 = local)", "--")),
  ("j2",    ("Input signal 2 code (3 = electrical power)", "--")),
  ("k2",    ("Remote bus for input 2 (0 = local)", "--")),
  ("tw1",   ("Washout time constant $T_{w1}$", "s")),
  ("tw2",   ("Washout time constant $T_{w2}$", "s")),
  ("tw3",   ("Washout time constant $T_{w3}$", "s")),
  ("tw4",   ("Washout time constant $T_{w4}$ (0 = bypassed)", "s")),
  ("t6",    ("Input 1 transducer time constant $T_6$", "s")),
  ("t7",    ("Input 2 transducer time constant $T_7$", "s")),
  ("ks2",   ("Input 2 gain $K_{S2}$ ($= T_7 / (2 \\cdot H)$)", "pu")),
  ("ks3",   ("Signal-matching gain $K_{S3}$", "pu")),
  ("ks4",   ("Input 2 gain $K_{S4}$", "pu")),
  ("t8",    ("Ramp-tracking filter lead time constant $T_8$", "s")),
  ("t9",    ("Ramp-tracking filter lag time constant $T_9$", "s")),
  ("n",     ("Ramp-tracking filter order $N$", "--")),
  ("m",     ("Ramp-tracking filter order $M$", "--")),
  ("ks1",   ("Stabilizer gain $K_{S1}$", "pu")),
  ("t1",    ("Lead time constant $T_1$", "s")),
  ("t2",    ("Lag time constant $T_2$", "s")),
  ("t3",    ("Lead time constant $T_3$", "s")),
  ("t4",    ("Lag time constant $T_4$", "s")),
  ("vstmax",("Stabilizer output upper limit $V_{STMAX}$", "pu")),
  ("vstmin",("Stabilizer output lower limit $V_{STMIN}$", "pu")),
  ("a",     ("Optional second-order filter coefficient $a$", "--")),
  ("ta",    ("Optional filter time constant $T_a$", "s")),
  ("tb",    ("Optional filter time constant $T_b$", "s")),
 ]),
}
# fix a tuple typo guard
for k, d in DESC.items():
    for p, v in d.items():
        assert isinstance(v, tuple) and len(v) == 2, (k, p, v)

def group(model):
    sets = {"Turboden": [], "Baker Hughes": []}
    for r in recs:
        if r["model"] != model:
            continue
        key = (r["bus"], r["cid"])
        if key in TURBODEN:
            sets["Turboden"].append(r)
        elif key in BAKER:
            sets["Baker Hughes"].append(r)
        else:
            raise SystemExit(f"unassigned unit {key}")
    out = {}
    for name, lst in sets.items():
        assert lst, (model, name)
        first = lst[0]["params"]
        for r in lst[1:]:
            assert r["params"] == first, (model, name, r["bus"], r["cid"])
        out[name] = first
    return out

import os
os.makedirs(OUT, exist_ok=True)

for model, desc in DESC.items():
    sets = group(model)
    tb, bh = sets["Turboden"], sets["Baker Hughes"]
    assert list(tb.keys()) == list(bh.keys()), model
    for p in tb:
        assert p in desc, (model, p)
    same = all(float(tb[p]) == float(bh[p]) for p in tb)
    lines = []
    if same:
        lines.append(r"\begin{tabularx}{\linewidth}{@{}l X l r@{}}")
        lines.append(r"\toprule")
        lines.append(r"\textbf{Parameter} & \textbf{Description} & \multicolumn{1}{c}{\textbf{Unit}} & \multicolumn{1}{c}{\textbf{Value}} \\")
    else:
        lines.append(r"\begin{tabularx}{\linewidth}{@{}l X l r r@{}}")
        lines.append(r"\toprule")
        lines.append(r"\textbf{Parameter} & \textbf{Description} & \multicolumn{1}{c}{\textbf{Unit}} & \multicolumn{1}{c}{\textbf{Turboden}} & \multicolumn{1}{c}{\textbf{Baker Hughes}} \\")
    lines.append(r"\midrule")
    for p in tb:
        d, u = desc[p]
        row = f"{texname(p)} & {d} & {u} & {fmt(tb[p])}"
        if not same:
            row += f" & {fmt(bh[p])}"
        lines.append(row + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabularx}")
    open(f"{OUT}/{model}.tex", "w").write("\n".join(lines) + "\n")
    print(model, "identical" if same else "two sets", len(tb), "parameters")

# ride-through models: emit stage tables and pgfplots coordinates -------------
def rt(model, pfx, refkey):
    sets = group(model)
    tb, bh = sets["Turboden"], sets["Baker Hughes"]
    assert tb == bh, model
    p = tb
    ref = float(p[refkey])
    stages = []
    for i in range(1, 11):
        dv = float(p[f"d{pfx}trp{i}"]); dt = float(p[f"dttrp{i}"])
        if dv == 0 and dt == 0:
            continue
        stages.append((i, dv, dt))
    return ref, stages, p

ref_v, st_v, p_v = rt("lhvrt", "v", "vref")
ref_f, st_f, p_f = rt("lhfrt", "f", "fref")

def rt_table(stages, ref, dvname, absname, dvunit, absunit, absfmt):
    lines = [r"\begin{tabularx}{\linewidth}{@{}l r r r@{}}", r"\toprule",
             r"\textbf{Stage} & \multicolumn{1}{c}{\textbf{" + dvname + r"}} & \multicolumn{1}{c}{\textbf{" + absname + r"}} & \multicolumn{1}{c}{\textbf{Time delay}} \\",
             r" & \multicolumn{1}{c}{" + dvunit + r"} & \multicolumn{1}{c}{" + absunit + r"} & \multicolumn{1}{c}{s} \\", r"\midrule"]
    for i, dv, dt in stages:
        lines.append(f"{i} & {dv:+.2f} & {absfmt(ref+dv)} & {fmt(dt)} \\\\")
    lines += [r"\bottomrule", r"\end{tabularx}"]
    return "\n".join(lines) + "\n"

open(f"{OUT}/lhvrt.tex", "w").write(rt_table(st_v, ref_v, r"$\Delta U$", "$U$", "pu", "pu", lambda x: f"{x:.2f}"))
open(f"{OUT}/lhfrt.tex", "w").write(rt_table(st_f, ref_f, r"$\Delta f$", "$f$", "Hz", "Hz", lambda x: f"{x:.1f}"))

# plot coordinates: for each stage, horizontal segment from t_delay to tmax at level ref+dv
def coords(stages, ref, tmax):
    over = sorted([(ref+dv, dt) for _, dv, dt in stages if dv > 0])       # ascending level
    under = sorted([(ref+dv, dt) for _, dv, dt in stages if dv < 0], reverse=True)
    def stair(lst, tmax):
        # lst sorted from closest-to-ref outward; trip region is beyond the level for t > dt
        pts = []
        # build boundary curve: time on x, level on y; staircase from long times to short
        for lvl, dt in lst:
            pts.append((dt, lvl))
        return pts
    return stair(over, tmax), stair(under, tmax)

import json
json.dump({"lhvrt": {"ref": ref_v, "stages": st_v}, "lhfrt": {"ref": ref_f, "stages": st_f}},
          open(f"{OUT}/rt.json", "w"), indent=1)
print("lhvrt stages", st_v)
print("lhfrt stages", st_f)
