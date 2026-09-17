#!/usr/bin/env python3
"""Plot electric-field VASP results from efield_summary.dat.

Produces:
- efield_total_energy_<system>.png/.pdf
- efield_fermi_<system>.png/.pdf
- efield_dipole_<system>.png/.pdf, if dipole exists
- efield_workfunction_<system>.png/.pdf, if workfunction_summary.dat exists

Optional workfunction_summary.dat format:
# EFIELD W_bottom W_top DeltaV_vac
-0.10  5.20  5.05  -0.15
 0.00  5.10  5.12   0.02
 0.10  4.95  5.25   0.30
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np


def load_summary(path: str = "efield_summary.dat") -> Dict[str, np.ndarray]:
    rows: List[List[float]] = []
    folders: List[str] = []
    completed: List[bool] = []
    for line in Path(path).read_text(errors="ignore").splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 9 or "NA" in (parts[0], parts[2], parts[3], parts[4]):
            continue
        if parts[6] != "True":
            continue
        ef = float(parts[0])
        folder = parts[1]
        toten = float(parts[2])
        erel = float(parts[3])
        efermi = float(parts[4])
        dipole = np.nan if parts[5] == "NA" else float(parts[5])
        rows.append([ef, toten, erel, efermi, dipole])
        folders.append(folder)
        completed.append(True)
    if not rows:
        raise RuntimeError("No completed numeric rows found in efield_summary.dat. Run collect_efield.py first and check VASP completion.")
    arr = np.array(rows, dtype=float)
    order = np.argsort(arr[:, 0])
    arr = arr[order]
    return {
        "field": arr[:, 0],
        "toten": arr[:, 1],
        "erel": arr[:, 2],
        "efermi": arr[:, 3],
        "dipole": arr[:, 4],
    }


def save_line_plot(x, y, system: str, ylabel: str, basename: str, title: Optional[str] = None) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    ax.plot(x, y, marker="o", linewidth=2.0, markersize=6)
    ax.axvline(0.0, linestyle="--", linewidth=1.0)
    ax.set_xlabel(r"Electric field (eV/\AA)", fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.set_title(title or system.replace("_", "/"), fontsize=15)
    ax.tick_params(axis="both", labelsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{basename}_{system}.png", dpi=600)
    fig.savefig(f"{basename}_{system}.pdf")
    plt.close(fig)


def load_workfunction(path: str = "workfunction_summary.dat"):
    p = Path(path)
    if not p.exists():
        return None
    data = []
    for line in p.read_text(errors="ignore").splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            data.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
        except ValueError:
            continue
    if not data:
        return None
    arr = np.array(data, dtype=float)
    arr = arr[np.argsort(arr[:, 0])]
    return arr


def plot_workfunction(arr, system: str):
    x = arr[:, 0]
    fig, ax = plt.subplots(figsize=(6.8, 4.9))
    ax.plot(x, arr[:, 1], marker="o", linewidth=2.0, markersize=6, label=r"$W_{bottom}$")
    ax.plot(x, arr[:, 2], marker="s", linewidth=2.0, markersize=6, label=r"$W_{top}$")
    ax.axvline(0.0, linestyle="--", linewidth=1.0)
    ax.set_xlabel(r"Electric field (eV/\AA)", fontsize=14)
    ax.set_ylabel("Work function (eV)", fontsize=14)
    ax.set_title(system.replace("_", "/"), fontsize=15)
    ax.tick_params(axis="both", labelsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False, fontsize=12)
    fig.tight_layout()
    fig.savefig(f"efield_workfunction_{system}.png", dpi=600)
    fig.savefig(f"efield_workfunction_{system}.pdf")
    plt.close(fig)

    save_line_plot(x, arr[:, 3], system, r"$\Delta V_{vac}$ (eV)", "efield_vacuum_difference", system.replace("_", "/"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", default="Au_MoS2", help="System name used in output figure names, e.g., Au_MoS2")
    parser.add_argument("--summary", default="efield_summary.dat")
    args = parser.parse_args()

    data = load_summary(args.summary)
    x = data["field"]

    save_line_plot(x, data["erel"] * 1000.0, args.system, r"$E - E_{min}$ (meV)", "efield_total_energy", args.system.replace("_", "/"))
    save_line_plot(x, data["efermi"], args.system, r"$E_F$ (eV)", "efield_fermi", args.system.replace("_", "/"))

    if np.isfinite(data["dipole"]).any():
        save_line_plot(x, data["dipole"], args.system, r"Dipole moment, $z$ component", "efield_dipole", args.system.replace("_", "/"))

    wf = load_workfunction()
    if wf is not None:
        plot_workfunction(wf, args.system)
        print("Work-function plots created from workfunction_summary.dat")
    else:
        print("No workfunction_summary.dat found. Basic energy/Fermi/dipole plots were created.")

    print("Saved figures:")
    for p in sorted(Path(".").glob(f"efield_*_{args.system}.png")):
        print("  ", p.name)


if __name__ == "__main__":
    main()
