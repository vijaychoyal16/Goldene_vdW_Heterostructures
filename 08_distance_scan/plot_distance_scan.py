#!/usr/bin/env python3
"""Plot E(d)-Emin from distance_scan.dat."""

import argparse
import numpy as np
import matplotlib.pyplot as plt

p = argparse.ArgumentParser()
p.add_argument("--data", default="distance_scan.dat")
p.add_argument("--system", default="Au_MoS2")
p.add_argument("--unit", choices=["meV", "eV"], default="meV")
args = p.parse_args()

d = np.loadtxt(args.data)
x = d[:, 0]
y = d[:, 3] if args.unit == "meV" else d[:, 2]
ylabel = r"$E(d)-E_{\min}$ (meV/cell)" if args.unit == "meV" else r"$E(d)-E_{\min}$ (eV/cell)"

imin = int(np.argmin(y))

def clean_title(s):
    return s.replace("_", "/")

plt.figure(figsize=(6.8, 5.0))
plt.plot(x, y, marker="o", linewidth=2.0)
plt.scatter([x[imin]], [y[imin]], s=80, zorder=5, label=fr"minimum $d$ = {x[imin]:.2f} $\AA$")
plt.xlabel(r"Interlayer distance $d$ ($\AA$)", fontsize=16)
plt.ylabel(ylabel, fontsize=16)
plt.title(clean_title(args.system), fontsize=17)
plt.legend(frameon=False, fontsize=12)
plt.tick_params(axis="both", labelsize=13)
plt.tight_layout()
plt.savefig(f"distance_scan_{args.system}.png", dpi=600)
plt.savefig(f"distance_scan_{args.system}.pdf")
print(f"Minimum distance: {x[imin]:.2f} A")
print(f"Saved: distance_scan_{args.system}.png/.pdf")
