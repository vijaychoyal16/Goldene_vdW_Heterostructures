#!/usr/bin/env python3
"""Collect VASP energies from d_* folders and write distance_scan.dat."""

import re
from pathlib import Path
import numpy as np


def parse_distance(folder_name):
    m = re.search(r"([0-9]+\.?[0-9]*)", folder_name)
    if not m:
        return None
    return float(m.group(1))


def read_sigma0(outcar):
    energy = None
    with open(outcar, "r", errors="ignore") as f:
        for line in f:
            if "energy  without entropy" in line and "energy(sigma->0)" in line:
                nums = re.findall(r"[-+]?\d+\.\d+", line)
                if nums:
                    energy = float(nums[-1])
    return energy


def read_efermi(outcar):
    ef = None
    with open(outcar, "r", errors="ignore") as f:
        for line in f:
            if "E-fermi" in line:
                parts = line.split()
                try:
                    ef = float(parts[2])
                except Exception:
                    pass
    return ef


def completed(outcar):
    try:
        text = Path(outcar).read_text(errors="ignore")[-5000:]
        return "Voluntary context switches" in text
    except Exception:
        return False


rows = []
for folder in sorted(Path(".").glob("d_*")):
    if not folder.is_dir():
        continue
    d = parse_distance(folder.name)
    outcar = folder / "OUTCAR"
    if d is None or not outcar.exists():
        continue
    E = read_sigma0(outcar)
    EF = read_efermi(outcar)
    ok = completed(outcar)
    if E is not None:
        rows.append([d, E, EF if EF is not None else np.nan, 1 if ok else 0])

if not rows:
    raise SystemExit("No completed energies found in d_* folders.")

rows = np.array(sorted(rows, key=lambda x: x[0]), dtype=float)
Emin = rows[:, 1].min()
Erel_eV = rows[:, 1] - Emin
Erel_meV = Erel_eV * 1000.0
out = np.column_stack([rows[:, 0], rows[:, 1], Erel_eV, Erel_meV, rows[:, 2], rows[:, 3]])

np.savetxt(
    "distance_scan.dat",
    out,
    fmt=["%.4f", "%.10f", "%.10f", "%.4f", "%.6f", "%.0f"],
    header="d_A E_total_eV E_minus_Emin_eV E_minus_Emin_meV E_F_eV completed_1_yes_0_no",
)

print("Distance-scan results")
print("---------------------")
print("d(A)     E_total(eV)        E-Emin(meV)     E_F(eV)    complete")
for r in out:
    print(f"{r[0]:5.2f}  {r[1]:16.8f}  {r[3]:12.4f}  {r[4]:10.4f}  {int(r[5])}")
print("Saved: distance_scan.dat")
