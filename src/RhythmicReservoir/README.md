# RhythmicReservoir

本目录保存作业 1 的自建模型代码，第三方 JutulDarcy 源码保持在相邻目录 `../JutulDarcy.jl`。

当前完成的是三维概念模型：`50 × 1 × 20` 个网格、物理尺寸 `500 × 20 × 20 m`，左端全层射开注水井，右端全层射开生产井。

通过主程序生成并在浏览器中打开可旋转、缩放、平移的三维模型：

```bash
.venv/bin/python main.py
```

交互图会离线保存至 `figures/model/conceptual_model_3d_interactive.html`；可直接双击该文件再次打开。

## 三维水驱方案与交互结果图

为展示不同韵律方案的三维剩余油分布，新增了独立的真三维水驱模型：`50 × 10 × 20` 个网格、物理尺寸 `500 × 100 × 20 m`。注水井和生产井位于横向中部，分别在模型左右端全层射开。二维剖面计算结果保留在 `results/`，三维计算结果独立保存到 `results_3d/`，不会相互覆盖。

在 JutulDarcy 的环境中重新计算九个韵律—级差方案：

```bash
JULIA_DEPOT_PATH=.julia_depot julia --project=../JutulDarcy.jl run_3d.jl
```

再生成离线交互图：

```bash
.venv/bin/python scripts/build_state_history.py
.venv/bin/python scripts/interactive_3d_results.py
```

每个方案的 `state_history.npz` 保存初始状态加 202 个数值时间步的完整单元属性：`Sw`、`So`、压力、渗透率、孔隙度、时间和累计注入 PV。图件为 `figures/results_3d/remaining_oil_3d_time_lapse.html`。使用下拉菜单切换 P-2、P-5、P-10、R-2、R-5、R-10、C-2、C-5、C-10；拖拽旋转、滚轮缩放，并用时间轴查看全部 203 个状态。单击“播放”可按实际时间步连续展示剩余油演化。

未来安装 Julia 后，可从 JutulDarcy 工作环境加载定义：

```julia
include("src/ConceptualModel.jl")
model = ConceptualModel.build_conceptual_model()
```
