"""Create an offline all-time-step 3D remaining-oil player from NPZ histories."""
import base64
import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results_3d"
OUTPUT = ROOT / "figures" / "results_3d" / "remaining_oil_3d_time_lapse.html"
CASES = ("P-2", "P-5", "P-10", "R-2", "R-5", "R-10", "C-2", "C-5", "C-10")
NX, NY, NZ = 50, 10, 20
LX, LY, LZ = 500.0, 100.0, 20.0
OIL_COLORSCALE = [
    [0.00, "#d500ff"], [0.16, "#6500ff"], [0.32, "#005cff"],
    [0.48, "#00d8ff"], [0.64, "#00df42"], [0.80, "#fff000"],
    [0.91, "#ff8a00"], [1.00, "#f00000"],
]


def cell_index(i, j, k):
    return (k - 1) * NX * NY + (j - 1) * NX + (i - 1)


def add_quad(vertices, triangles, cell_ids, points, cell_id):
    start = len(vertices)
    vertices.extend(points)
    triangles.extend(((start, start + 1, start + 2), (start, start + 2, start + 3)))
    cell_ids.append(cell_id)


def shell_geometry():
    vertices, triangles, cell_ids = [], [], []
    dx, dy, dz = LX / NX, LY / NY, LZ / NZ
    for i in range(1, NX + 1):
        for j in range(1, NY + 1):
            x0, x1, y0, y1 = (i - 1) * dx, i * dx, (j - 1) * dy, j * dy
            add_quad(vertices, triangles, cell_ids, ((x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)), cell_index(i, j, 1))
            add_quad(vertices, triangles, cell_ids, ((x0, y0, LZ), (x0, y1, LZ), (x1, y1, LZ), (x1, y0, LZ)), cell_index(i, j, NZ))
    for i in range(1, NX + 1):
        for k in range(1, NZ + 1):
            x0, x1, z0, z1 = (i - 1) * dx, i * dx, (k - 1) * dz, k * dz
            add_quad(vertices, triangles, cell_ids, ((x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)), cell_index(i, 1, k))
            add_quad(vertices, triangles, cell_ids, ((x0, LY, z0), (x0, LY, z1), (x1, LY, z1), (x1, LY, z0)), cell_index(i, NY, k))
    for j in range(1, NY + 1):
        for k in range(1, NZ + 1):
            y0, y1, z0, z1 = (j - 1) * dy, j * dy, (k - 1) * dz, k * dz
            add_quad(vertices, triangles, cell_ids, ((0, y0, z0), (0, y0, z1), (0, y1, z1), (0, y1, z0)), cell_index(1, j, k))
            add_quad(vertices, triangles, cell_ids, ((LX, y0, z0), (LX, y1, z0), (LX, y1, z1), (LX, y0, z1)), cell_index(NX, j, k))
    return np.asarray(vertices), np.asarray(triangles), np.asarray(cell_ids)


def add_segment(x, y, z, a, b):
    x.extend((a[0], b[0], None)); y.extend((a[1], b[1], None)); z.extend((a[2], b[2], None))


def grid_trace():
    x, y, z = [], [], []
    for i in range(NX + 1):
        xi = i * LX / NX
        add_segment(x, y, z, (xi, 0, 0), (xi, LY, 0)); add_segment(x, y, z, (xi, 0, 0), (xi, 0, LZ)); add_segment(x, y, z, (xi, LY, 0), (xi, LY, LZ))
    for j in range(NY + 1):
        yj = j * LY / NY
        add_segment(x, y, z, (0, yj, 0), (LX, yj, 0)); add_segment(x, y, z, (0, yj, 0), (0, yj, LZ)); add_segment(x, y, z, (LX, yj, 0), (LX, yj, LZ))
    for k in range(NZ + 1):
        zk = k * LZ / NZ
        add_segment(x, y, z, (0, 0, zk), (LX, 0, zk)); add_segment(x, y, z, (0, LY, zk), (LX, LY, zk))
        add_segment(x, y, z, (0, 0, zk), (0, LY, zk)); add_segment(x, y, z, (LX, 0, zk), (LX, LY, zk))
    return go.Scatter3d(x=x, y=y, z=z, mode="lines", hoverinfo="skip", showlegend=False, line=dict(color="#1f2937", width=2))


def well_trace(name, x, color):
    return go.Scatter3d(x=[x, x], y=[LY / 2, LY / 2], z=[-4, LZ], mode="lines+text", text=[name, ""], textposition="top center",
                        hoverinfo="skip", showlegend=False, line=dict(color=color, width=12), textfont=dict(color=color, size=17))


def palette():
    return [sample_colorscale(OIL_COLORSCALE, value / 255)[0] for value in range(256)]


def render():
    vertices, triangles, surface_cells = shell_geometry()
    colors = palette()
    histories, metadata = [], []
    for case in CASES:
        with np.load(RESULTS / case / "state_history.npz") as history:
            so = history["So"][:, surface_cells]
            codes = np.rint(np.clip((so - 0.2) / 0.6, 0, 1) * 255).astype(np.uint8)
            histories.append(codes)
            metadata.append({"time_day": history["time_day"].round(6).tolist(), "injected_pv": history["injected_pv"].round(6).tolist()})
    values = np.stack(histories)
    initial_colors = [colors[value] for value in values[0, 0] for _ in (0, 1)]
    mesh = go.Mesh3d(x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2], i=triangles[:, 0], j=triangles[:, 1], k=triangles[:, 2],
                     facecolor=initial_colors, flatshading=True, hoverinfo="skip", lighting=dict(ambient=1.0, diffuse=0.0, specular=0.0, roughness=1.0))
    colorbar = go.Scatter3d(x=[None, None], y=[None, None], z=[None, None], mode="markers", hoverinfo="skip", showlegend=False,
                            marker=dict(color=[0.2, 0.8], colorscale=OIL_COLORSCALE, cmin=0.2, cmax=0.8, showscale=True,
                                        colorbar=dict(title="Oil saturation, So", len=0.72, thickness=22)))
    fig = go.Figure([colorbar, mesh, grid_trace(), well_trace("Injector", LX / NX / 2, "#f08bbd"), well_trace("Producer", LX - LX / NX / 2, "#62dfe8")])
    fig.update_layout(title="三维剩余油饱和度：P-2 · 0.0 d · 0.000 PV", template="plotly_white", margin=dict(l=0, r=0, t=52, b=0),
                      scene=dict(xaxis=dict(title="X (m)", range=[0, LX]), yaxis=dict(title="Y (m)", range=[0, LY]),
                                 zaxis=dict(title="Depth (m)", range=[LZ, -5]), aspectmode="manual", aspectratio=dict(x=5, y=1.35, z=0.62),
                                 camera=dict(eye=dict(x=1.55, y=-1.7, z=0.8)), dragmode="orbit"))
    chart = fig.to_html(include_plotlyjs=True, full_html=False, div_id="reservoir-view")
    encoded = base64.b64encode(values.tobytes()).decode("ascii")
    options = "".join(f'<option value="{case}">{case}</option>' for case in CASES)
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>三维剩余油饱和度时移图</title>
<style>body{{margin:0;font-family:Arial,"Microsoft YaHei",sans-serif;color:#17345d}}#controls{{display:flex;align-items:center;gap:16px;padding:12px 18px 2px}}label{{font-weight:600}}select,button{{font:inherit;padding:6px 10px;border:1px solid #7185a2;border-radius:4px;color:#17345d;background:#fff}}button{{background:#285ea8;color:#fff;border-color:#285ea8;cursor:pointer}}input{{width:360px;accent-color:#285ea8}}#time-label{{min-width:150px;font-weight:600}}#reservoir-view{{width:100vw;height:calc(100vh - 66px)}}</style></head><body>
<div id="controls"><label>方案 <select id="case-select">{options}</select></label><button id="play-button">▶ 播放</button><label>时间轴 <input id="time-slider" type="range" min="0" max="{values.shape[1] - 1}" step="1" value="0"></label><span id="time-label"></span></div>{chart}
<script>const cases={json.dumps(CASES)}, meta={json.dumps(metadata)}, palette={json.dumps(colors)}, steps={values.shape[1]}, faces={values.shape[2]}, encoded="{encoded}", bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0)), plot=document.getElementById("reservoir-view"), select=document.getElementById("case-select"), slider=document.getElementById("time-slider"), label=document.getElementById("time-label"), button=document.getElementById("play-button");let timer=null;
function colorsFor(ci,ti){{const offset=(ci*steps+ti)*faces, faceColors=new Array(faces*2);for(let q=0;q<faces;q++){{const c=palette[bytes[offset+q]];faceColors[2*q]=c;faceColors[2*q+1]=c;}}return faceColors;}}
function update(){{const ci=cases.indexOf(select.value),ti=Number(slider.value),m=meta[ci],text=`${{m.time_day[ti].toFixed(1)}} d · ${{m.injected_pv[ti].toFixed(3)}} PV`;label.textContent=text;Plotly.restyle(plot,{{facecolor:[colorsFor(ci,ti)]}},[1]);Plotly.relayout(plot,{{title:`三维剩余油饱和度：${{select.value}} · ${{text}}`}});}}
function stop(){{if(timer){{clearInterval(timer);timer=null;button.textContent="▶ 播放";}}}}
function play(){{if(timer){{stop();return;}}if(Number(slider.value)>=steps-1)slider.value=0;button.textContent="❚❚ 暂停";timer=setInterval(()=>{{if(Number(slider.value)>=steps-1){{stop();return;}}slider.value=Number(slider.value)+1;update();}},260);}}
select.addEventListener("change",()=>{{stop();update();}});slider.addEventListener("input",()=>{{stop();update();}});button.addEventListener("click",play);update();</script></body></html>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    render()
