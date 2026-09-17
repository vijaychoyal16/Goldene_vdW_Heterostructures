#!/usr/bin/env python3
"""Collect basic VASP electric-field results from E_* folders.

Creates efield_summary.dat with:
EFIELD_eV_per_A folder TOTEN_eV EminusEmin_eV Efermi_eV dipole_z completed locpot chgcar
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


def read_text(path: Path) -> str:
    return path.read_text(errors="ignore")


def parse_efield(folder: Path) -> Optional[float]:
    incar = folder / "INCAR"
    if not incar.exists():
        return None
    for line in read_text(incar).splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if re.match(r"^EFIELD\s*=", s, re.I):
            m = re.search(r"EFIELD\s*=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", s, re.I)
            if m:
                return float(m.group(1))
    return None


def parse_toten(outcar_text: str) -> Optional[float]:
    vals = re.findall(r"free\s+energy\s+TOTEN\s+=\s+([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", outcar_text)
    return float(vals[-1]) if vals else None


def parse_efermi(outcar_text: str) -> Optional[float]:
    vals = re.findall(r"E-fermi\s*:\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", outcar_text)
    return float(vals[-1]) if vals else None


def parse_dipole_z(outcar_text: str) -> Optional[float]:
    lines = [ln for ln in outcar_text.splitlines() if re.search(r"dipolmoment|dipole moment", ln, re.I)]
    if not lines:
        return None
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?", lines[-1])
    return float(nums[-1]) if nums else None


def fmt(x: Optional[float], ndigits: int = 8) -> str:
    return "NA" if x is None else f"{x:.{ndigits}f}"


def main() -> None:
    rows = []
    for folder in sorted(Path(".").glob("E_*")):
        if not folder.is_dir():
            continue
        ef = parse_efield(folder)
        outcar = folder / "OUTCAR"
        completed = False
        toten = efermi = dipz = None
        if outcar.exists():
            txt = read_text(outcar)
            completed = "Voluntary context switches" in txt
            toten = parse_toten(txt)
            efermi = parse_efermi(txt)
            dipz = parse_dipole_z(txt)
        rows.append({
            "EFIELD": ef,
            "folder": folder.name,
            "TOTEN": toten,
            "Efermi": efermi,
            "dipole_z": dipz,
            "completed": completed,
            "locpot": (folder / "LOCPOT").exists() and (folder / "LOCPOT").stat().st_size > 0,
            "chgcar": (folder / "CHGCAR").exists() and (folder / "CHGCAR").stat().st_size > 0,
        })

    done_energies = [r["TOTEN"] for r in rows if r["completed"] and r["TOTEN"] is not None]
    emin = min(done_energies) if done_energies else None

    out = Path("efield_summary.dat")
    with out.open("w") as f:
        f.write("# EFIELD_eV_per_A folder TOTEN_eV EminusEmin_eV Efermi_eV dipole_z completed LOCPOT CHGCAR\n")
        for r in sorted(rows, key=lambda row: (999 if row["EFIELD"] is None else row["EFIELD"])):
            e_rel = None if (emin is None or r["TOTEN"] is None) else r["TOTEN"] - emin
            f.write(
                f"{fmt(r['EFIELD'], 4):>10s} "
                f"{r['folder']:>12s} "
                f"{fmt(r['TOTEN'], 8):>16s} "
                f"{fmt(e_rel, 8):>16s} "
                f"{fmt(r['Efermi'], 8):>14s} "
                f"{fmt(r['dipole_z'], 8):>14s} "
                f"{str(r['completed']):>9s} "
                f"{str(r['locpot']):>7s} "
                f"{str(r['chgcar']):>7s}\n"
            )

    print(f"Saved {out}")
    if not rows:
        print("No E_* folders were found.")
    else:
        print(f"Found {len(rows)} electric-field folders.")
        print("Use: python3 plot_efield_graphs.py --system Au_MoS2")


if __name__ == "__main__":
    main()
