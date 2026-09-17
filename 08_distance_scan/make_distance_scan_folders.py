#!/usr/bin/env python3
"""
Create fixed-interlayer-distance VASP folders for 08_distance_scan.

Example for Au/MX2 when Au is the lower layer and MX2 is the upper layer:
python3 make_distance_scan_folders.py \
  --poscar POSCAR_relaxed \
  --bottom Au \
  --top Mo S \
  --distances 2.75 3.00 3.25 3.45 3.75 4.00 4.25 \
  --incar INCAR_static_fixed_distance \
  --kpoints KPOINTS_13atom \
  --potcar POTCAR \
  --slurm runVasp.slurm

If your Au layer is above the semiconductor layer, swap --bottom and --top.
"""

import argparse
import os
import shutil
from pathlib import Path
import numpy as np


def read_poscar(path):
    lines = Path(path).read_text().splitlines()
    if len(lines) < 8:
        raise ValueError(f"{path} does not look like a valid POSCAR")

    comment = lines[0]
    scale = float(lines[1].split()[0])
    cell = np.array([[float(x) for x in lines[i].split()[:3]] for i in range(2, 5)], dtype=float) * scale

    idx = 5
    tokens = lines[idx].split()
    try:
        [int(x) for x in tokens]
        raise ValueError("This script expects a POSCAR with an element-symbol line, e.g. Au Mo S")
    except ValueError as exc:
        if "expects" in str(exc):
            raise

    elements = tokens
    counts = [int(x) for x in lines[idx + 1].split()]
    idx += 2

    selective = False
    if lines[idx].strip().lower().startswith("s"):
        selective = True
        idx += 1

    coord_mode = lines[idx].strip().lower()
    direct = coord_mode.startswith("d")
    cartesian = coord_mode.startswith("c") or coord_mode.startswith("k")
    if not (direct or cartesian):
        raise ValueError(f"Could not identify coordinate mode in line: {lines[idx]}")
    idx += 1

    natoms = sum(counts)
    coord_lines = lines[idx:idx + natoms]
    coords = np.array([[float(x) for x in line.split()[:3]] for line in coord_lines], dtype=float)

    labels = []
    for el, count in zip(elements, counts):
        labels.extend([el] * count)

    if direct:
        frac = coords.copy()
        cart = frac @ cell
    else:
        cart = coords * scale
        frac = cart @ np.linalg.inv(cell)

    return {
        "comment": comment,
        "cell": cell,
        "elements": elements,
        "counts": counts,
        "labels": labels,
        "frac": frac,
        "cart": cart,
        "selective": selective,
    }


def write_poscar(path, data, frac, comment):
    cell = data["cell"]
    with open(path, "w") as f:
        f.write(comment + "\n")
        f.write("1.0\n")
        for vec in cell:
            f.write(f"{vec[0]:20.12f} {vec[1]:20.12f} {vec[2]:20.12f}\n")
        f.write("  " + "  ".join(data["elements"]) + "\n")
        f.write("  " + "  ".join(str(x) for x in data["counts"]) + "\n")
        f.write("Direct\n")
        for r in frac:
            f.write(f"{r[0]:18.12f} {r[1]:18.12f} {r[2]:18.12f}\n")


def copy_if_given(src, dst_name, folder):
    if src is None:
        return
    src_path = Path(src)
    if not src_path.exists():
        print(f"WARNING: {src} not found; not copied")
        return
    shutil.copy2(src_path, Path(folder) / dst_name)


def main():
    p = argparse.ArgumentParser(description="Create fixed-distance scan folders for VASP")
    p.add_argument("--poscar", default="POSCAR", help="Input relaxed heterostructure POSCAR/CONTCAR")
    p.add_argument("--bottom", nargs="+", required=True, help="Element symbols of lower layer, e.g. Au")
    p.add_argument("--top", nargs="+", required=True, help="Element symbols of upper layer, e.g. Mo S")
    p.add_argument("--distances", nargs="+", type=float,
                   default=[2.75, 3.00, 3.25, 3.45, 3.75, 4.00, 4.25],
                   help="Target vertical interlayer gaps in Angstrom")
    p.add_argument("--prefix", default="d_", help="Folder prefix")
    p.add_argument("--incar", default=None, help="INCAR template to copy")
    p.add_argument("--kpoints", default=None, help="KPOINTS template to copy")
    p.add_argument("--potcar", default=None, help="POTCAR to copy")
    p.add_argument("--slurm", default=None, help="SLURM script to copy as runVasp.slurm")
    p.add_argument("--center", action="store_true", help="Center final slab along z after changing distance")
    args = p.parse_args()

    data = read_poscar(args.poscar)
    cell = data["cell"]
    cart0 = data["cart"].copy()
    labels = np.array(data["labels"])

    bottom_mask = np.isin(labels, args.bottom)
    top_mask = np.isin(labels, args.top)

    if not np.any(bottom_mask):
        raise ValueError(f"No atoms found for bottom layer elements: {args.bottom}")
    if not np.any(top_mask):
        raise ValueError(f"No atoms found for top layer elements: {args.top}")
    if np.any(bottom_mask & top_mask):
        raise ValueError("Bottom and top element sets overlap; use distinct layer definitions")

    z_bottom_max = cart0[bottom_mask, 2].max()
    z_top_min = cart0[top_mask, 2].min()
    current_gap = z_top_min - z_bottom_max

    print("Distance-scan setup")
    print("-------------------")
    print(f"Input POSCAR      : {args.poscar}")
    print(f"Bottom elements   : {' '.join(args.bottom)}")
    print(f"Top elements      : {' '.join(args.top)}")
    print(f"Current z gap     : {current_gap:.6f} Angstrom")
    if current_gap < 0:
        print("WARNING: current gap is negative. Your top/bottom layers may be swapped.")

    inv_cell = np.linalg.inv(cell)

    for d in args.distances:
        folder = f"{args.prefix}{d:.2f}"
        os.makedirs(folder, exist_ok=True)

        cart = cart0.copy()
        shift = d - current_gap
        cart[top_mask, 2] += shift

        if args.center:
            zmin = cart[:, 2].min()
            zmax = cart[:, 2].max()
            c_length = np.linalg.norm(cell[2])
            cart[:, 2] += 0.5 * c_length - 0.5 * (zmin + zmax)

        frac = cart @ inv_cell
        frac[:, 0] = frac[:, 0] % 1.0
        frac[:, 1] = frac[:, 1] % 1.0

        write_poscar(Path(folder) / "POSCAR", data, frac, f"{data['comment']} | fixed d = {d:.2f} A")
        copy_if_given(args.incar, "INCAR", folder)
        copy_if_given(args.kpoints, "KPOINTS", folder)
        copy_if_given(args.potcar, "POTCAR", folder)
        copy_if_given(args.slurm, "runVasp.slurm", folder)

        print(f"Created {folder}/POSCAR with target d = {d:.2f} A")

    print("Done.")


if __name__ == "__main__":
    main()
