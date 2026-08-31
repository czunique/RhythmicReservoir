"""Replot the 17 report figures directly from the saved simulation outputs.

The Word report is treated only as a figure list and a presentation reference.
All numerical curves and fields below are rebuilt from ``results/`` and
``results_3d/`` so the PNG files can be used as traceable, publication-style
figures without relying on pasted Word images.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS_2D = ROOT / "results"
RESULTS_3D = ROOT / "results_3d"
OUT = ROOT / "figures" / "results"

RHYTHM_CASES = {
    "Positive rhythm": ("P-2", "P-5", "P-10"),
    "Reverse rhythm": ("R-2", "R-5", "R-10"),
    "Compound rhythm": ("C-2", "C-5", "C-10"),
}
CONTRASTS = ("2", "5", "10")
CONTRAST_COLORS = {"2": "#2563eb", "5": "#f59e0b", "10": "#dc2626"}
RHYTHM_COLORS = {
    "Positive rhythm": "#2563eb",
    "Reverse rhythm": "#ef7d32",
    "Compound rhythm": "#2ca25f",
}
OIL_CMAP = LinearSegmentedColormap.from_list(
    "oil_rainbow",
    ["#d500ff", "#6500ff", "#005cff", "#00d8ff", "#00df42", "#fff000", "#ff8a00", "#f00000"],
    N=256,
)


def configure_style():
    """Use conservative scientific-plot defaults that render on any machine."""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 10,
        "axes.titlesize": 10.5,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": "#d8dee9",
        "grid.linewidth": 0.55,
        "grid.alpha": 0.8,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
    })


def save(fig, basename):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / basename
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def data_2d(case, filename):
    return np.genfromtxt(RESULTS_2D / case / filename, delimiter=",", names=True)


def data_3d(case, filename):
    return np.genfromtxt(RESULTS_3D / case / filename, delimiter=",", names=True)


def profile(root, case):
    return np.loadtxt(root / case / "permeability_md.csv", delimiter=",")


def layer(root, case):
    return np.genfromtxt(root / case / "layer_results.csv", delimiter=",", names=True)


def metrics(root):
    return np.genfromtxt(root / "case_metrics.csv", delimiter=",", names=True,
                         dtype=None, encoding="utf-8")


def set_depth_axis(ax):
    ax.set_ylim(20.5, -0.5)
    ax.set_yticks((0, 5, 10, 15, 20))
    ax.set_ylabel("Depth (m)")


def annotate_panels(axes):
    for label, ax in zip("abc", np.ravel(axes)):
        ax.text(0.015, 0.985, f"({label})", transform=ax.transAxes,
                ha="left", va="top", fontsize=10, fontweight="bold")


def figure_01_workflow():
    fig, ax = plt.subplots(figsize=(11.5, 3.0), layout="constrained")
    ax.set_axis_off()
    labels = [
        "Unified grid and\nfluid model",
        "Rhythm profiles\n(P / R / C; J = 2, 5, 10)",
        "JutulDarcy\nwaterflood simulation",
        "Saved state and\nproduction histories",
        "Python post-processing\nand comparison",
    ]
    x_positions = np.linspace(0.11, 0.89, len(labels))
    for i, (x, label) in enumerate(zip(x_positions, labels)):
        ax.text(x, 0.52, label, transform=ax.transAxes, ha="center", va="center",
                fontsize=10, linespacing=1.35,
                bbox={"boxstyle": "round,pad=0.55", "fc": "#f8fafc", "ec": "#3b82f6", "lw": 1.3})
        if i < len(labels) - 1:
            ax.annotate("", xy=(x_positions[i + 1] - 0.095, 0.52), xytext=(x + 0.095, 0.52),
                        xycoords=ax.transAxes, textcoords=ax.transAxes,
                        arrowprops={"arrowstyle": "->", "lw": 1.5, "color": "#64748b"})
    ax.text(0.5, 0.12, "Same geometry, rock/fluid properties, and well controls for every case",
            transform=ax.transAxes, ha="center", color="#475569", fontsize=9.5)
    return save(fig, "report_fig01_workflow.png")


def figure_02_relative_permeability():
    sw = np.linspace(0.20, 0.80, 401)
    swe = (sw - 0.20) / 0.60
    krw, kro = 0.30 * swe**2, (1.0 - swe)**2
    fig, ax = plt.subplots(figsize=(6.4, 4.6), layout="constrained")
    ax.plot(sw, krw, color="#1677c8", lw=2.3, label=r"$k_{rw}$ (water)")
    ax.plot(sw, kro, color="#d34f3d", lw=2.3, ls="--", label=r"$k_{ro}$ (oil)")
    ax.axvline(0.20, color="#64748b", lw=0.8, ls=":")
    ax.axvline(0.80, color="#64748b", lw=0.8, ls=":")
    ax.set(xlim=(0.18, 0.82), ylim=(0, 1.04), xlabel=r"Water saturation, $S_w$",
           ylabel="Relative permeability")
    ax.legend(loc="center right")
    return save(fig, "report_fig02_relative_permeability.png")


def figure_03_2d_model():
    nx, nz, lx, lz = 50, 20, 500.0, 20.0
    fig, ax = plt.subplots(figsize=(10.5, 3.7), layout="constrained")
    for x in np.linspace(0, lx, nx + 1):
        ax.plot((x, x), (0, lz), color="#cbd5e1", lw=0.35, zorder=1)
    for z in np.linspace(0, lz, nz + 1):
        ax.plot((0, lx), (z, z), color="#cbd5e1", lw=0.35, zorder=1)
    ax.add_patch(plt.Rectangle((0, 0), lx, lz, fill=False, ec="#334155", lw=1.2, zorder=2))
    ax.plot((5, 5), (0, lz), color="#d64c8b", lw=5.5, solid_capstyle="round", zorder=3)
    ax.plot((495, 495), (0, lz), color="#1ba9b5", lw=5.5, solid_capstyle="round", zorder=3)
    ax.annotate("Injector\nfull completion", xy=(5, 10), xytext=(45, -3.8), ha="left", va="top",
                arrowprops={"arrowstyle": "-", "color": "#d64c8b"}, color="#b42468", fontsize=9)
    ax.annotate("Producer\nfull completion", xy=(495, 10), xytext=(455, -3.8), ha="right", va="top",
                arrowprops={"arrowstyle": "-", "color": "#1ba9b5"}, color="#0f8994", fontsize=9)
    ax.annotate("Water-drive direction", xy=(400, 10), xytext=(105, 10), va="center", ha="center",
                arrowprops={"arrowstyle": "->", "color": "#475569", "lw": 1.4}, color="#475569")
    # Do not force a 1:1 aspect ratio: the 500 m by 20 m model would leave a
    # large blank area and make the annotations unnecessarily small.
    ax.set(xlim=(-15, 515), ylim=(22, -5), xlabel="X (m)", ylabel="Depth (m)")
    ax.set_yticks((0, 5, 10, 15, 20))
    return save(fig, "report_fig03_2d_model_and_wells.png")


def figure_04_profiles():
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), sharey=True, layout="constrained")
    for ax, contrast in zip(axes, CONTRASTS):
        for name, prefix in (("Positive rhythm", "P"), ("Reverse rhythm", "R"), ("Compound rhythm", "C")):
            ax.plot(profile(RESULTS_2D, f"{prefix}-{contrast}"), np.arange(0.5, 20.5),
                    color=RHYTHM_COLORS[name], lw=2.1, label=name.replace(" rhythm", ""))
        ax.set_title(f"Nominal contrast J = {contrast}")
        ax.set_xlabel("Horizontal permeability (mD)")
        ax.set_xlim(50, 1000)
        set_depth_axis(ax)
    axes[0].legend(loc="lower right")
    annotate_panels(axes)
    return save(fig, "report_fig04_rhythm_permeability_profiles.png")


def figure_05_permeability_fields():
    case_rows = (("P-2", "P-5", "P-10"), ("R-2", "R-5", "R-10"), ("C-2", "C-5", "C-10"))
    fig, axes = plt.subplots(3, 3, figsize=(11.2, 7.8), sharex=True, sharey=True, layout="constrained")
    for row, case_row in enumerate(case_rows):
        for col, case in enumerate(case_row):
            field = np.repeat(profile(RESULTS_2D, case)[:, None], 50, axis=1)
            image = axes[row, col].imshow(field, extent=(0, 500, 20, 0), aspect="auto",
                                          cmap="viridis", vmin=0, vmax=1000)
            axes[row, col].set_title(case)
    for ax in axes[-1, :]:
        ax.set_xlabel("X (m)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Depth (m)")
    colorbar = fig.colorbar(image, ax=axes, shrink=0.92, pad=0.02)
    colorbar.set_label("Horizontal permeability (mD)")
    return save(fig, "report_fig05_nine_permeability_fields.png")


def plot_breakthrough_and_terminal(ax_left, ax_right, rhythm_name):
    rows = {str(int(row["contrast"])): row for row in metrics(RESULTS_2D)
            if row["rhythm"] == rhythm_name.lower().split()[0]}
    xs = np.array([float(value) for value in CONTRASTS])
    breakthrough = [rows[value]["breakthrough_pv"] for value in CONTRASTS]
    terminal = [100 * rows[value]["terminal_RF"] for value in CONTRASTS]
    ax_left.plot(xs, breakthrough, marker="o", ms=5, lw=2.0, color="#2563eb")
    ax_left.axhline(metrics(RESULTS_2D)[0]["breakthrough_pv"], color="#2563eb", lw=1.0, ls=":")
    ax_left.set(xlabel="Nominal permeability contrast, J", ylabel="Breakthrough (PVI)",
                xlim=(1.5, 10.5), xticks=xs)
    ax_right.plot(xs, terminal, marker="o", ms=5, lw=2.0, color="#d64c3b")
    ax_right.axhline(100 * metrics(RESULTS_2D)[0]["terminal_RF"], color="#d64c3b", lw=1.0, ls=":")
    ax_right.set(xlabel="Nominal permeability contrast, J", ylabel="Terminal recovery factor (%)",
                 xlim=(1.5, 10.5), xticks=xs)


def figure_group_metrics(number, rhythm_name):
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 3.8), layout="constrained")
    plot_breakthrough_and_terminal(*axes, rhythm_name)
    axes[0].set_title("Water breakthrough")
    axes[1].set_title("Recovery at 2.001 PVI")
    annotate_panels(axes)
    slug = rhythm_name.lower().replace(" ", "_")
    return save(fig, f"report_fig{number:02d}_{slug}_breakthrough_recovery.png")


def figure_07_positive_watercut_recovery():
    targets = (0.05, 0.80, 0.90)
    fig, ax = plt.subplots(figsize=(7.4, 4.8), layout="constrained")
    for case in RHYTHM_CASES["Positive rhythm"]:
        summary = data_2d(case, "summary.csv")
        values = []
        for target in targets:
            index = np.flatnonzero(summary["water_cut"] >= target)[0]
            values.append(100 * summary["recovery_factor"][index])
        contrast = case.split("-")[1]
        ax.plot((5, 80, 90), values, marker="o", ms=5, lw=2.1,
                color=CONTRAST_COLORS[contrast], label=f"J = {contrast}")
    ax.set(xlabel="Water cut (%)", ylabel="Recovery factor (%)", xlim=(0, 95), xticks=(5, 80, 90))
    ax.legend(title="Positive rhythm", loc="best")
    return save(fig, "report_fig07_positive_recovery_at_watercut.png")


def figure_layer_oil(number, rhythm_name):
    prefix = {"Positive rhythm": "P", "Reverse rhythm": "R", "Compound rhythm": "C"}[rhythm_name]
    fig, ax = plt.subplots(figsize=(6.8, 5.0), layout="constrained")
    for contrast in CONTRASTS:
        values = layer(RESULTS_2D, f"{prefix}-{contrast}")
        ax.plot(values["avg_So"], values["depth_m"], marker="o", ms=2.7, lw=2.0,
                color=CONTRAST_COLORS[contrast], label=f"J = {contrast}")
    set_depth_axis(ax)
    ax.set(xlabel=r"Layer-averaged oil saturation, $S_o$", xlim=(0.22, 0.65))
    ax.legend(title=rhythm_name)
    return save(fig, f"report_fig{number:02d}_{rhythm_name.lower().replace(' ', '_')}_layer_oil_saturation.png")


def figure_13_comparison():
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5), layout="constrained")
    values = metrics(RESULTS_2D)
    x = np.asarray((2, 5, 10), dtype=float)
    for name in RHYTHM_CASES:
        subset = [row for row in values if row["rhythm"] == name.lower().split()[0]]
        subset.sort(key=lambda row: row["contrast"])
        axes[0].plot(x, [row["breakthrough_pv"] for row in subset], marker="o", lw=1.9,
                     color=RHYTHM_COLORS[name], label=name.replace(" rhythm", ""))
        axes[1].plot(x, [100 * row["terminal_RF"] for row in subset], marker="o", lw=1.9,
                     color=RHYTHM_COLORS[name])
    for name, prefix in (("Positive rhythm", "P"), ("Reverse rhythm", "R"), ("Compound rhythm", "C")):
        values_j10 = layer(RESULTS_2D, f"{prefix}-10")
        axes[2].plot(values_j10["avg_So"], values_j10["depth_m"], lw=2.0,
                     color=RHYTHM_COLORS[name], label=name.replace(" rhythm", ""))
    axes[0].set(xlabel="Nominal contrast, J", ylabel="Breakthrough (PVI)", xticks=x)
    axes[1].set(xlabel="Nominal contrast, J", ylabel="Terminal recovery factor (%)", xticks=x)
    axes[2].set(xlabel=r"Layer-averaged $S_o$ at J = 10")
    set_depth_axis(axes[2])
    axes[0].legend(loc="best")
    axes[2].legend(loc="lower right")
    annotate_panels(axes)
    return save(fig, "report_fig13_rhythm_comparison.png")


def figure_14_grid_sensitivity():
    data = np.genfromtxt(RESULTS_2D / "grid_sensitivity.csv", delimiter=",", names=True)
    labels = [f"{row['nx']} x 1 x {row['nz']}" for row in data]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.7), layout="constrained")
    axes[0].plot(labels, data["breakthrough_pv"], marker="o", ms=5, lw=2.0, color="#2563eb")
    axes[0].set(ylabel="Breakthrough (PVI)", title="P-5 water breakthrough")
    axes[1].plot(labels, 100 * data["terminal_recovery_factor"], marker="o", ms=5, lw=2.0, color="#d64c3b")
    axes[1].set(ylabel="Terminal recovery factor (%)", title="P-5 recovery at 2.001 PVI")
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=15)
    annotate_panels(axes)
    return save(fig, "report_fig14_grid_sensitivity.png")


def figure_15_3d_model():
    nx, ny, nz, lx, ly, lz = 50, 10, 20, 500.0, 100.0, 20.0
    lines = []
    for x in np.linspace(0, lx, nx + 1):
        lines.extend([[(x, 0, 0), (x, 0, lz)], [(x, ly, 0), (x, ly, lz)]])
    for z in np.linspace(0, lz, nz + 1):
        lines.extend([[(0, 0, z), (lx, 0, z)], [(0, ly, z), (lx, ly, z)]])
    for y in (0, ly):
        lines.extend([[(0, y, 0), (lx, y, 0)], [(0, y, lz), (lx, y, lz)],
                      [(0, y, 0), (0, y, lz)], [(lx, y, 0), (lx, y, lz)]])
    # Use an explicit axes rectangle: constrained_layout gives a switched-off
    # 3-D axis an unnecessarily large empty margin.
    fig = plt.figure(figsize=(10.8, 4.8))
    ax = fig.add_axes((0.03, 0.12, 0.94, 0.79), projection="3d")
    ax.add_collection3d(Line3DCollection(lines, colors="#9aa6b2", linewidths=0.35, alpha=0.72))
    ax.plot((5, 5), (50, 50), (0, lz), color="#d64c8b", lw=4.8, label="Injector")
    ax.plot((495, 495), (50, 50), (0, lz), color="#25aebb", lw=4.8, label="Producer")
    # Suppress crowded Matplotlib 3-D axis labels.  The dimensional caption
    # below is more legible in a report and avoids the Y/Z label collision
    # that occurs for a thin 500 x 100 x 20 m domain.
    ax.set(xlim=(0, lx), ylim=(0, ly), zlim=(lz, 0))
    ax.set_box_aspect((5.0, 1.2, 0.72))
    ax.view_init(elev=22, azim=-58)
    ax.set_axis_off()
    ax.legend(loc="upper left")
    fig.text(0.5, 0.045, "3D supplementary model: 50 x 10 x 20 cells; 500 m x 100 m x 20 m",
             ha="center", va="center", color="#334155", fontsize=10)
    return save(fig, "report_fig15_3d_model_and_wells.png")


def figure_16_3d_breakthrough():
    values = metrics(RESULTS_3D)
    fig, ax = plt.subplots(figsize=(7.6, 4.8), layout="constrained")
    x = np.asarray((2, 5, 10), dtype=float)
    for name in RHYTHM_CASES:
        subset = [row for row in values if row["rhythm"] == name.lower().split()[0]]
        subset.sort(key=lambda row: row["contrast"])
        ax.plot(x, [row["breakthrough_pv"] for row in subset], marker="o", ms=5, lw=2.1,
                color=RHYTHM_COLORS[name], label=name.replace(" rhythm", ""))
    ax.set(xlabel="Nominal permeability contrast, J", ylabel="Breakthrough (PVI)",
           xlim=(1.5, 10.5), xticks=x)
    ax.legend(loc="best")
    return save(fig, "report_fig16_3d_breakthrough.png")


def figure_17_3d_layer_oil():
    fig, ax = plt.subplots(figsize=(7.1, 5.1), layout="constrained")
    for name, case in (("Positive rhythm", "P-5"), ("Reverse rhythm", "R-5"), ("Compound rhythm", "C-5")):
        values = layer(RESULTS_3D, case)
        ax.plot(values["avg_So"], values["depth_m"], marker="o", ms=2.6, lw=2.1,
                color=RHYTHM_COLORS[name], label=name.replace(" rhythm", ""))
    set_depth_axis(ax)
    ax.set(xlabel=r"Layer-averaged oil saturation, $S_o$ at 2001 d", xlim=(0.32, 0.76))
    ax.legend(loc="best")
    return save(fig, "report_fig17_3d_layer_oil_saturation_j5.png")


def main():
    configure_style()
    outputs = [
        figure_01_workflow(), figure_02_relative_permeability(), figure_03_2d_model(),
        figure_04_profiles(), figure_05_permeability_fields(),
        figure_group_metrics(6, "Positive rhythm"), figure_07_positive_watercut_recovery(),
        figure_layer_oil(8, "Positive rhythm"), figure_group_metrics(9, "Reverse rhythm"),
        figure_layer_oil(10, "Reverse rhythm"), figure_group_metrics(11, "Compound rhythm"),
        figure_layer_oil(12, "Compound rhythm"), figure_13_comparison(), figure_14_grid_sensitivity(),
        figure_15_3d_model(), figure_16_3d_breakthrough(), figure_17_3d_layer_oil(),
    ]
    print("\n".join(str(path) for path in outputs))


if __name__ == "__main__":
    main()
