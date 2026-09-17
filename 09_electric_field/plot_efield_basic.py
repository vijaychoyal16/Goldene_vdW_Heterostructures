#!/usr/bin/env python3
"""Plot E-fermi and dipole moment vs EFIELD from efield_summary.dat."""
import argparse
import numpy as np
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("--data", default="efield_summary.dat")
parser.add_argument("--system", default="Au_MoS2")
args = parser.parse_args()

data = np.genfromtxt(args.data, comments="#", dtype=None, encoding=None)
if data.ndim == 0:
    data = np.array([data])
field = np.array([row[0] for row in data], dtype=float)
toten = np.array([row[2] for row in data], dtype=float)
efermi = np.array([row[3] for row in data], dtype=float)
dipz = np.array([row[4] for row in data], dtype=float)
completed = np.array([row[5] for row in data], dtype=int)
mask = completed == 1

# E-fermi plot
fig, ax = plt.subplots(figsize=(6.5, 4.8))
ax.plot(field[mask], efermi[mask], marker="o")
ax.set_xlabel(r"Applied field, $E_{\mathrm{field}}$ (eV/\AA)", fontsize=14)
ax.set_ylabel(r"$E_F$ (eV)", fontsize=14)
ax.set_title(args.system.replace("_", "/"), fontsize=15)
ax.tick_params(axis="both", labelsize=12)
fig.tight_layout()
fig.savefig(f"efield_Efermi_{args.system}.png", dpi=600)
fig.savefig(f"efield_Efermi_{args.system}.pdf")
plt.close(fig)

# dipole moment plot
fig, ax = plt.subplots(figsize=(6.5, 4.8))
ax.plot(field[mask], dipz[mask], marker="o")
ax.set_xlabel(r"Applied field, $E_{\mathrm{field}}$ (eV/\AA)", fontsize=14)
ax.set_ylabel(r"Dipole moment along $z$ (e\AA)", fontsize=14)
ax.set_title(args.system.replace("_", "/"), fontsize=15)
ax.tick_params(axis="both", labelsize=12)
fig.tight_layout()
fig.savefig(f"efield_dipole_{args.system}.png", dpi=600)
fig.savefig(f"efield_dipole_{args.system}.pdf")
plt.close(fig)

print(f"Saved efield_Efermi_{args.system}.png/.pdf")
print(f"Saved efield_dipole_{args.system}.png/.pdf")
