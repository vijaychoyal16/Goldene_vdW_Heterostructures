#!/usr/bin/env bash
set -e
MODE=${MODE:-sbatch}        # sbatch or run
VASP_EXE=${VASP_EXE:-vasp_std}
NP=${NP:-16}
SLURM_SCRIPT=${SLURM_SCRIPT:-runVasp.slurm}

for d in E_*; do
  [ -d "$d" ] || continue
  echo "===== $d ====="
  cd "$d"
  if [ "$MODE" = "sbatch" ]; then
    if [ ! -f "$SLURM_SCRIPT" ]; then
      echo "Missing $SLURM_SCRIPT in $d"
    else
      sbatch "$SLURM_SCRIPT"
    fi
  else
    mpirun -np "$NP" "$VASP_EXE" > vasp.out 2> vasp.err
  fi
  cd ..
done
