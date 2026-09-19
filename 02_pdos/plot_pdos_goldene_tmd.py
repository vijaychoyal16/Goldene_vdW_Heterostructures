#!/usr/bin/env python3

"""
Smooth publication-quality PDOS plot from VASP vasprun.xml.

Requirements:
    pip install pymatgen matplotlib numpy

Example for Goldene/Bi2Se3:
    python3 plot_pdos_goldene_smooth.py \
        python 

Example for Goldene/MoS2:
    python3 plot_pdos_goldene_smooth.py \
        --system Goldene_MoS2 \
        --tmd-metal Mo \
        --metal-orbital d \
        --chalcogen S \
        --chalcogen-orbital p \
        --emin -6 --emax 4 \
        --smooth-sigma 0.06
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt

from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.core.periodic_table import Element
from pymatgen.electronic_structure.core import Spin, OrbitalType


def get_dos_array(dos):
    """Return spin-summed DOS array."""
    up = dos.densities.get(Spin.up, np.zeros_like(dos.energies))
    down = dos.densities.get(Spin.down, None)
    if down is None:
        return np.array(up, dtype=float)
    return np.array(up + down, dtype=float)


def get_orbital_type(label):
    label = label.lower()
    if label == "s":
        return OrbitalType.s
    if label == "p":
        return OrbitalType.p
    if label == "d":
        return OrbitalType.d
    if label == "f":
        return OrbitalType.f
    raise ValueError(f"Unsupported orbital type: {label}. Use s, p, d, or f.")


def gaussian_smooth(y, energies, sigma_eV):
    """
    Smooth DOS using a Gaussian kernel with width sigma_eV.
    sigma_eV = 0 means no smoothing.
    """
    y = np.asarray(y, dtype=float)
    if sigma_eV <= 0:
        return y

    dE = np.median(np.diff(energies))
    if dE <= 0:
        raise RuntimeError("Energy grid is not increasing.")

    sigma_pts = sigma_eV / dE
    radius = max(3, int(np.ceil(4.0 * sigma_pts)))
    x = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * (x / sigma_pts) ** 2)
    kernel /= kernel.sum()

    # Reflect padding reduces edge artifacts.
    y_pad = np.pad(y, radius, mode="reflect")
    y_smooth = np.convolve(y_pad, kernel, mode="same")[radius:-radius]
    return y_smooth


def plot_one(ax, energies, density, label, mask, sigma, lw):
    density_smooth = gaussian_smooth(density, energies, sigma)
    ax.plot(energies[mask], density_smooth[mask], linewidth=lw, label=label)


def main():
    parser = argparse.ArgumentParser(
        description="Smooth element- and orbital-projected DOS from VASP vasprun.xml"
    )

    parser.add_argument("--vasprun", default="vasprun.xml")
    parser.add_argument("--system", default="Goldene_MoS2")
    parser.add_argument("--tmd-metal", default="Mo", help="Mo, W, Bi, In, etc.")
    parser.add_argument("--metal-orbital", default="d", help="s, p, d, or f")
    parser.add_argument("--chalcogen", default="S", help="S, Se, or Te")
    parser.add_argument("--chalcogen-orbital", default="p", help="s, p, d, or f")
    parser.add_argument("--emin", type=float, default=-6.0)
    parser.add_argument("--emax", type=float, default=4.0)
    parser.add_argument("--smooth-sigma", type=float, default=0.06,
                        help="Gaussian smoothing width in eV. Good range: 0.04-0.10 eV.")
    parser.add_argument("--no-total", action="store_true", help="Do not plot total DOS")
    parser.add_argument("--hide-metal", action="store_true",
                        help="Do not plot the non-Au metal projection, useful when you only want Au and chalcogen DOS")
    parser.add_argument("--ymax", type=float, default=None)
    parser.add_argument("--output-prefix", default=None)

    args = parser.parse_args()

    print("Reading vasprun.xml ...")
    vasprun = Vasprun(
        args.vasprun,
        parse_dos=True,
        parse_projected_eigen=False
    )

    cdos = vasprun.complete_dos
    efermi = cdos.efermi
    energies = cdos.energies - efermi
    mask = (energies >= args.emin) & (energies <= args.emax)

    fig, ax = plt.subplots(figsize=(7.4, 5.2))

    if not args.no_total:
        total_dos = get_dos_array(cdos)
        plot_one(ax, energies, total_dos, "Total DOS", mask, args.smooth_sigma, 2.2)

    projections = [
        ("Au", "s", "Au-$s$"),
        ("Au", "d", "Au-$d$"),
    ]

    if not args.hide_metal:
        projections.append(
            (args.tmd_metal, args.metal_orbital,
             f"{args.tmd_metal}-${args.metal_orbital}$")
        )

    projections.append(
        (args.chalcogen, args.chalcogen_orbital,
         f"{args.chalcogen}-${args.chalcogen_orbital}$")
    )

    for element_symbol, orbital_symbol, label in projections:
        try:
            element = Element(element_symbol)
            orbital_type = get_orbital_type(orbital_symbol)
            spd_dos = cdos.get_element_spd_dos(element)
            orbital_dos = spd_dos[orbital_type]
            density = get_dos_array(orbital_dos)
            plot_one(ax, energies, density, label, mask, args.smooth_sigma, 2.0)
        except Exception as error:
            print(f"Warning: could not plot {label}: {error}")

    ax.axvline(0.0, linestyle="--", linewidth=1.4)
    ax.set_xlim(args.emin, args.emax)
    if args.ymax is not None:
        ax.set_ylim(0, args.ymax)

    ax.set_xlabel(r"$E - E_F$ (eV)", fontsize=15)
    ax.set_ylabel("DOS (states/eV)", fontsize=15)
    ax.set_title(args.system.replace("_", "/"), fontsize=16)
    ax.tick_params(axis="both", labelsize=13, width=1.2, length=5)
    ax.legend(frameon=False, fontsize=12)

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)

    plt.tight_layout()

    prefix = args.output_prefix or f"PDOS_smooth_{args.system}"
    png_name = f"{prefix}.png"
    pdf_name = f"{prefix}.pdf"
    dat_name = f"{prefix}.dat"

    plt.savefig(png_name, dpi=600, bbox_inches="tight")
    plt.savefig(pdf_name, bbox_inches="tight")

    print(f"Saved: {png_name}")
    print(f"Saved: {pdf_name}")
    print(f"Fermi energy used from vasprun.xml: {efermi:.6f} eV")
    print(f"Gaussian smoothing sigma: {args.smooth_sigma:.4f} eV")


if __name__ == "__main__":
    main()
