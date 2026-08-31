# RhythmicReservoir

本目录保存作业 1 的自建模型代码，第三方 JutulDarcy 源码保持在相邻目录 `../JutulDarcy.jl`。

当前完成的是三维概念模型：`50 × 1 × 20` 个网格、物理尺寸 `500 × 20 × 20 m`，左端全层射开注水井，右端全层射开生产井。

通过主程序生成并在浏览器中打开可旋转、缩放、平移的三维模型：

```bash
.venv/bin/python main.py
```

交互图会离线保存至 `figures/model/conceptual_model_3d_interactive.html`；可直接双击该文件再次打开。

未来安装 Julia 后，可从 JutulDarcy 工作环境加载定义：

```julia
include("src/ConceptualModel.jl")
model = ConceptualModel.build_conceptual_model()
```
