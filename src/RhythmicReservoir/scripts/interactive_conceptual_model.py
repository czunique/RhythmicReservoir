"""Build an offline, interactive Plotly view of the conceptual reservoir model."""
from pathlib import Path
import re

import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "conceptual_model.toml"
OUTPUT = ROOT / "figures" / "model" / "conceptual_model_3d_interactive.html"


def read_numbers():
    text = CONFIG.read_text(encoding="utf-8")
    keys = ("nx", "ny", "nz", "length_x_m", "length_y_m", "length_z_m",
            "injector_i", "producer_i")
    values = {}
    for key in keys:
        match = re.search(rf"^{key}\s*=\s*([0-9.]+)", text, flags=re.MULTILINE)
        if not match:
            raise ValueError(f"Missing {key} in {CONFIG}")
        values[key] = float(match.group(1))
    return values


def grid_trace(nx, nz, lx, ly, lz):
    x, y, z = [], [], []
    for i in range(nx + 1):
        xi = i * lx / nx
        for yi in (0, ly):
            x.extend((xi, xi, None)); y.extend((yi, yi, None)); z.extend((0, lz, None))
    for k in range(nz + 1):
        zk = k * lz / nz
        for yi in (0, ly):
            x.extend((0, lx, None)); y.extend((yi, yi, None)); z.extend((zk, zk, None))
    return go.Scatter3d(x=x, y=y, z=z, mode="lines", hoverinfo="skip",
                        line=dict(color="#9aa8ba", width=2), name="Grid")


def reservoir_box(lx, ly, lz):
    x = [0, lx, lx, 0, 0, lx, lx, 0]
    y = [0, 0, ly, ly, 0, 0, ly, ly]
    z = [0, 0, 0, 0, lz, lz, lz, lz]
    return go.Mesh3d(
        x=x, y=y, z=z,
        i=[0, 0, 0, 7, 1, 2, 4, 4, 5, 3, 0, 1],
        j=[1, 2, 3, 4, 2, 3, 5, 6, 6, 7, 4, 5],
        k=[2, 3, 7, 5, 6, 6, 6, 7, 2, 0, 5, 6],
        color="#bfdbfe", opacity=0.16, hoverinfo="skip", name="Reservoir")


def well_trace(name, x, y, lz, color, role):
    return go.Scatter3d(
        x=[x, x], y=[y, y], z=[0, lz], mode="lines+text",
        text=[name, ""], textposition="top center",
        hovertemplate=(f"<b>{name}</b><br>{role}<br>Full completion: 20 layers"
                       "<br>X = %{x:.1f} m<br>Depth = %{z:.1f} m<extra></extra>"),
        line=dict(color=color, width=12), textfont=dict(color=color, size=15), name=name)


def render_interactive_conceptual_model(show=True):
    """Save one offline HTML figure; Plotly provides rotate, pan, zoom and hover."""
    v = read_numbers()
    nx, nz = int(v["nx"]), int(v["nz"])
    lx, ly, lz = v["length_x_m"], v["length_y_m"], v["length_z_m"]
    y_mid = ly / 2
    inj_x = (v["injector_i"] - 0.5) * lx / nx
    prod_x = (v["producer_i"] - 0.5) * lx / nx

    fig = go.Figure([
        reservoir_box(lx, ly, lz),
        grid_trace(nx, nz, lx, ly, lz),
        well_trace("Injector", inj_x, y_mid, lz, "#2563eb", "Water injector"),
        well_trace("Producer", prod_x, y_mid, lz, "#dc2626", "Oil producer"),
        go.Cone(x=[lx - 28], y=[y_mid], z=[lz / 2], u=[28], v=[0], w=[0],
                sizemode="absolute", sizeref=7, showscale=False, hoverinfo="skip",
                colorscale=[[0, "#0f766e"], [1, "#0f766e"]], name="Water-drive direction"),
    ])
    fig.update_layout(
        title="Interactive 3D conceptual reservoir model (50 × 1 × 20 cells)",
        template="plotly_white",
        margin=dict(l=0, r=0, t=56, b=0),
        legend=dict(x=0.01, y=0.99),
        annotations=[dict(text="Drag to rotate · Scroll to zoom · Shift + drag to pan · Hover wells for details",
                          x=0.5, y=0.01, xref="paper", yref="paper", showarrow=False)],
        scene=dict(
            xaxis=dict(title="X (m)", range=[0, lx]),
            yaxis=dict(title="Y (m)", range=[0, ly]),
            zaxis=dict(title="Depth (m)", range=[lz, 0]),
            aspectmode="manual", aspectratio=dict(x=8, y=1, z=1),
            camera=dict(eye=dict(x=1.55, y=-1.55, z=0.85)),
            dragmode="orbit",
        ),
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUTPUT, include_plotlyjs=True, full_html=True, auto_open=show)
    return OUTPUT
