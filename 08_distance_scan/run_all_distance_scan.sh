#!/bin/bash
# Submit or run all fixed-distance scan folders.
# Put this script in the parent 08_distance_scan folder.

set -e

MODE=${MODE:-sbatch}   # sbatch or run
VASP_EXE=${VASP_EXE:-vasp_std}
NP=${NP:-16}

for d in d_*; do
    [ -d "$d" ] || continue
    echo "===== $d ====="
    cd "$d"
    if [ "$MODE" = "sbatch" ]; then
        sbatch runVasp.slurm
    else
        mpirun -np "$NP" "$VASP_EXE" > vasp.out 2> vasp.err
    fi
    cd ..
done
