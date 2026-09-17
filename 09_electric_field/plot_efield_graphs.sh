#!/usr/bin/env bash
# Linux/cluster version for plotting electric-field graphs.
# Run from the parent 09_electric_field folder.

set -euo pipefail
SYSTEM=${1:-Au_MoS2}

python3 collect_efield.py
python3 plot_efield_graphs.py --system "$SYSTEM"

echo "Done. Created electric-field plots for $SYSTEM"
ls -lh efield_*_${SYSTEM}.png 2>/dev/null || true
