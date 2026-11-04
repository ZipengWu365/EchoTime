# EchoTime 加速执行计划（合并版 v2）

状态：待 Zipeng 确认后开工
日期：2026-11-04
适用源码：https://github.com/ZipengWu365/EchoTime ，提交 `08f7df7`（`main`，版本号 `0.18.0.dev0`）
本文件取代 v1，由三份方案合并而成。

| 标记 | 来源 | 用法 |
|---|---|---|
| [R] | 研究路线图 `EchoTime_Extreme_Acceleration_Research_Plan_2026-11-04.md`（82 条）。**未入库**，需要时从本地拷到服务器 | 总图。条目编号 FP/BD/EX/SY/AP/Q 沿用它的编号，推导和文献回它查 |
| [S] | v1 的 SearchIndex 方案 | batch 指标的逐一下界推导、API、测试设计 |
| [W] | 第三方加速白皮书。**未入库** | 只采纳标明的几条，全部按 EchoTime 现有定义改写过 |

[R] 中对源码的说法本次抽查了四处（`setdefault` 的行号、`-march=x86-64-v3`、`kLanes = 8`、performance.md 的数字），全部属实。

---

## 0. 读法

- 每条措施后面标来源，如 [R:FP04]。
- 精度等级（[R] 1.2 节）：
  - **A** 逐位一致：和现有程序的输出每一位都相同。
  - **B** 数值一致：同一个数学定义，误差在声明范围内（通常 1e-12 量级），边界情况回退到原路径。
  - **C** 检索结果有证书：返回的 top-k 或阈值结果正确，但没有算出每个候选的距离。
  - **D** 近似：结果可能漏，必须报告召回率。
- 每个阶段做完提交一次并汇报，等确认再进下一阶段。写着"等 Zipeng 确认"的地方先停。

---

## 1. 目标与边界

### 1.1 对"能不能像 FAISS 一样快"的回答

两条路，按每次查询的 `mode` 选，不混用：

| | certified（默认） | approximate |
|---|---|---|
| 做法 | 下界 + 提前停止 + 综合分数上界 | FAISS / 二值码 / 多视角粗筛，再用原版精排 |
| 结果 | 和逐条计算完全相同 | 可能漏，每次报告 CandidateRecall@k 的估计 |
| 速度 | 由数据决定：区分度高时只算少数候选；最坏退化为逐条，但不出错 | 固定，和 FAISS 同量级 |
| 精度等级 | C | D |

没有第三种。声称"又精确又恒定 FAISS 速度"的方案，都在某处换掉了定义。

### 1.2 六种工作负载（[R] 1.1 节，裁剪）

| 工作负载 | 主要成本 | 本计划对应 |
|---|---|---|
| 一对序列的完整报告 `compare_series` | 重复的特征计算、报告字符串、对象构造 | P1 |
| 一个查询对很多候选 | 候选距离、排序 | P2、P3 |
| 全部成对矩阵 | 二次输出、内核吞吐 | P1（去重复）、P4 |
| 多通道 profile | 同一谱重复计算 | P1 |
| 滑动窗口 | 相邻窗口重复 | P1 |
| 静态大库长期检索 | 建索引、常驻特征 | P2、P3 |

### 1.3 不做的事

- 不改任何距离、分量、权重的定义。换定义是另一个产品决策，不叫加速。
- Q01–Q04（量子）、SY19（FPGA）、SY20（浏览器）不做。量子的原因见第 12 节。
- 核心包不加必需依赖；`faiss-cpu` 为可选依赖。
- 不合并到 `main`、不发布到 PyPI，直到 Zipeng 确认。

---

## 2. 现状（已核对）

### 2.1 仓库

- 写本文时本地副本与 GitHub `main` 相同（`08f7df7`），工作区干净。
- 本地是部分检出（62% 文件），缺 `native/`、`setup.py`、`benchmarks/`。开工前先 `git sparse-checkout disable`。
- PyPI 是 `0.17.1`（2026-05-14），纯 Python，不含 C++ 内核。

### 2.2 已有基础（保留，不重做）

| 能力 | 位置 | 含义 |
|---|---|---|
| DTW、LCSS、EDR、ERP、TWED 的 C++ 内核，FP64，无 fast-math，关闭 FMA 收缩 | `native/echotime_native.cpp`，`setup.py` | 和 Python 参考逐位一致，新代码必须沿用 |
| 等长单变量序列按 `kLanes = 8` 对一组向量化 | 同上 | 下一步是多变量和运行时分派 |
| 按序列对多线程，释放 GIL | `parallel_for` | 每次调用新建线程，见 SY03 |
| 批量 NCC 每条序列一次 FFT，每对一次逆 FFT，再精算 lag | `batch.py` | 跨调用复用还没有 |
| 多种 embedding 调用内缓存 | `batch.py` | 跨调用、跨指标没有 |
| Linux x86 默认 `-march=x86-64-v3` | `setup.py` | 服务器若是 x86 会用到 AVX2；M4 走 NEON |

### 2.3 已核对的具体低效点

| 位置 | 问题 | 对应条目 |
|---|---|---|
| `batch.py:294`、`batch.py:482` | `setdefault(k, f(k))` 先执行 `f` 再查键，缓存命中也在重算 | FP04 |
| `similarity.py` `_best_lag_corr` | 每对序列 49 次 `np.corrcoef` | FP08 |
| `similarity.py` `rolling_similarity` | 每个窗口重采样到 128 点再跑完整 `compare_series`，只用其中 10 列 | FP01、EX13 |
| `similarity.py` `compare_series` | 每次都拼 notes、suggestions、interpretation 字符串 | FP01 |
| `metrics.py` 多个指标各自重算同一条序列的归一化谱 | [R] 核查，本次未复核 | FP02 |
| 弹性距离内核 | 没有 cutoff，无法提前放弃 | EX01 |
| 整个包 | 没有索引、没有下界，一次查询 = N 次精确距离 | P2 |

### 2.4 现有耗时（performance.md，BlueBEAR Ice Lake，32 核，真实 fMRI 数据）

| 工作负载 | 当前 |
|---|---:|
| 290 点单对 `compare_series` | 8.0 ms |
| 290 点、窗口 60、步长 5 的 47 个 rolling 窗口 | 268.3 ms |
| 290 点 × 400 ROI 的 `profile_dataset` | 8.9 s |
| 400 条 290 点全部 DTW（上三角含对角） | 46.8 ms |
| 400 条 5470 点、带宽 20 的全部 DTW | 579.8 ms |
| 单对 5470 点不限带宽 DTW | 112.6 ms |

这些数字只用来定位热点；P0 要在目标服务器上重测。

---

## 3. 阶段总表

| 阶段 | 内容 | 精度 | 进入下一阶段的条件 |
|---|---|---|---|
| P0 锁定语义与基线 | 完整检出、后端检查、真值集合、基线基准 | A | 有基线 JSON；真值文件入库 |
| P1 消除重复 | FP01、FP02、FP03/SY05、FP04、FP06–FP08、FP14、EX13、SY03、SY06 | A/B | 全部等价测试通过；基准对比 P0 有明确收益 |
| P2 认证检索 | SearchIndex：batch 指标下界 + EX01 cutoff 内核 + BD01–BD04 综合分数上界 | C | 一致性测试通过（结果与暴力完全相同）；有排除比例和基准 |
| P3 近似模式 | AP01、AP02、AP03、FAISS 索引、召回率估计、BD04 anytime | D | 召回率报告与抽样真值相符 |
| P4 规模与设备 | SY01、SY02、波前 DTW、SY07、SY08；GPU 条目视服务器而定 | A/B | 实际规模下优于优化后的 CPU 基线 |
| 发布 | 文档、网站示例页、`echotime[search]`、`0.18.0` | | 新环境安装后示例能跑 |

P3 和 P4 可以并行；P2 依赖 P1 的 PreparedSeries。

---

## 4. P0：锁定语义与基线

### 4.1 环境检查 [R:2.4]

- `git sparse-checkout disable`，确认 `native/`、`setup.py`、`benchmarks/` 存在。
- 新建分支 `feature/acceleration`。
- `pip install -e ".[dev]"`，然后 `similarity_backend_info()` 必须显示 `native_available: True`。不是就先修构建，否则所有基准都在测 Python。
- 记录：CPU 型号和核数、内存、有无 GPU、操作系统、Python/NumPy/SciPy 版本、`ECHOTIME_NUM_THREADS`。

### 4.2 真值集合 [R:10.1]

用固定提交的 Python 参考实现（`ECHOTIME_BACKEND=python`）生成并存入 `tests/golden/`：

- 16 种 batch 指标：随机游走 + 常数序列 + 含 NaN + 不等长 + 多通道，各种 `window`/`mode`/参数组合的 `pairwise_distance_matrix`、`one_vs_many`、`paired_distances`。
- `compare_series`、`rolling_similarity`、`profile_dataset` 的完整输出（含 notes、suggestions）。
- 之后每个阶段的等价测试都对照这些文件。A 类比逐位，B 类比容差并列出最大误差。

### 4.3 基线基准

写 `benchmarks/run_suite.py`，一条命令跑完，输出 JSON 和 Markdown 表：

| 工作负载 | 规模 |
|---|---|
| `compare_series` 单对 | 290 点、1024 点 |
| `rolling_similarity` | 290 点，窗口 60，步长 5 |
| `profile_dataset` | 400 × 290 |
| `one_vs_many`，16 种指标各一次 | N=10,000，T=256；dtw/erp/twed 另加 window=16 |
| `pairwise_distance_matrix`，dtw/sbd/erp | 400 × 400，T=290 和 5470 |
| 暴力 top-10（`one_vs_many` + 排序） | N=10,000 和 100,000，T=256，dtw 和 sbd |

记录字段见 9.3。数据用固定种子的随机游走，另加 `examples/data/` 里的真实数据。

### 4.4 产出

`benchmarks/results/<主机名>-<日期>-baseline.json`，以及 `tests/golden/`。

---

## 5. P1：消除重复（A/B 类）

这一阶段不改任何数值定义，所有工作负载都受益。按顺序做。

### FP04 修 `setdefault` 提前求值；去掉按对复制 embedding [R]

- `batch.py:294`、`:482` 改成 `if k not in cache`。A 类。
- embedding 距离现在把每对的两个向量各 stack 一份，全对任务复制 O(P·d)。改成存 N×d 唯一表，用索引取块。严格路径保留原来的逐元素减法求范数；GEMM 版本（`‖x‖²+‖y‖²−2x·y`）放到 SY07，属 B 类。

### FP01 数值与报告分离；惰性渲染 [R] [W:七.2]

- `compare_series` 内部拆成"数值核心"和"解释层"。数值核心只算请求的分量；notes、suggestions、interpretation 在访问时才生成。
- 旧接口行为不变：完整报告继续算完整字段。
- 新增 `compare_series(..., output="score")` 只返回五个分量和综合分数，不算 Spearman、Kendall、best-lag、NMI。
- `rolling_similarity` 按它实际返回的 10 列生成依赖集合，只算需要的。

### FP02 PreparedSeries：每条序列的特征只算一次 [R] [W:阶段 0]

一个对象，按需缓存：清洗后的值和时间戳；重采样、z 标准化后的各通道；差分及其标准化；Savitzky–Golay 趋势及其差分；差分的归一化谱；Spearman 秩；NMI 分箱；ACF；补零幅值谱（P2 用）；DTW 包络（P2 用）。

缓存键包含：数据版本、有效值掩码、`n_points`、通道策略、参数、源码语义版本。原地修改 NumPy 数组会破坏缓存，`PreparedSeries` 持有只读副本。

`compute_series_metrics` 里六个指标共用一次归一化谱。`spectral_drift` 用前后半段谱，不能用全谱替代。

### FP03 / SY05 PreparedCollection：跨查询复用 [R]

固定数据库、反复查询时，一次性按长度、通道数、参数分桶，保存连续数组、offsets、标准化视图、谱、包络。每次查询只准备查询端。内存不足时按特征层级 `np.memmap`。这也是 P2 索引的底座。

### FP05 相关类分量批量点积 [R]

z 标准化后 `r(x,y) = x̂ᵀŷ`。原序列相关、差分相关、趋势相关、趋势差分相关都能预先排成矩阵，按块算 `X Yᵀ`。B 类：GEMM 求和顺序不同；近常数输入保留 EPS 分支；小批量（默认 256 点）可能直接算更快，设批量阈值。多通道先按通道算非线性组合，再 `nanmean`，不能先平均再开方。

### FP06 / FP07 秩缓存、NMI 预分箱 [R]

- Spearman：每条序列的带并列处理的秩缓存一次，再批量相关。保留 wrapper 的小样本、常数、非有限值约定。Kendall 不能用秩点积代替，只在需要诊断时算。
- NMI：bins 由配对有效样本数决定；默认重采样且全有效时，每条序列的整数 bin 序列可缓存，配对时 `z = B·b_x + b_y`，一次 `bincount`。保留 `histogram2d` 对最右端点和边界的定义。

### FP08 best-lag 相关：前缀和 + 批量交叉项 [R] [W:三.1，修正版]

`_best_lag_corr` 是在重叠段上重新归一化的 Pearson，lag 范围 ±min(24, n/10)。[W] 写的"irfft 取最大值"用的是全局归一化，算出来不是同一个数。正确做法：

- 重叠段的 S_x、S_y、S_xx、S_yy 用前缀和；
- S_xy(ℓ) 对 49 个 lag 直接批量点积（短序列）或 FFT（长序列，交叉点由 P0 实测定）；
- 逐 lag 按真实重叠长度还原 `r = (nS_xy − S_xS_y)/√((nS_xx − S_x²)(nS_yy − S_y²))`。

B 类。大均值小方差时上式会抵消：先中心化再做前缀和，接近 EPS 阈值的 lag 回退原路径。保留 lag 集合、最小重叠 3 点、有符号最大值和并列次序。

### EX13 滚动统计快速模式 [R] [W:三.2，修正版]

新增 `rolling_similarity(..., mode="fast")`：维护 S_x、S_y、S_xx、S_yy、S_xy，窗口移动一格做一次删除和加入，只返回 Pearson、一阶差分 r 这类相关量。这是**另一个接口**，不是现有 rolling 的等价加速：现有 rolling 每个窗口重采样到 128 点再比较。

实现用 float64、先中心化、周期性重算，避免 `sum(x²) − sum(x)²/m` 抵消（[W] 的 float32 版本会出错）。

### SY03 线程池与 scratch 复用；SY06 在线 top-k [R]

- `parallel_for` 现在每次调用新建并 join 线程。改成和 `PreparedCollection` 绑定的线程池，线程私有 scratch 复用；按估算代价（长度 × 带宽 × 通道数）分块。
- 检索接口不再物化全部 pair，按块更新 top-k 堆。固定 (值, 序号) 的并列规则。

### FP14 冷启动与稳态分开 [R]

批量验证输入，直接返回结构化数组，再按需转对象。基准里冷启动和热启动分开报告。

### 单遍融合统计内核 [W:四.1，修正版]

C++ 一次扫描同时算原序列和一阶差分的全部矩。必须 float64、两遍去均值（先算均值再算离差平方和），否则和 `np.corrcoef` 对不上。[W] 的 float32 + `sxx − sx²/L` 版本不采用。放在 FP05 之后，只有 FP05 的 Python 版本仍是热点时才做。

### P1 验收

- `tests/golden/` 全部通过：A 类逐位，B 类列出最大误差。
- `benchmarks/run_suite.py` 对比 P0：`compare_series`、rolling、profile、全对矩阵分别报告倍数；分开报告冷热。
- 统计每个基础算子的调用次数（[R] FP02 的验证方法），确认重复确实消除。

---

## 6. P2：认证检索（C 类）

### 6.1 核心机制：下界加提前停止 [S:3] [R:9.4]

```
lb    = lower_bounds(query, 全部候选)        # 便宜：向量化或 FAISS Flat
order = 按 lb 从小到大（分块部分排序）
best  = 容量 k 的结果堆，按 (值, 序号) 排序，NaN 排最后

for 块 in order（每块约 线程数 × 4 条）:
    if best 已满 and 块首候选的 lb > best 第 k 名的值:
        break                               # 剩余候选的真实值 ≥ 下界 > 第 k 名
    并行: d = exact(query, c, cutoff=第 k 名的值)   # EX01 内核可提前放弃
    用 (d, c) 更新 best
```

停止时剩下每个候选的真实距离 ≥ 它的下界 > 第 k 名，不可能进入前 k（GEMINI 下界引理，Faloutsos 等 1994）。

让"精确"真正成立的细节：

- 并列：参考结果定义为按 (值, 序号) 稳定排序；停止条件用严格大于，下界等于第 k 名时继续算。
- 浮点：下界和精确距离走不同计算路径，下界可能因舍入略大于真实值（两条序列完全相同时最明显）。下界一律减去安全余量 c·ε·量级，c 由性质测试确定。[R:BD01] 强调固定 epsilon 不构成认证，所以余量要有误差分析，并在性质测试里用"完全相同的序列"等边界反复验证。
- 逐级：先用最便宜的下界对全部候选排序；更紧的下界在算精确距离之前才算。[R:EX02] 每一级都要统计拒绝率和耗时，几乎不排除候选的级关掉（见 9.5）。
- 并行：块内并行，块间更新阈值。较旧的阈值只会少剪，不会出错。

### 6.2 batch 指标的下界 [S:4]

依据是对 `similarity_methods.py` 实际定义的核对，不是教科书版本。

| 距离 | 定义要点 | 下界 / 方法 | 来源 |
|---|---|---|---|
| `trend`、`periodogram`、`linear_trend_model` | 向量差的 L2 | 本身是向量距离：FAISS `IndexFlatL2` 或 numpy 矩阵运算，直接精确 | S |
| `acf` | 每通道一个 L2，再平均 | 单通道同上；多通道用 ‖拼接差‖/d 作下界再精排 | S |
| `ordinal_js` | 序数模式分布的 JS 距离 | 默认 order=3 只有 6 维，全量向量化即可；大字母表时按 bin 逐块停止 | S，R:EX11 |
| `sbd`、`max_ncc` | 各自 z 标准化，多通道共用时滞 | 补零幅值谱的余弦是 max_ncc 的上界（6.3.1） | S |
| `independent_sbd`、`independent_max_ncc` | 每通道各取最大再平均 | 每通道一个谱上界，再平均 | S |
| `dtw` | 单点代价绝对值（多通道行间 L2），带宽 `max(window, |n−m|)`，可选除以 n+m | LB_Kim → LB_Keogh 双向 → 可选 LB_Webb → EX01 cutoff 内核（6.3.2） | S，R:EX02 |
| `erp` | 行间 L2，固定间隔值 | 求和下界；不限带宽时可加参照点（6.3.3） | S，R:EX04 |
| `twed` | ν>0、λ≥0 时是度量 | 参照点三角不等式（6.3.3） | S，R:EX04 |
| `lcss` | 1 − 匹配数/min(n,m)，匹配是 L2 ≤ ε | 包络给匹配数上界（6.3.4） | S |
| `edr` | 编辑次数，默认除以 max(n,m) | 包络给不可匹配点数下界；|n−m|；阈值推出窄带（6.3.4） | S，R:EX07 |
| `best_shift` | 返回时滞，不是距离 | 不参与检索 | |

### 6.3 推导要点

**6.3.1 SBD 和 NCC 的谱上界** [S]

L ≥ n+m−1，z 标准化后补零到 L，FFT 得 X、Y。线性互相关每一项满足 |cc[w]| ≤ (1/L)Σ_f |X_f||Y_f|；Parseval 给 ‖x‖² = (1/L)Σ|X_f|²。所以

```
max_ncc(x, y) ≤ cos(|X|, |Y|)        sbd(x, y) ≥ 1 − cos(|X|, |Y|)
```

多通道共用时滞时把各通道幅值谱拼接，结论不变。实现：每条序列存归一化幅值谱（半谱，频点权重 1、2、…、2、1 先乘 √权重）；下界就是一次内积，交给 `IndexFlatIP` 或矩阵乘。

降维仍精确：只保留前 D 个频点，再加一维 ‖X_tail‖。由 Cauchy–Schwarz，Σ_tail |X||Y| ≤ ‖X_tail‖‖Y_tail‖，截断向量的余弦仍是上界。这是 [R:EX10] "投影 + 残差范数"在相关类上的特例。

常数序列的 NCC 按约定为 0，下界设为 1，等于真实值。L 按集合中最长序列定，查询更长时按新 L 重算一次谱并缓存。

**6.3.2 DTW** [S] [R:EX01、EX02]

- LB_Kim：路径经过 (1,1) 和 (n,m)，下界 |x_1−y_1| + |x_n−y_m|（n=m=1 时只算一次）。只加首尾两项；加入最大最小项要取 max，不能相加（[W] 的四项平方和不是下界）。
- LB_Keogh：对每个 x_i，包络是 EchoTime 实际带宽 `j ∈ [max(1,i−w), min(m,i+w)]` 内 y 的逐通道最小、最大值；DTW ≥ Σ_i dist(x_i, 包络框_i)。多通道时点到轴对齐框的欧氏距离仍不超过点到框内任一点的距离。两个方向各算一次取最大；不相加。包络建在查询上，候选按长度分组。
- 归一化：`normalize=True` 时下界也除以 n+m。
- LB_Webb 作第三级，看第二级的剩余候选比例再决定。
- 内核 cutoff（EX01）：接口返回 `{value, exceeded_cutoff}`。提前放弃时不能把哨兵值写进结果矩阵。先做行最小值版本（每行最小值是最终值的下界，超过阈值即停）；再按 EAPruned（Herrmann & Webb 2021，实现 tempo）加入状态剪枝，覆盖 DTW、ERP、TWED。没有被放弃的计算和原内核逐位相同。
- 默认 `window=None` 不限带宽时包络很松，排除少。结果仍精确；文档建议设 `window` 或用 `mode="fast"`，结果里报告排除比例。

**6.3.3 ERP 和 TWED** [S] [R:EX04]

- ERP 不限带宽时满足三角不等式，且 ERP(x, ∅) = Σ‖x_i − g‖，所以 `ERP(x,y) ≥ |Σ‖x_i−g‖ − Σ‖y_j−g‖|`。限带宽的 ERP ≥ 不限带宽的，下界在任何带宽下成立。每条序列只存一个数。
- 参照点：选 P 个参照序列（16–64），预存每条候选到参照点的距离，查询时 `d(q,c) ≥ max_p |d(q,p) − d(p,c)|`。只对真正的度量用：ERP 不限带宽；TWED 在 ν>0、λ≥0 时（Marteau 2009）。用户设了带宽时，参照距离一律用不限带宽的版本算。EchoTime 的零哨兵、无穷边界、时间戳处理要在性质测试里逐一验证三角不等式确实成立（[R] 的提醒）。

**6.3.4 LCSS 和 EDR** [S] [R:EX07]

共用包络检查：x_i 到带宽内 y 的包络框距离 > ε，则 x_i 在带宽内无匹配。

- LCSS：匹配数 ≤ min(可匹配的 x 点数, 可匹配的 y 点数)，得相似度上界、距离下界。
- EDR：每个 x_i 恰好参与一次操作，找不到匹配的至少花 1；`EDR ≥ max(不可匹配 x 点数, 不可匹配 y 点数, |n−m|)`，默认再除以 max(n,m)。
- EX07：若非归一化 EDR ≤ K，则路径上 |i−j| ≤ K，可只访问宽 K 的带；长度差 > K 直接排除。归一化阈值先换算成整数预算，明确 `<` 与 `≤`，临界取整朝保守方向。
- 内核提前放弃：EDR 看行最小值；LCSS 看"当前行最大值 + 剩余行数"能否达到阈值。

### 6.4 `compare_series` 综合分数的 top-k [R:BD01–BD04]

这是 [S] v1 没有覆盖的一半。目标是

```
S = 0.20·s_shape + 0.20·s_dtw + 0.20·s_trend + 0.25·s_derivative + 0.15·s_spectral
```

无效分量被排除、权重重新归一化；`component_mean` 是另一个量，检索时必须指定目标是哪一个。

做法：

1. 四个便宜分量（shape、trend、derivative、spectral）在 PreparedSeries 上都是 O(L) 的点积和谱比较，**直接算精确值**。
2. 只对 DTW 分量用上界（BD01）：已算的加权和 A，DTW 权重 0.20，`S ≤ A + 0.20`。若当前第 k 名 τ > A + 0.20，跳过 DTW。
3. 收紧（BD02）：`s_dtw = exp[−½(d_level/0.45 + d_diff/0.35)]`，其中 d 是除以 n+m 后的 DTW。有下界 L_level、L_diff（6.3.2 的 LB_Keogh 除以 n+m）时，`s_dtw ≤ exp[−½(L_level/0.45 + L_diff/0.35)]`。
4. 还要算时，把 τ 换算成 DTW 必须达到的最小相似度 `s_req = (τ − A)/0.20`，再换成累计代价预算 `½(d_level/0.45 + d_diff/0.35) ≤ −ln s_req`。两次 DTW 共享预算，先算水平 DTW（cutoff 按 d_diff = 0 换算，再乘回 n+m），超过就放弃；再算差分 DTW。
5. 无效分支：默认 `n_points=256` 时 DTW 分量不会是 NaN（需要 min(n,m) < 6 才会）。长度 < 6 的退化输入直接算完整分数，不走界。
6. 并列和余量规则同 6.1。
7. 可随时返回（BD04）：先用 P3 的廉价候选把 τ 抬高，再扫描剩余候选的上界。`certified=True` 只在 pending 覆盖了全部候选、且最大剩余上界 < τ 时才置位。只精排 ANN 候选的结果标 `certified=False`。

节点级上界（BD03，给索引树整块排除）放到 P4 之后再评估。

### 6.5 接口 [S:7] [R:9.3]

```python
from echotime.search import SearchIndex

index = SearchIndex.build(
    collection,                 # 与 one_vs_many 的 candidates 同格式
    target="dtw",               # batch.METRICS 里任一名字，或 "similarity_score"
    layout="rows",
    window=16, mode="exact",    # 距离参数在建索引时固定
    n_jobs=None,
)

hits = index.search(query, k=10)                                   # mode="certified"
hits = index.search(query, k=10, mode="approximate", candidates=2000)
hits = index.range_search(query, radius=0.2)                       # 距离型 target
hits = index.search_batch(queries, k=10)

hits.ids            # 序号
hits.values         # 距离或分数，和逐条计算逐位相同
hits.certified      # True：全库认证；False：只在候选内精排
hits.stats          # 各级下界算了几次、精确距离算了几次、排除比例、耗时
hits.recall_estimate    # 仅 approximate：抽样估计的 CandidateRecall@k

reports = index.explain(query, hits.ids)   # 只对这 k 条生成 SimilarityReport
index.save(path); SearchIndex.load(path)
```

没装 FAISS 时所有功能可用，向量计算用 numpy，结果相同。

### 6.6 正确性保证 [S:8] [R:10.4]

1. 下界性质测试：大量随机序列对，覆盖不等长、多通道、带宽、NaN、常数、`fast` 模式、TWED 时间戳、完全相同的序列。每种下界检查 `LB − 余量 ≤ 精确值`；三角不等式用的度量逐一验证。
2. 检索一致性：每种 target、多种 k 和参数，`index.search` 必须和"`one_vs_many` + 按 (值, 序号) 稳定排序"完全相同。专门构造重复序列测并列。
3. cutoff 内核：未放弃时逐位相同；放弃时返回 `exceeded_cutoff=True` 且真实值确实超过阈值。
4. `similarity_score` 目标：和"逐对 `compare_series` + 排序"完全相同，包括 `component_mean`。
5. 覆盖检查：`certified=True` 的结果必须能证明 pending 覆盖了全部候选。
6. 小规模穷举、随机数据和构造反例上无误剪。原有 C++ 与 Python 一致性测试全部保留。

### 6.7 限制

- 不限带宽的弹性距离下界松，加速有限但不出错。
- 所有序列都很相似的库退化到接近逐条计算。
- 这两种情况在基准里如实报告。

---

## 7. P3：近似模式（D 类）[R:第 7 章] [S:6] [W:二，改写]

### 7.1 必须保住的

- 显式 `mode="approximate"` 才启用。
- 四类误差分开记录：表示误差、量化误差、搜索遗漏、评分误差。
- 指标是对**原版分数**的 `CandidateRecall@k = |G_k ∩ C_B| / k`，不是向量空间的召回率。
- 精排一律用原版精确函数。只精排候选 ≠ 全库精确，返回值 `certified=False`。

### 7.2 粗筛来源

| 条目 | 做法 | 备注 |
|---|---|---|
| AP01 多视角并集 | 标准化水平、差分、趋势、差分谱、峰谷统计各自检索，候选取并集 | 各路配额不等于评分权重；逐路消融 |
| FAISS 索引 | 6.3.1 的幅值谱、各类向量上建 IVF 或 HNSW；DTW 用 PAA 向量 | 可选依赖 `echotime[search]` |
| AP03 二值码 | 符号位、随机超平面哈希，XOR + popcount 扫描 | [W] 的符号位和 WTA 序数哈希归到这里，作为 D 类；必须覆盖全长，不是前 64 点 |
| AP02 分辨率金字塔 | 16/32/64/128 点表示，粗层决定是否进下一层 | 单独保护高频和尖峰视角 |
| AP19 热启动 | 相邻查询复用上一轮候选，先抬高 τ | 可和 certified 组合：热启动只改评估顺序 |

### 7.3 召回率估计

每次查询抽一部分（或定期抽一批）查询跑 certified 模式，比较两边 top-k，报告"估计 CandidateRecall@k = 0.99x（n 次抽样）"。[R:AP11] 的 conformal 校准放到有稳定查询分布之后。

### 7.4 从近似升级到认证 [R:BD04]

同一次查询先给候选，再对剩余候选扫描上界；满足覆盖和 `max 剩余上界 < τ` 时把 `certified` 置为 True。一次近似查询不能只改标签变成认证。

---

## 8. P4：规模与设备（按服务器硬件取舍）

先确认服务器配置，再决定做哪些。

| 条目 | 条件 | 内容 |
|---|---|---|
| SY01 运行时 ISA 分派 [R] | x86 服务器 | 同一包含 scalar、AVX2、AVX-512、NEON 内核，启动时检测。不把整个扩展用最高 ISA 编译。 |
| SY02 多变量 SIMD [R] | 多通道数据多 | 跨 pair 的 AoSoA 布局；lane 内保持现有通道求和树 |
| 波前 DTW [W:四.2] | 长序列宽带宽 | 反对角线并行，不改数值；配合 cutoff。M4 的 NEON 收益小于 AVX-512 |
| SY07 GEMM + 融合选择 [R] | 向量类目标 | FP05 的批量版本；B 类；边界候选用逐元素重算 |
| SY08 FFT 计划缓存 [R] | SBD 大批量 | plan 复用、批量变换、候选 lag 的精算批量化 |
| SY09、SY11 GPU DP 与数据常驻 [R] | **仅当服务器有 GPU** | FP64 吞吐先实测；剪枝比例和 GPU 倍数不能相乘 |
| SY13 混合精度 + 区间精排 [R] | 大库、内存带宽受限 | `|D̂ − D| ≤ (n+m−1)η` 的界只覆盖局部代价误差，累计舍入要另算 |
| SY16 超内存分块 [R] | 库大于内存 | `np.memmap`、预取、局部 top-k |
| SY18 发布 [R] | 发布前 | cibuildwheel；诊断输出当前后端、ISA、线程数 |

不做：SY04 NUMA（除非多路机器）、SY10 DPX、SY12 CUDA Graphs、SY15 多 GPU、SY19、SY20。

---

## 9. 实验：跑什么、什么时候跑

### 9.1 三类实验

| 类型 | 什么时候 | 耗时 | 做什么 |
|---|---|---|---|
| 正确性测试 | 每次提交 | 几分钟 | `pytest`：golden 文件、下界性质、检索一致性、cutoff 内核 |
| 阶段基准 | 每个阶段结束 | 服务器上 10–30 分钟 | `benchmarks/run_suite.py`，和 P0 基线比，写进阶段汇报 |
| 决策实验 | 只在需要取舍时 | 各不相同 | 见下表 |

决策实验：

| 问题 | 实验 | 判据 |
|---|---|---|
| 某一级下界留不留 | 记录该级耗时、拒绝率、省下的后续成本 | 省下的 > 自身成本才留 [R:11.4] |
| best-lag 用直接法还是 FFT | 按序列长度扫描两种实现 | 找交叉点，按长度分派 |
| GEMM 批量阈值 | 按批量大小扫描直接点积和 GEMM | 找交叉点 |
| 建索引是否划算 | 测 T_build、T_scan、T_index | `Q > T_build / (T_scan − T_index)` 次查询才摊平 [R:10.7] |
| 近似模式的候选数 | 候选数 B 对 CandidateRecall@k 和耗时的曲线 | 给定召回目标（0.95、0.99）取最小 B |
| GPU 值不值 | 同任务 CPU 与 GPU 端到端（含传输） | 端到端更快才进 P4 |

### 9.2 数据

- 固定种子的随机游走（UCR Suite 的标准做法），N ∈ {10⁴, 10⁵, 10⁶}，T ∈ {128, 256, 512, 1024}，D ∈ {1, 3}。
- `examples/data/` 的真实数据。
- 可选：UCR 时间序列档案。
- 困难子集必须单列：近重复序列、大量并列、`window=None`、全库高度相似。

### 9.3 记录字段 [R:10.3]

端到端 p50/p95/p99；稳态 pairs/s；prepare/build 时间；各阶段分时；峰值 RSS；DP 实际访问单元数；各级进入和拒绝的候选数；精排比例；线程数；冷启动和热启动分开；硬件和软件版本。GPU 计时要同步。

### 9.4 各精度等级的验收指标 [R:10.4]

- A：逐位、状态、NaN、边界、稳定排序。
- B：最大绝对误差、相对误差、误差分位数、最差案例；参考值接近 0 时用绝对误差。
- C：每个返回结果与参考值相同；覆盖全部候选；界的方向；cutoff 单位；并列次序；小规模穷举无误剪。
- D：`Recall@k`、`CandidateRecall@k`、阈值任务的漏检率、最坏子群、下游差异。

### 9.5 停止条件 [R:11.4]

- 下界成本长期高于它省下的计算：关闭该级。
- 索引在目标查询量内摊不平：用扫描。
- 近似模式在稀有模式上召回明显下降：扩大候选或回退。
- GPU 含传输后不胜过 CPU：保留 CPU。
- 低精度导致几乎所有候选都要 FP64 精排：缩小适用范围。

### 9.6 两个公式

- Amdahl：某阶段占比 p、加速 a 倍，整体 `1 / ((1−p) + p/a)`。热点转移后继续只优化 DTW 收益会下降。
- 带宽下限：必须读写的字节数 ÷ 实测可持续带宽。

### 9.7 服务器上要做的事

1. 按第 10 节准备环境。
2. 跑 `python benchmarks/run_suite.py --out benchmarks/results/$(hostname)-$(date +%F)-<阶段>.json`。
3. 把 JSON 和自动生成的 Markdown 表回传。
4. 每个阶段重复第 2、3 步一次。

开发和正确性测试在本地 M4 上做；服务器只跑基准和大规模实验。

---

## 10. 服务器准备清单

- 操作系统、CPU 型号和核数、内存、GPU 型号（有则记录 CUDA 版本）。
- Python 3.10–3.12，C++17 编译器（gcc ≥ 9 或 clang），`pip install -e ".[dev]"`。
- `python -c "from echotime._native import similarity_backend_info as i; print(i())"` 必须 `native_available: True`。
- `ECHOTIME_NUM_THREADS` 设为分配到的核数；容器或 Slurm 下用实际 cpuset，不用宿主机核数。
- 可选：`pip install faiss-cpu`（P3）；UCR 档案（9.2）。
- 不要在服务器上 `pip install echotime`（PyPI 的 0.17.1 是旧的纯 Python 版）。

---

## 11. 发布

- 新增可选依赖 `echotime[search]` = `faiss-cpu`，版本开工时定。
- `0.18.0` 一起发布 C++ 内核、P1 的加速和 P2 的检索。包里有 C++ 扩展后用 cibuildwheel 构建各平台 wheel，不再只发纯 Python wheel。
- 网站加一页示例：certified 和 approximate 两种模式的结果对比和召回率报告。
- 合并到 `main` 和发布都等 Zipeng 确认。

---

## 12. 量子计算：不采用 [S:13] [R:Q01–Q04]

- Grover / Dürr–Høyer 只把"逐条检查 N 个候选"降到约 √N 次 oracle 调用，每次调用要在量子电路里完整算一遍距离并反计算。
- 数据要先装进量子态：需要 QRAM 或 O(L) 的态制备，这一步已经和经典逐条计算同量级。
- 经典下界本来就跳过了大部分候选，平方级加速面对的前提在这里不成立。
- Swap test 读到的是 |⟨x|y⟩|²，丢掉相关的正负号；读 r 到 ε 精度要约 1/ε² 次测量。
- QFT 的"指数级加速"不含读出：读出全部谱系数仍要 O(L) 次测量。
- DTW 是多项式问题，DP 在 O(L·w) 内精确求解；改写成 QUBO 交给退火或模拟分岔，变量数变成 L²，且只是启发式。
- [R:Q04] 提到的 QOS 一类新结果是理论入口，未证明对完整 EchoTime 流水线有端到端优势。

---

## 13. 风险

| 风险 | 影响 | 应对 |
|---|---|---|
| 默认不限带宽，弹性距离下界松 | P2 加速有限 | 报告排除比例；文档建议设 `window` |
| 库内序列高度相似 | 退化到逐条 | 结果不错；基准里如实报告 |
| 浮点让下界略大于真实值 | 可能漏检 | 有误差分析的安全余量；性质测试覆盖完全相同的序列 |
| 不等长序列 | 包络和补零更复杂 | 候选按长度分组 |
| 百万级库内存 | 放不下 | memmap；谱截断 |
| ERP/TWED 的度量性质在 EchoTime 的边界处理下可能失效 | 参照点下界不成立 | 性质测试直接验证三角不等式；失效则只用求和下界 |
| B 类改动的误差在排名边界翻转次序 | 检索结果变化 | 边界候选用原路径重算 |
| 服务器没有 GPU | P4 的 GPU 条目作废 | 本计划已把 GPU 条目设为条件项 |

---

## 14. 来源对照

| 本文节 | 主要来源 |
|---|---|
| 1.1 两条路 | S，R 1.2 |
| 2 现状 | S 核对 + R 2.2、2.3 |
| 5 P1 | R FP01–FP08、FP14、EX13、SY03、SY05、SY06；W 三.1、三.2、四.1、七.2（均改写） |
| 6.1–6.3 下界 | S 3–4；R EX01、EX02、EX04、EX07、EX10、EX11 |
| 6.4 综合分数 | R BD01–BD04 |
| 6.5 API | S 7，R 9.3 |
| 7 近似 | R 第 7 章；S 6；W 二（改写为 D 类） |
| 8 设备 | R SY01、SY02、SY07–SY09、SY11、SY13、SY16、SY18；W 四.2 |
| 9 实验 | R 第 10 章、11.4；S 8–9 |
| 12 量子 | S 13；R Q01–Q04 |

---

## 15. 参考文献

- Faloutsos, Ranganathan, Manolopoulos. Fast subsequence matching in time-series databases. SIGMOD 1994.
- Kim, Park, Chu. An index-based approach for similarity search supporting time warping in large sequence databases. ICDE 2001.
- Keogh, Ratanamahatana. Exact indexing of dynamic time warping. KAIS 2005.
- Lemire. Faster retrieval with a two-pass dynamic-time-warping lower bound. Pattern Recognition 2009.
- Rakthanmanon et al. Searching and mining trillions of time series subsequences under dynamic time warping. KDD 2012.
- Webb, Petitjean. Tight lower bounds for Dynamic Time Warping. Pattern Recognition 2021.
- Herrmann, Webb. Early abandoning and pruning for elastic distances including dynamic time warping. 2021. 实现：github.com/MonashTS/tempo
- Chen, Ng. On the marriage of Lp-norms and edit distance. VLDB 2004.
- Chen, Özsu, Oria. Robust and fast similarity search for moving object trajectories. SIGMOD 2005.
- Vlachos, Kollios, Gunopulos. Discovering similar multidimensional trajectories. ICDE 2002.
- Marteau. Time warp edit distance with stiffness adjustment for time series matching. IEEE TPAMI 2009.
- Ukkonen. Algorithms for approximate string matching. Information and Control 1985.
- Paparrizos, Gravano. k-Shape: Efficient and accurate clustering of time series. SIGMOD 2015.
- Paparrizos, Franklin. GRAIL: Efficient time-series representation learning. PVLDB 2019.
- Micó, Oncina, Vidal. LAESA. Pattern Recognition Letters 1994.
- Shieh, Keogh. iSAX: Indexing and mining terabyte sized time series. KDD 2008.
- Johnson, Douze, Jégou. Billion-scale similarity search with GPUs. IEEE Trans. Big Data 2019.
- Malkov, Yashunin. HNSW. IEEE TPAMI 2018.
- Charikar. Similarity estimation techniques from rounding algorithms. STOC 2002.
- Chan, Golub, LeVeque. Algorithms for computing the sample variance. The American Statistician 1983.
- Wu, Keogh. FastDTW is approximate and generally slower than the algorithm it approximates. 2020.
- Dürr, Høyer. A quantum algorithm for finding the minimum. 1996.
- Aaronson. Read the fine print. Nature Physics 2015.
- Tang. A quantum-inspired classical algorithm for recommendation systems. STOC 2019.
- 其余按条目编号回查 [R] 各章末的参考资料。
