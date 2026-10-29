# Animated time-series similarity methods / 时序相似性方法动图

137 individual explanations cover the existing 10 EchoTime report components and 127 imported atlas entries. Each has a GIF, static image, four calculation stages, limitations, primary definition links and a downloadable numerical trace.

覆盖现有 10 个 EchoTime 原生分项和 127 个方法条目。每项包含 GIF、静态图、四步说明、使用边界、定义来源以及示例输入与计算过程。

**Scope:** small deterministic teaching examples. `Checked against EchoTime` identifies actual implementation checks; `Reference-formula demonstration` specifies a mathematical variant; `Specified illustrative protocol` explains a concrete encoder/model choice. These examples do not implement all atlas methods as public APIs and provide no performance ranking.

**Read on the website:** [Methods Atlas](https://zipengwu.me/EchoTime/guide/methods.html#method-animations). The existing page offers search, English/Chinese text, and click-to-play controls; all animations are static until requested.

| Family / 类别 | Entries |
|---|---:|
| [EchoTime comparison layer / EchoTime 原生比较分项](native.md) | 10 |
| [Aligned, pointwise comparison / 逐点比较](lock-step.md) | 34 |
| [Shifts and lead–lag relationships / 平移与领先滞后](sliding.md) | 12 |
| [Elastic alignment and edit operations / 弹性对齐与编辑操作](elastic.md) | 24 |
| [Kernel constructions / 核函数构造](kernel.md) | 10 |
| [Explicit features / 显式特征](feature-based.md) | 18 |
| [Fitted dynamics and models / 动力学与模型](model-based.md) | 5 |
| [Representation and comparison / 表示与比较](embedding.md) | 24 |

## Reproduce and validate / 复现与验证

```bash
python -m pip install -e '.[dev,docs]'
python tools/build_method_animations.py
python tools/build_method_animations.py --check
echotime --export-pages docs
```

The renderer uses Pillow and the DejaVu fonts distributed with Matplotlib. Rendering needs only a CPU. Input traces retain the example parameters, intermediate matrices/vectors and output values. Runtime imports and website export use the prebuilt files, without plotting dependencies.

**Visual convention:** A is cyan and B is coral. Gold marks the active contribution, state or alignment path. Matrix blank cells are unavailable/uncomputed as described by the frame; matrix color scales can change as the visible range changes. Distances, divergences, correlations and kernels keep their own units and direction. A large score has no cross-method interpretation.

**中文阅读提示：** 青色为 A、珊瑚色为 B，金色标记当前贡献、状态或路径。矩阵空白格的含义见帧内说明；随着可见数值范围变化，矩阵色标可能调整。不同方法的数值单位和方向不同，不能直接横向比较分数大小。
