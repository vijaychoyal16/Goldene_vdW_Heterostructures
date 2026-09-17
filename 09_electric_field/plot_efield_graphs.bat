@echo off
REM plot_efield_graphs.bat
REM Windows batch file to collect and plot electric-field results.
REM Put this file in the parent 09_electric_field folder together with:
REM collect_efield.py, plot_efield_graphs.py, and E_m0.10 / E_0.00 / E_p0.10 folders.

set SYSTEM=Au_MoS2
if not "%~1"=="" set SYSTEM=%~1

echo ===============================================
echo Collecting electric-field VASP results for %SYSTEM%
echo ===============================================

python collect_efield.py
if errorlevel 1 (
    echo collect_efield.py failed. Check that E_* folders and OUTCAR files exist.
    pause
    exit /b 1
)

echo ===============================================
echo Plotting electric-field graphs for %SYSTEM%
echo ===============================================

python plot_efield_graphs.py --system %SYSTEM%
if errorlevel 1 (
    echo plot_efield_graphs.py failed. Check efield_summary.dat and Python packages.
    pause
    exit /b 1
)

echo ===============================================
echo Done. Created PNG/PDF electric-field graphs.
echo Example files:
echo efield_total_energy_%SYSTEM%.png
echo efield_fermi_%SYSTEM%.png
echo efield_dipole_%SYSTEM%.png, if dipole data exist
echo ===============================================
pause
