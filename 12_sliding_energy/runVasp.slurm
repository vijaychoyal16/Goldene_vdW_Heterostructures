#!/bin/sh
#SBATCH --time=200:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --error %x.e%j
#SBATCH --error %x.o%j
#SBATCH --mem-per-cpu=5G
#SBATCH --mail-user=vchoyal@iop.uni-hannover.de
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --partition=amo
#SBATCH --job-name='05_soc_band'

cd ${SLURM_SUBMIT_DIR}

module load intel/2022b


#exe='/bigwork/nhbmvcho/VASP/vasp.6.2.0/bin/vasp_std'
exe='/bigwork/nhbmvcho/VASP/vasp.6.2.0/bin/vasp_ncl'

mpirun -np ${SLURM_NTASKS} ${exe} 

