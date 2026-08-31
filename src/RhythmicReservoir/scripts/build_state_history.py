"""Convert JutulDarcy binary state histories into compact, portable NPZ files."""
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results_3d"
CASES = ("P-2", "P-5", "P-10", "R-2", "R-5", "R-10", "C-2", "C-5", "C-10")
NX, NY, NZ = 50, 10, 20
POROSITY = 0.20


def read_history(path):
    with path.open("rb") as handle:
        nt, nc = np.fromfile(handle, dtype=np.int32, count=2)
        time_day = np.fromfile(handle, dtype=np.float64, count=nt)
        injected_pv = np.fromfile(handle, dtype=np.float64, count=nt)
        sw = np.fromfile(handle, dtype=np.float32, count=nt * nc).reshape((nc, nt), order="F").T
        pressure_mpa = np.fromfile(handle, dtype=np.float32, count=nt * nc).reshape((nc, nt), order="F").T
    if nt < 2 or nc != NX * NY * NZ:
        raise ValueError(f"Unexpected history shape in {path}: {nt} time points, {nc} cells")
    return time_day, injected_pv, sw, pressure_mpa


def build_case(case):
    case_dir = RESULTS / case
    time_day, injected_pv, sw, pressure_mpa = read_history(case_dir / "state_history.bin")
    profile = np.loadtxt(case_dir / "permeability_md.csv", delimiter=",").reshape(-1)
    permeability_md = np.repeat(profile, NX * NY).astype(np.float32)
    np.savez_compressed(
        case_dir / "state_history.npz",
        time_day=time_day,
        injected_pv=injected_pv,
        Sw=sw,
        So=(1.0 - sw).astype(np.float32),
        pressure_mpa=pressure_mpa,
        permeability_md=permeability_md,
        porosity=np.full(NX * NY * NZ, POROSITY, dtype=np.float32),
        grid_shape=np.array((NX, NY, NZ), dtype=np.int32),
    )


if __name__ == "__main__":
    for case in CASES:
        build_case(case)
        print(f"Saved {case}/state_history.npz")
