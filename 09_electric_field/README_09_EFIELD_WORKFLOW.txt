09_electric_field workflow
==========================

Goal:
Study how an external electric field perpendicular to the vdW heterostructure changes
work function, Fermi level, interface dipole, and later Schottky barrier/contact type.

Recommended fields for first scan:
EFIELD = -0.20, -0.10, -0.05, 0.00, +0.05, +0.10, +0.20 eV/Angstrom
For final publication, use a smaller range if the structure or SCF becomes unstable.

Order:
1. Use fully relaxed POSCAR/CONTCAR at equilibrium interlayer distance.
2. Copy POSCAR_relaxed, POTCAR, KPOINTS_13atom, INCAR_EFIELD_template, runVasp.slurm.
3. Run make_efield_folders.py.
4. Submit all folders with run_all_efield.sh.
5. Check completion with check_efield_status.sh.
6. Collect E_F/dipole/TOTEN with collect_efield.py.
7. Use your work-function LOCPOT script inside each folder for W_bottom/W_top vs field.
8. Use projected band edges/PDOS to extract Schottky barrier vs field.

Example:
python3 make_efield_folders.py --poscar POSCAR_relaxed --potcar POTCAR --kpoints KPOINTS_13atom --incar INCAR_EFIELD_template --slurm runVasp.slurm --fields -0.20 -0.10 -0.05 0.00 0.05 0.10 0.20
MODE=sbatch ./run_all_efield.sh
./check_efield_status.sh
python3 collect_efield.py
python3 plot_efield_basic.py --system Au_MoS2
