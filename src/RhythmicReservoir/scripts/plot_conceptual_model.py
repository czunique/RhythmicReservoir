"""Render the geometry defined in config/conceptual_model.toml without a simulator."""
from pathlib import Path
import re

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "conceptual_model.toml"
OUTPUT = ROOT / "figures" / "model" / "conceptual_model_3d.png"


def read_numbers():
    text = CONFIG.read_text(encoding="utf-8")
    keys = ("nx", "ny", "nz", "length_x_m", "length_y_m", "length_z_m",
            "injector_i", "injector_j", "producer_i", "producer_j")
    values = {}
    for key in keys:
        match = re.search(rf"^{key}\s*=\s*([0-9.]+)", text, flags=re.MULTILINE)
        if not match:
            raise ValueError(f"Missing {key} in {CONFIG}")
        values[key] = float(match.group(1))
    return values


def add_grid(ax, nx, ny, nz, lx, ly, lz):
    lines = []
    for x in range(nx + 1):
        x_coord = x * lx / nx
        lines.extend([[(x_coord, 0, 0), (x_coord, 0, lz)],
                      [(x_coord, ly, 0), (x_coord, ly, lz)]])
    for z in range(nz + 1):
        z_coord = z * lz / nz
        lines.extend([[(0, 0, z_coord), (lx, 0, z_coord)],
                      [(0, ly, z_coord), (lx, ly, z_coord)]])
    for y in (0, ly):
        lines.extend([[(0, y, 0), (lx, y, 0)], [(0, y, lz), (lx, y, lz)],
                      [(0, y, 0), (0, y, lz)], [(lx, y, 0), (lx, y, lz)]])
    ax.add_collection3d(Line3DCollection(lines, colors="#94a3b8", linewidths=0.35, alpha=0.7))


def render_conceptual_model(show=True):
    """Save the conceptual-model figure and optionally display it in a window."""
    v = read_numbers()
    nx, ny, nz = int(v["nx"]), int(v["ny"]), int(v["nz"])
    lx, ly, lz = v["length_x_m"], v["length_y_m"], v["length_z_m"]

    fig = plt.figure(figsize=(13, 7.2), dpi=200)
    ax = fig.add_axes((0.03, 0.15, 0.94, 0.72), projection="3d")
    add_grid(ax, nx, ny, nz, lx, ly, lz)

    y_mid = ly / 2
    inj_x = (v["injector_i"] - 0.5) * lx / nx
    prod_x = (v["producer_i"] - 0.5) * lx / nx
    ax.plot([inj_x, inj_x], [y_mid, y_mid], [0, lz], color="#2563eb", lw=4, label="Injector (full completion)")
    ax.plot([prod_x, prod_x], [y_mid, y_mid], [0, lz], color="#dc2626", lw=4, label="Producer (full completion)")
    ax.quiver(inj_x + 10, y_mid, lz / 2, 1, 0, 0, length=lx - 35,
              normalize=True, color="#0f766e", arrow_length_ratio=0.025, lw=2.2)

    ax.text(inj_x, y_mid, -2.2, "Injector", color="#1d4ed8", ha="center", weight="bold")
    ax.text(prod_x, y_mid, -2.2, "Producer", color="#b91c1c", ha="center", weight="bold")
    ax.text(lx / 2, y_mid, lz + 2, "Water-drive direction", color="#0f766e", ha="center")
    ax.set(xlim=(0, lx), ylim=(0, ly), zlim=(lz, 0), xlabel="X (m)", ylabel="Y (m)", zlabel="Depth (m)")
    # The display aspect is deliberately compressed in X so that the thin
    # 500 × 20 × 20 m domain remains readable in a perspective figure.
    ax.set_box_aspect((5, 1, 1))
    ax.set_yticks((0, ly / 2, ly))
    ax.set_zticks((0, 5, 10, 15, lz))
    ax.view_init(elev=22, azim=-64)
    ax.set_title("3D conceptual reservoir model: 50 x 1 x 20 cells (500 m x 20 m x 20 m)", pad=10, weight="bold")
    ax.legend(loc="upper left")
    fig.text(0.5, 0.04, "Uniform baseline properties: porosity = 0.20; horizontal permeability = 500 mD; Kz/Kx = 0.10", ha="center", fontsize=10)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return OUTPUT


def main():
    print(render_conceptual_model(show=True))


if __name__ == "__main__":
    main()
