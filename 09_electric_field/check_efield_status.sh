#!/usr/bin/env bash
# check_efield_status.sh
# Check VASP electric-field folders such as E_m0.20, E_0.00, E_p0.10.
# Run from the parent 09_electric_field directory.

set -u

OUT="efield_status_summary.dat"
printf "%-12s %-12s %-12s %-18s %-14s %-14s %-12s %-12s\n" \
  "folder" "EFIELD" "status" "TOTEN_eV" "Efermi_eV" "dipole_z" "LOCPOT" "CHGCAR" | tee "$OUT"
printf "%-12s %-12s %-12s %-18s %-14s %-14s %-12s %-12s\n" \
  "------------" "------------" "------------" "------------------" "--------------" "--------------" "------------" "------------" | tee -a "$OUT"

shopt -s nullglob
folders=(E_*)

if [ ${#folders[@]} -eq 0 ]; then
  echo "No E_* folders found. Run this script inside the 09_electric_field parent directory."
  exit 1
fi

for d in "${folders[@]}"; do
  [ -d "$d" ] || continue

  # Extract EFIELD from INCAR if available
  if [ -f "$d/INCAR" ]; then
    ef=$(awk 'BEGIN{IGNORECASE=1} /^[[:space:]]*EFIELD[[:space:]]*=/{print $3}' "$d/INCAR" | tail -1)
  else
    ef="NA"
  fi
  [ -n "${ef:-}" ] || ef="NA"

  if [ ! -f "$d/OUTCAR" ]; then
    status="NO_OUTCAR"
    toten="NA"
    efermi="NA"
    dipz="NA"
  else
    if grep -q "Voluntary context switches" "$d/OUTCAR"; then
      status="DONE"
    elif grep -qi "error\|VERY BAD NEWS\|ZBRENT\|DAV" "$d/OUTCAR"; then
      status="ERROR"
    else
      status="RUN/STOP"
    fi

    toten=$(grep "free  energy   TOTEN" "$d/OUTCAR" | tail -1 | awk '{print $5}')
    [ -n "${toten:-}" ] || toten="NA"

    efermi=$(grep "E-fermi" "$d/OUTCAR" | tail -1 | awk '{print $3}')
    [ -n "${efermi:-}" ] || efermi="NA"

    # Several VASP versions print dipole lines differently; keep last numeric triplet if possible.
    dipz=$(grep -i "dipolmoment\|dipole moment" "$d/OUTCAR" | tail -1 | awk '{for(i=NF;i>=1;i--) if($i ~ /^[-+]?[0-9]*\.?[0-9]+([Ee][-+]?[0-9]+)?$/){print $i; exit}}')
    [ -n "${dipz:-}" ] || dipz="NA"
  fi

  if [ -s "$d/LOCPOT" ]; then
    loc="YES"
  else
    loc="NO"
  fi

  if [ -s "$d/CHGCAR" ]; then
    chg="YES"
  else
    chg="NO"
  fi

  printf "%-12s %-12s %-12s %-18s %-14s %-14s %-12s %-12s\n" \
    "$d" "$ef" "$status" "$toten" "$efermi" "$dipz" "$loc" "$chg" | tee -a "$OUT"
done

echo ""
echo "Saved status table: $OUT"
echo "DONE = VASP finished normally. LOCPOT=YES is needed for work-function plots."
