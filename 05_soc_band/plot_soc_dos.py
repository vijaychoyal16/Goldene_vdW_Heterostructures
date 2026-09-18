#!/usr/bin/env python3

import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.core import Spin


def read_fermi_from_outcar(outcar="OUTCAR"):
    ef = None
    if not os.path.exists(outcar):
        return None

    with open(outcar, "r", errors="ignore") as f:
        for line in f:
            if "E-fermi" in line:
                try:
                    ef = float(line.split()[2])
                except Exception:
                    pass
    return ef


def check_kpoints(kpoints="KPOINTS"):
    if not os.path.exists(kpoints):
        return

    with open(kpoints, "r", errors="ignore") as f:
        text = f.read().lower()

    if "line-mode" in text or "linemode" in text:
        print("\nWARNING:")
        print("This folder uses line-mode KPOINTS.")
        print("Band-structure KPOINTS are not suitable for DOS.")
        print("Use a uniform Gamma-centered mesh such as 9 9 1 for SOC DOS.\n")


def get_total_dos(dos):
    up = dos.densities.get(Spin.up, None)
    down = dos.densities.get(Spin.down, None)

    if up is not None and down is not None:
        return up + down
    if up is not None:
        return up
    if down is not None:
        return down

    raise RuntimeError("Could not read DOS density from vasprun.xml.")


def gaussian_smooth(y, sigma_points):
    if sigma_points <= 0:
        return y

    radius = int(4 * sigma_points + 1)
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-(x**2) / (2 * sigma_points**2))
    kernel /= kernel.sum()

    return np.convolve(y, kernel, mode="same")


def main():
    parser = argparse.ArgumentParser(
        description="Plot clean SOC total DOS from VASP vasprun.xml"
    )
    parser.add_argument("--vasprun", default="vasprun.xml")
    parser.add_argument("--outcar", default="OUTCAR")
    parser.add_argument("--kpoints", default="KPOINTS")
    parser.add_argument("--system", default="Au_MoS2_SOC")
    parser.add_argument("--emin", type=float, default=-4.0)
    parser.add_argument("--emax", type=float, default=3.0)
    parser.add_argument("--sigma", type=float, default=0.06,
                        help="Gaussian smoothing width in eV")
    parser.add_argument("--per-atom", action="store_true",
                        help="Normalize DOS by number of atoms")
    args = parser.parse_args()

    check_kpoints(args.kpoints)

    print("Reading vasprun.xml ...")
    vr = Vasprun(args.vasprun, parse_dos=True, parse_projected_eigen=False)

    dos = vr.complete_dos

    ef_outcar = read_fermi_from_outcar(args.outcar)
    if ef_outcar is not None:
        efermi = ef_outcar
        print(f"Using Fermi energy from OUTCAR: {efermi:.6f} eV")
    else:
        efermi = dos.efermi
        print(f"Using Fermi energy from vasprun.xml: {efermi:.6f} eV")

    energy = dos.energies - efermi
    density = get_total_dos(dos)

    if args.per_atom:
        natoms = len(vr.final_structure)
        density = density / natoms
        ylabel = "DOS (states/eV/atom)"
    else:
        ylabel = "DOS (states/eV)"

    dE = np.mean(np.diff(dos.energies))
    sigma_points = args.sigma / dE
    density_smooth = gaussian_smooth(density, sigma_points)

    mask = (energy >= args.emin) & (energy <= args.emax)

    np.savetxt(
        f"DOS_data_{args.system}.dat",
        np.column_stack((energy[mask], density[mask], density_smooth[mask])),
        header="E_minus_EF_eV  DOS_raw  DOS_smooth",
        fmt="%.8f"
    )

    plt.figure(figsize=(7.2, 5.2))

    plt.plot(
        energy[mask],
        density_smooth[mask],
        linewidth=2.2,
        label="SOC total DOS"
    )

    plt.axvline(
        0.0,
        linestyle="--",
        linewidth=1.4,
        label=r"$E_F$"
    )

    plt.xlabel(r"$E-E_F$ (eV)", fontsize=18)
    plt.ylabel(ylabel, fontsize=18)
    plt.title(args.system.replace("_", "/"), fontsize=18)

    plt.xlim(args.emin, args.emax)
    plt.ylim(bottom=0)

    plt.legend(frameon=False, fontsize=14)
    plt.tick_params(axis="both", labelsize=15)
    plt.tight_layout()

    png_name = f"DOS_{args.system}_clean.png"
    pdf_name = f"DOS_{args.system}_clean.pdf"

    plt.savefig(png_name, dpi=600)
    plt.savefig(pdf_name)

    print("DOS plot completed.")
    print(f"Saved: {png_name}")
    print(f"Saved: {pdf_name}")
    print(f"Saved: DOS_data_{args.system}.dat")


if __name__ == "__main__":
    main()