#!/usr/bin/env python3
"""
Create VASP folders for external electric-field calculations.

Usage example:
python3 make_efield_folders.py \
  --poscar POSCAR_relaxed \
  --potcar POTCAR \
  --kpoints KPOINTS_13atom \
  --incar INCAR_EFIELD_template \
  --slurm runVasp.slurm \
  --fields -0.20 -0.10 -0.05 0.00 0.05 0.10 0.20
"""
import argparse
import shutil
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(errors="ignore")


def set_incar_tag(text: str, tag: str, value: str) -> str:
    lines = text.splitlines()
    out = []
    found = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            out.append(line)
            continue
        lhs = stripped.split("=", 1)[0].strip().upper()
        if lhs == tag.upper():
            out.append(f"{tag} = {value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{tag} = {value}")
    return "\n".join(out) + "\n"


def folder_name(field: float) -> str:
    # e.g. E_m0.10, E_p0.10, E_0.00
    if abs(field) < 1e-12:
        return "E_0.00"
    sign = "p" if field > 0 else "m"
    return f"E_{sign}{abs(field):.2f}"


def main():
    parser = argparse.ArgumentParser(description="Create electric-field scan folders")
    parser.add_argument("--poscar", default="POSCAR_relaxed")
    parser.add_argument("--potcar", default="POTCAR")
    parser.add_argument("--kpoints", default="KPOINTS_13atom")
    parser.add_argument("--incar", default="INCAR_EFIELD_template")
    parser.add_argument("--slurm", default="runVasp.slurm")
    parser.add_argument("--fields", nargs="+", type=float, default=[-0.20, -0.10, -0.05, 0.00, 0.05, 0.10, 0.20])
    parser.add_argument("--dipol", default="0.5 0.5 0.5", help="DIPOL tag in direct coordinates")
    args = parser.parse_args()

    poscar = Path(args.poscar)
    potcar = Path(args.potcar)
    kpoints = Path(args.kpoints)
    incar = Path(args.incar)
    slurm = Path(args.slurm)

    incar_text = read_text(incar)
    incar_text = set_incar_tag(incar_text, "LDIPOL", ".TRUE.")
    incar_text = set_incar_tag(incar_text, "IDIPOL", "3")
    incar_text = set_incar_tag(incar_text, "DIPOL", args.dipol)
    incar_text = set_incar_tag(incar_text, "LVHAR", ".TRUE.")
    incar_text = set_incar_tag(incar_text, "LVTOT", ".TRUE.")
    incar_text = set_incar_tag(incar_text, "LCHARG", ".TRUE.")
    incar_text = set_incar_tag(incar_text, "LWAVE", ".FALSE.")
    incar_text = set_incar_tag(incar_text, "IBRION", "-1")
    incar_text = set_incar_tag(incar_text, "NSW", "0")

    for f in args.fields:
        d = Path(folder_name(f))
        d.mkdir(exist_ok=True)
        shutil.copy2(poscar, d / "POSCAR")
        shutil.copy2(potcar, d / "POTCAR")
        shutil.copy2(kpoints, d / "KPOINTS")
        if slurm.exists():
            shutil.copy2(slurm, d / slurm.name)
        text_f = set_incar_tag(incar_text, "SYSTEM", f"Au_vdW_EFIELD_{f:+.2f}")
        text_f = set_incar_tag(text_f, "EFIELD", f"{f:.6f}")
        (d / "INCAR").write_text(text_f)
        print(f"created {d}/  EFIELD = {f:+.2f}")

    print("\nNext: submit jobs with run_all_efield.sh")


if __name__ == "__main__":
    main()
