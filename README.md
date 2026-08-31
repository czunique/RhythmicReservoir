# 高等油藏工程作业 1：韵律性对剩余油分布的影响

本项目采用开源油藏数值模拟器 **JutulDarcy.jl**，研究正韵律、反韵律和复合韵律储层在水驱条件下的剩余油分布规律。项目包含可复现的模拟代码、全时间步状态数据、交互式三维结果页及报告插图。

原始建模方案见：[JutulDarcy_作业1_韵律性对剩余油分布_数值模拟方案.md](JutulDarcy_作业1_韵律性对剩余油分布_数值模拟方案.md)。

## 研究设计

- 韵律类型：正韵律（P）、反韵律（R）、复合韵律（C）
- 渗透率级差：2、5、10
- 对比组合：9 个韵律方案；另有 1 个均质对照方案用于二维基准比较
- 注采方式：左端全层注水井、右端全层生产井
- 初始条件：孔隙度 0.20，初始水饱和度 0.20，初始压力 20 MPa
- 相渗模型：Brooks–Corey 两相相对渗透率模型

二维基准模型为 `50 × 1 × 20` 网格、`500 × 20 × 20 m`；真三维水驱模型为 `50 × 10 × 20` 网格、`500 × 100 × 20 m`。

## 三维数值模拟结果

真三维模型每个方案计算 202 个时间步，时间步长为 `0.1 d`、`0.9 d` 和后续 200 个 `10 d` 步；连同初始状态，共保存 203 个状态，累计模拟 2001 天、注入 0.400 PV。

| 方案 | 级差 | 见水 PV（fw ≥ 5%） | 终采收率（2001 d） |
| --- | ---: | ---: | ---: |
| P-2 / R-2 | 2 | 0.286 | 0.529 |
| P-5 / R-5 | 5 | 0.232 | 0.481 |
| P-10 / R-10 | 10 | 0.214 | 0.459 |
| C-2 | 2 | 0.290 | 0.528 |
| C-5 | 5 | 0.234 | 0.479 |
| C-10 | 10 | 0.214 | 0.455 |

详细指标见 `src/RhythmicReservoir/results_3d/case_metrics.csv`。

## 目录说明

```text
.
├── JutulDarcy_作业1_韵律性对剩余油分布_数值模拟方案.md  # 作业建模方案
├── src/
│   ├── JutulDarcy.jl/                 # 官方 JutulDarcy 源码（Git 子模块）
│   └── RhythmicReservoir/             # 自建模型、求解与可视化代码
│       ├── run_all.jl                 # 二维基准方案批计算
│       ├── run_3d.jl                  # 九个真三维方案批计算
│       ├── results/                   # 二维结果
│       ├── results_3d/                # 三维结果与全时间步属性库
│       ├── figures/results/           # 25 张报告用 PNG 图
│       └── figures/results_3d/        # 三维交互播放页面
└── README.md                          # 本说明
```

## 查看结果

- 报告插图目录：`src/RhythmicReservoir/figures/results/`
- 三维剩余油时移播放页：`src/RhythmicReservoir/figures/results_3d/remaining_oil_3d_time_lapse.html`
- 每个方案的完整属性历史：`src/RhythmicReservoir/results_3d/<方案>/state_history.npz`

交互页支持方案选择、三维旋转缩放、203 个时间状态切换和自动播放。色标为紫—蓝—青—绿—黄—橙—红，表示由低到高的油饱和度。

## 复现命令

进入自建模型目录：

```bash
cd src/RhythmicReservoir
```

运行三维批量模拟：

```bash
JULIA_DEPOT_PATH=.julia_depot julia --project=../JutulDarcy.jl run_3d.jl
```

将每一步的状态转换为压缩属性库，并生成交互页：

```bash
.venv/bin/python scripts/build_state_history.py
.venv/bin/python scripts/interactive_3d_results.py
```

生成报告用静态图：

```bash
python3 scripts/plot_results.py
```

## 数据说明

`state_history.npz` 保存每个网格单元、每个时间状态的 `Sw`、`So`、压力、渗透率、孔隙度、时间和累计注入 PV。静态图和交互图均由这些 JutulDarcy 实际求解结果生成，不使用时间插值。
