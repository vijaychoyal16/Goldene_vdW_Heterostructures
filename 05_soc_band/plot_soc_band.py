#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import argparse
import re


def read_fermi_from_outcar(outcar="OUTCAR"):
    ef = None
    with open(outcar, "r", errors="ignore") as f:
        for line in f:
            if "E-fermi" in line:
                ef = float(line.split()[2])
    if ef is None:
        raise RuntimeError("Could not find E-fermi in OUTCAR.")
    return ef


def read_eigenval(eigenval="EIGENVAL"):
    with open(eigenval, "r", errors="ignore") as f:
        lines = f.readlines()

    header = lines[5].split()
    nelect = int(header[0])
    nkpts = int(header[1])
    nbands = int(header[2])

    kdist = []
    eigs = []

    index = 7
    k_prev = None
    dist = 0.0

    for ik in range(nkpts):
        while len(lines[index].split()) < 4:
            index += 1

        k = np.array([float(x) for x in lines[index].split()[0:3]])

        if k_prev is not None:
            dist += np.linalg.norm(k - k_prev)

        kdist.append(dist)
        k_prev = k.copy()
        index += 1

        band_energies = []
        for ib in range(nbands):
            parts = lines[index].split()
            band_energies.append(float(parts[1]))
            index += 1

        eigs.append(band_energies)

    return np.array(kdist), np.array(eigs), nkpts, nbands


def read_kpoints_labels(kpoints="KPOINTS"):
    labels = []
    with open(kpoints, "r", errors="ignore") as f:
        for line in f:
            if "!" in line:
                label = line.split("!")[-1].strip()

                label_low = label.lower()
                if "gamma" in label_low or "\\gamma" in label_low or "gamm" in label_low:
                    label = r"$\Gamma$"
                elif label_low == "m":
                    label = "M"
                elif label_low == "k":
                    label = "K"
                else:
                    label = label

                labels.append(label)

    clean_labels = []
    for label in labels:
        if len(clean_labels) == 0 or clean_labels[-1] != label:
            clean_labels.append(label)

    return clean_labels


def get_high_symmetry_positions(kdist, labels):
    nlabels = len(labels)

    if nlabels == 4:
        return [kdist[0], kdist[len(kdist)//3], kdist[2*len(kdist)//3], kdist[-1]]
    elif nlabels == 3:
        return [kdist[0], kdist[len(kdist)//2], kdist[-1]]
    else:
        return np.linspace(kdist[0], kdist[-1], nlabels)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", default="Au_MoS2_SOC")
    parser.add_argument("--emin", type=float, default=-2.0)
    parser.add_argument("--emax", type=float, default=2.0)
    parser.add_argument("--outcar", default="OUTCAR")
    parser.add_argument("--eigenval", default="EIGENVAL")
    parser.add_argument("--kpoints", default="KPOINTS")
    args = parser.parse_args()

    efermi = read_fermi_from_outcar(args.outcar)
    kdist, eigs, nkpts, nbands = read_eigenval(args.eigenval)
    eigs = eigs - efermi

    labels = read_kpoints_labels(args.kpoints)

    if len(labels) == 0:
        labels = [r"$\Gamma$", "M", "K", r"$\Gamma$"]

    xpos = get_high_symmetry_positions(kdist, labels)

    plt.figure(figsize=(7.5, 6.0))

    for ib in range(nbands):
        plt.plot(kdist, eigs[:, ib], color="black", linewidth=0.8)

    plt.axhline(0.0, color="red", linestyle="--", linewidth=1.2)

    for x in xpos:
        plt.axvline(x, color="gray", linestyle="--", linewidth=0.8)

    plt.xlim(kdist[0], kdist[-1])
    plt.ylim(args.emin, args.emax)

    plt.xticks(xpos, labels, fontsize=16)
    plt.yticks(fontsize=14)

    plt.xlabel("Wave vector", fontsize=18)
    plt.ylabel(r"$E - E_F$ (eV)", fontsize=18)
    plt.title(args.system.replace("_", "/"), fontsize=18)

    plt.tight_layout()

    png_name = f"band_{args.system}_clean.png"
    pdf_name = f"band_{args.system}_clean.pdf"

    plt.savefig(png_name, dpi=600)
    plt.savefig(pdf_name)

    print("SOC band plot completed")
    print(f"Fermi energy = {efermi:.6f} eV")
    print(f"nkpts = {nkpts}, nbands = {nbands}")
    print(f"Saved: {png_name}")
    print(f"Saved: {pdf_name}")


if __name__ == "__main__":
    main()