"""Generate the complete static result-figure set from JutulDarcy CSV outputs."""
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures" / "results"
CASES = ["H-1", "P-2", "P-5", "P-10", "R-2", "R-5", "R-10", "C-2", "C-5", "C-10"]
GROUPS = {"Positive rhythm": ["P-2", "P-5", "P-10"],
          "Reverse rhythm": ["R-2", "R-5", "R-10"],
          "Compound rhythm": ["C-2", "C-5", "C-10"]}
COLORS = {"2": "#60a5fa", "5": "#f59e0b", "10": "#dc2626"}
OIL_CMAP = LinearSegmentedColormap.from_list("oil_rainbow", [
    "#d500ff", "#6500ff", "#005cff", "#00d8ff", "#00df42", "#fff000", "#ff8a00", "#f00000",
], N=256)


def save(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def summary(case):
    return np.genfromtxt(RESULTS / case / "summary.csv", delimiter=",", names=True)


def field(case, label="terminal"):
    return np.loadtxt(RESULTS / case / f"sw_{label}.csv", delimiter=",")


def profile(case):
    return np.loadtxt(RESULTS / case / "permeability_md.csv", delimiter=",")


def layer(case):
    return np.genfromtxt(RESULTS / case / "layer_results.csv", delimiter=",", names=True)


def draw_field(ax, array, title, value="Sw", cmap="Blues", vmin=0.2, vmax=0.8):
    image = ax.imshow(array, extent=(0, 500, 20, 0), aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set(title=title, xlabel="X (m)", ylabel="Depth (m)")
    return image


def figure_01_to_05():
    FIGURES.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "figures" / "model" / "conceptual_model_3d.png", FIGURES / "fig01_model_and_wells.png")
    sw = np.linspace(0.2, 0.8, 301)
    sn = (sw - 0.2)/0.6
    krw, kro = 0.3*sn**2, (1 - sn)**2
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(sw, krw, lw=2.5, label=r"$k_{rw}$")
    ax.plot(sw, kro, lw=2.5, label=r"$k_{ro}$")
    ax.set(xlabel=r"Water saturation $S_w$", ylabel="Relative permeability", ylim=(0, 1.05), title="Corey relative-permeability model")
    ax.grid(alpha=.25); ax.legend(); save(fig, "fig02_relative_permeability.png")

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for case, label in (("P-5", "Positive"), ("R-5", "Reverse"), ("C-5", "Compound")):
        ax.plot(profile(case), np.arange(.5, 20.5), lw=2.5, label=label)
    ax.invert_yaxis(); ax.set(xlabel="Horizontal permeability (mD)", ylabel="Depth (m)", title="Rhythm permeability profiles (contrast = 5)")
    ax.grid(alpha=.25); ax.legend(); save(fig, "fig03_rhythm_profiles_j5.png")

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for case in ("P-2", "P-5", "P-10"):
        ax.plot(profile(case), np.arange(.5, 20.5), lw=2.5, label=f"Contrast = {case.split('-')[1]}", color=COLORS[case.split('-')[1]])
    ax.invert_yaxis(); ax.set(xlabel="Horizontal permeability (mD)", ylabel="Depth (m)", title="Positive-rhythm permeability contrast")
    ax.grid(alpha=.25); ax.legend(); save(fig, "fig04_contrast_profiles.png")

    cases = [["P-2", "P-5", "P-10"], ["R-2", "R-5", "R-10"], ["C-2", "C-5", "C-10"]]
    fig, axes = plt.subplots(3, 3, figsize=(12, 8), sharex=True, sharey=True)
    for row, case_row in enumerate(cases):
        for col, case in enumerate(case_row):
            k = profile(case)
            im = axes[row, col].imshow(np.repeat(k[:, None], 50, axis=1), extent=(0, 500, 20, 0), aspect="auto", cmap="viridis", vmin=0, vmax=1000)
            axes[row, col].set_title(case)
    for ax in axes[-1, :]: ax.set_xlabel("X (m)")
    for ax in axes[:, 0]: ax.set_ylabel("Depth (m)")
    fig.colorbar(im, ax=axes, label="Horizontal permeability (mD)", shrink=.84)
    fig.suptitle("Nine rhythmic-reservoir permeability fields", y=1.01); save(fig, "fig05_permeability_matrix.png")


def figure_06_to_10():
    snapshots = [("0p1", "0.1 PV"), ("0p3", "0.3 PV"), ("0p5", "0.5 PV"), ("1p0", "1.0 PV")]
    for figure_no, case in ((6, "H-1"), (7, "P-5"), (8, "R-5"), (9, "C-5")):
        fig, axes = plt.subplots(1, 4, figsize=(15, 3.6), sharey=True)
        for ax, (label, title) in zip(axes, snapshots):
            im = draw_field(ax, field(case, label), title, vmin=.2, vmax=.8)
        fig.colorbar(im, ax=axes, label="Water saturation, Sw", shrink=.78)
        fig.suptitle(f"Waterflood evolution: {case}", y=1.03); save(fig, f"fig{figure_no:02d}_{case}_waterflood_evolution.png")

    cases = [["P-2", "P-5", "P-10"], ["R-2", "R-5", "R-10"], ["C-2", "C-5", "C-10"]]
    fig, axes = plt.subplots(3, 3, figsize=(12, 8), sharex=True, sharey=True)
    for row, case_row in enumerate(cases):
        for col, case in enumerate(case_row):
            im = draw_field(axes[row, col], 1 - field(case), f"{case}", value="So", cmap=OIL_CMAP, vmin=.2, vmax=.8)
            if row < 2:
                axes[row, col].set_xlabel("")
            if col > 0:
                axes[row, col].set_ylabel("")
    for ax in axes[-1, :]: ax.set_xlabel("X (m)")
    for ax in axes[:, 0]: ax.set_ylabel("Depth (m)")
    fig.colorbar(im, ax=axes, label="Oil saturation, So", shrink=.84)
    fig.suptitle("Terminal remaining-oil distribution at 2.0 injected PV", y=1.01)
    save(fig, "fig10_terminal_remaining_oil_matrix.png")


def figure_11_to_17():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for ax, (name, cases) in zip(axes, GROUPS.items()):
        for case in cases:
            s = summary(case); contrast = case.split("-")[1]
            ax.plot(s["injected_pv"], s["water_cut"], lw=2.2, label=f"J={contrast}", color=COLORS[contrast])
        ax.set(title=name, xlabel="Injected PV", ylim=(0, 1.02), xlim=(0, 2.01)); ax.grid(alpha=.25); ax.legend()
    axes[0].set_ylabel("Water cut")
    fig.suptitle("Water-cut response by rhythm and permeability contrast", y=1.03); save(fig, "fig11_water_cut_curves.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    for case in CASES:
        s = summary(case)
        style = "--" if case == "H-1" else "-"
        ax.plot(s["injected_pv"], s["recovery_factor"], lw=2, ls=style, label=case)
    ax.set(xlabel="Injected PV", ylabel="Recovery factor", xlim=(0, 2.01), title="Recovery-factor comparison")
    ax.grid(alpha=.25); ax.legend(ncol=2, fontsize=8); save(fig, "fig12_recovery_factor_curves.png")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for ax, (name, cases) in zip(axes, GROUPS.items()):
        for case in cases:
            s = summary(case); contrast = case.split("-")[1]
            ax.plot(s["injected_pv"], s["oil_rate_m3_day"], lw=2.2, label=f"J={contrast}", color=COLORS[contrast])
        ax.set(title=name, xlabel="Injected PV", xlim=(0, 2.01)); ax.grid(alpha=.25); ax.legend()
    axes[0].set_ylabel("Oil rate (m³/d)")
    fig.suptitle("Oil-rate response by rhythm and permeability contrast", y=1.03); save(fig, "fig13_oil_rate_curves.png")

    metrics = np.genfromtxt(RESULTS / "case_metrics.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    rhythmic = metrics[1:]
    labels = [item["case"] for item in rhythmic]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(labels, rhythmic["breakthrough_pv"], color=[COLORS[x.split("-")[1]] for x in labels])
    ax.set(ylabel="Breakthrough PV (fw ≥ 5%)", title="Water-breakthrough comparison"); ax.grid(axis="y", alpha=.25)
    save(fig, "fig14_breakthrough_pv.png")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(labels, rhythmic["terminal_RF"], color=[COLORS[x.split("-")[1]] for x in labels])
    ax.set(ylabel="Recovery factor at 2.0 PV", title="Terminal recovery-factor comparison"); ax.grid(axis="y", alpha=.25)
    save(fig, "fig15_terminal_recovery_factor.png")

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for case, color in (("P-10", "#2563eb"), ("R-10", "#dc2626"), ("C-10", "#7c3aed")):
        data = layer(case)
        ax.plot(data["avg_So"], data["depth_m"], lw=2.5, label=case, color=color)
    ax.invert_yaxis(); ax.set(xlabel="Average oil saturation, So", ylabel="Depth (m)", title="Layer-wise remaining oil at J=10")
    ax.grid(alpha=.25); ax.legend(); save(fig, "fig16_layer_remaining_oil.png")

    fig, axes = plt.subplots(1, 3, figsize=(12, 5), sharey=True)
    for ax, case in zip(axes, ("P-10", "R-10", "C-10")):
        data = layer(case)
        ax.plot(data["permeability_md"], data["depth_m"], color="#2563eb", lw=2.5, label="K")
        twin = ax.twiny(); twin.plot(data["avg_So"], data["depth_m"], color="#dc2626", lw=2.5, label="So")
        ax.invert_yaxis(); ax.set(title=case, xlabel="K (mD)")
        twin.set_xlabel("So")
        ax.grid(alpha=.25)
    axes[0].set_ylabel("Depth (m)")
    fig.suptitle("Permeability and remaining-oil correspondence at J=10", y=1.03); save(fig, "fig17_permeability_remaining_oil.png")


def figure_18_grid_sensitivity():
    data = np.genfromtxt(RESULTS / "grid_sensitivity.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    labels = [f"{row['nx']}×1×{row['nz']}" for row in data]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(labels, data["breakthrough_pv"], marker="o", lw=2.5, color="#2563eb")
    axes[0].set(ylabel="Breakthrough PV", title="P-5 water breakthrough"); axes[0].grid(alpha=.25)
    axes[1].plot(labels, data["terminal_recovery_factor"], marker="o", lw=2.5, color="#dc2626")
    axes[1].set(ylabel="Recovery factor at 2 PV", title="P-5 terminal recovery"); axes[1].grid(alpha=.25)
    fig.suptitle("Grid-sensitivity analysis", y=1.03); save(fig, "fig18_grid_sensitivity.png")


def cell_index(i, j, k):
    return (k - 1)*50*10 + (j - 1)*50 + (i - 1)


def add_quad(polygons, values, so, points, index):
    polygons.append(points)
    values.append(so[index])


def draw_3d_remaining_oil(ax, case, time_index=-1):
    with np.load(ROOT / "results_3d" / case / "state_history.npz") as history:
        so = history["So"][time_index]
    nx, ny, nz, lx, ly, lz = 50, 10, 20, 500.0, 100.0, 20.0
    dx, dy, dz = lx/nx, ly/ny, lz/nz
    polygons, values = [], []
    for i in range(1, nx + 1):
        for j in range(1, ny + 1):
            x0, x1, y0, y1 = (i - 1)*dx, i*dx, (j - 1)*dy, j*dy
            add_quad(polygons, values, so, [(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)], cell_index(i,j,1))
            add_quad(polygons, values, so, [(x0,y0,lz),(x0,y1,lz),(x1,y1,lz),(x1,y0,lz)], cell_index(i,j,nz))
    for i in range(1, nx + 1):
        for k in range(1, nz + 1):
            x0, x1, z0, z1 = (i - 1)*dx, i*dx, (k - 1)*dz, k*dz
            add_quad(polygons, values, so, [(x0,0,z0),(x1,0,z0),(x1,0,z1),(x0,0,z1)], cell_index(i,1,k))
            add_quad(polygons, values, so, [(x0,ly,z0),(x0,ly,z1),(x1,ly,z1),(x1,ly,z0)], cell_index(i,ny,k))
    for j in range(1, ny + 1):
        for k in range(1, nz + 1):
            y0, y1, z0, z1 = (j - 1)*dy, j*dy, (k - 1)*dz, k*dz
            add_quad(polygons, values, so, [(0,y0,z0),(0,y0,z1),(0,y1,z1),(0,y1,z0)], cell_index(1,j,k))
            add_quad(polygons, values, so, [(lx,y0,z0),(lx,y1,z0),(lx,y1,z1),(lx,y0,z1)], cell_index(nx,j,k))
    norm = Normalize(.2, .8)
    shell = Poly3DCollection(polygons, facecolors=OIL_CMAP(norm(values)), edgecolors="#2b1b1b", linewidths=.16)
    ax.add_collection3d(shell)
    ax.plot([5, 5], [50, 50], [-4, lz], color="#f08bbd", lw=5); ax.text(10, 50, -5, "Inj.", color="#d44e91")
    ax.plot([495, 495], [50, 50], [-4, lz], color="#62dfe8", lw=5); ax.text(462, 50, -5, "Prod.", color="#21b8c7")
    ax.set(xlim=(-15, lx + 15), ylim=(-8, ly + 8), zlim=(lz, -8), xlabel="X (m)", ylabel="Y (m)", zlabel="Depth (m)")
    ax.set_box_aspect((5, 1.25, .82)); ax.view_init(elev=24, azim=-56)
    ax.tick_params(labelsize=8)
    return ScalarMappable(norm=norm, cmap=OIL_CMAP)


def figure_19_to_22_3d_remaining_oil():
    for figure_no, case in ((19, "P-5"), (20, "R-5"), (21, "C-5")):
        fig = plt.figure(figsize=(10, 6.5)); ax = fig.add_subplot(projection="3d")
        mapper = draw_3d_remaining_oil(ax, case)
        fig.colorbar(mapper, ax=ax, shrink=.65, pad=.08, label="Oil saturation, So")
        ax.set_title(f"{case}: 3D terminal remaining-oil distribution\n(2001 days, 0.400 injected PV)")
        save(fig, f"fig{figure_no:02d}_{case}_terminal_3d_remaining_oil.png")

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.7), subplot_kw={"projection": "3d"})
    for ax, case in zip(axes, ("P-5", "R-5", "C-5")):
        mapper = draw_3d_remaining_oil(ax, case)
        ax.set_title(case)
    fig.colorbar(mapper, ax=axes, shrink=.66, pad=.05, label="Oil saturation, So")
    fig.suptitle("3D terminal remaining-oil comparison (contrast = 5, 2001 days)", y=.97)
    save(fig, "fig22_3d_terminal_remaining_oil_comparison.png")


def figure_23_to_25_3d_saturation_evolution():
    for figure_no, case in ((23, "P-5"), (24, "R-5"), (25, "C-5")):
        with np.load(ROOT / "results_3d" / case / "state_history.npz") as history:
            time_day, pvi = history["time_day"], history["injected_pv"]
        indices = [np.abs(pvi - target).argmin() for target in (0.0, 0.1, 0.2, 0.4)]
        fig, axes = plt.subplots(2, 2, figsize=(14, 9), subplot_kw={"projection": "3d"})
        for ax, index in zip(axes.flat, indices):
            mapper = draw_3d_remaining_oil(ax, case, index)
            ax.set_title(f"{time_day[index]:.0f} d · {pvi[index]:.3f} PV", fontsize=11)
        fig.colorbar(mapper, ax=axes, shrink=.67, pad=.04, label="Oil saturation, So")
        fig.suptitle(f"{case}: 3D oil-saturation evolution", y=.96)
        save(fig, f"fig{figure_no:02d}_{case}_3d_oil_saturation_evolution.png")


if __name__ == "__main__":
    figure_01_to_05()
    figure_06_to_10()
    figure_11_to_17()
    figure_18_grid_sensitivity()
    figure_19_to_22_3d_remaining_oil()
    figure_23_to_25_3d_saturation_evolution()
    print(FIGURES)
