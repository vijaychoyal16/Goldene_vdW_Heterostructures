Run three folders with the same lattice and same FFT settings: hetero, goldene_only, tmd_only.
Charge-density difference: chgdiff.pl CHGCAR_hetero CHGCAR_goldene CHGCAR_tmd
Bader: chgsum.pl AECCAR0 AECCAR2; bader CHGCAR -ref CHGCAR_sum
