# EchoTime 加速：服务器验证与 RTX PRO 6000 交接

本文件用于验收当前代码，以及把尚未完成的服务器性能验证交给下一位开发者。
**`run_suite.py` 执行 Python / C++ CPU 路径；GPU 设备信息采集不等于 GPU 加速测试。**
不能根据服务器装有 RTX PRO 6000，把 CPU 结果标成 GPU 结果。CUDA、CuPy、PyTorch、
GPU FAISS 和专用 GPU kernel 不由这套基准自动启用。若当前仓库没有实际 GPU 实现，
EchoTime GPU 后端的验收结论应填写“未实现、未测试”，不要填写 0 ms 或“通过”。
独立的 `gpu_probe.py` 可以测试 GPU 矩阵乘法硬件路径，不能把它称为 EchoTime GPU 后端。

## 1. 本轮验证对象

这次交付重点是已有评分语义的回归、重复准备工作的减少、原始距离的搜索、以及显式
近似搜索。真正的速度提升需要在同一台机器、相同数据与配置上对比。

| 层次 | 验证内容 | 合格证据 |
|---|---|---|
| 原始语义 | 16 个 batch metric、参数、NaN、常量、ragged、multichannel、完整高层报告 | golden 和 Python/native equivalence 通过；有偏差时给出具体位置 |
| P1 准备与报告 | raw/prepared、完整报告/score、full/fast rolling | 语义符合各自 API 合同；计时包含可识别的准备成本 |
| Certified 搜索 | 返回原 metric 的 top-k、原值、稳定 ID tie order | 与完整 `one_vs_many` 排序逐项相同 |
| Approximate 搜索 | 候选生成后按原 metric 重排 | 返回值仍来自原 metric；明确候选预算和实测 Recall@k |
| 大规模性能 | 10k/100k 候选、400 条 pairwise、400 通道 profile | 完整 JSON/Markdown、环境、配置、失败记录、峰值内存说明 |
| GPU | 只有实际 GPU kernel 才能进入此栏 | kernel 路径、设备、传输/执行时间、原始精度对照；当前 suite 不提供此测量 |
| GPU 硬件探测 | `gpu_probe.py` 的 FP32/FP64 GEMM | 驻留 GPU 与上传/计算/回传分开计时；不构成 DTW 或 EchoTime 加速证据 |

基准对新 API 做存在性检测：旧基线缺少 `PreparedSeries`、score 输出、fast rolling
或 `SearchIndex` 时记为 `unavailable`。已有 API 执行异常记为 `error`，进程返回非零。
因此“脚本退出 0”需要和 JSON 的 `summary` 一起阅读；存在 `unavailable` 不代表所有
计划中的能力都已验收。

## 2. 服务器准备

建议在待验收开发分支的独立环境中运行。以下命令假设当前目录是完整 EchoTime checkout，
Python 3.12 可用，系统已有 C++17 编译器。不要在验收期间更改实现或参考数据。

```bash
python3.12 -m venv .venv-accel
source .venv-accel/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pip install pybind11 'setuptools>=77.0.3' wheel

python -c "import echotime; from echotime import _native; print(echotime.__file__); print(_native.similarity_backend_info()); assert _native.native_available()"
```

编译扩展是可选安装步骤，安装成功本身不能证明 native 编译成功。上面的断言用于防止
把 Python fallback 当成 C++ 性能结果。对原始架构不支持当前编译目标的节点，需要按
`setup.py` 的 `ECHOTIME_NATIVE_MARCH` 配置重编译并记录该参数，不要修改 fast-math
设置来换取未经验证的数字。

建议保留以下环境材料：

```bash
mkdir -p benchmark-results/server
git rev-parse HEAD > benchmark-results/server/revision.txt
git status --short > benchmark-results/server/worktree-status.txt
python -m pip freeze > benchmark-results/server/packages.txt
c++ --version > benchmark-results/server/compiler.txt
python -c "import numpy as np; np.show_config()" > benchmark-results/server/numpy-config.txt
python -c "import os, platform; print(platform.platform()); print(os.cpu_count()); print(sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else 'affinity unavailable')" > benchmark-results/server/cpu.txt
nvidia-smi > benchmark-results/server/nvidia-smi.txt
```

最后一个命令仅在有 NVIDIA 驱动时适用；没有该工具应说明环境情况。suite 本身会在
工具存在时记录 GPU 名称、驱动和总显存，同时明确 `execution_status`。

## 3. 先做正确性验收

```bash
python -m pytest -q
python -m pytest tests/test_acceleration_golden.py tests/test_native_equivalence.py -q
```

Golden 从原始提交 `08f7df742b364175105e957d39f9f81fe6211bb3` 的 Python 实现冻结，
共 383 个参考 case，双后端加元数据校验共 767 个测试。完整字段、文本和异常语义都检查。
浮点输入/结果以 hex 保存；生成环境和源文件 SHA256 位于
`tests/golden/acceleration_reference.json`。这些期望值不能从优化后的实现重新生成。

如果新机器只出现浮点末位差异，先保留严格失败日志，再运行显式诊断：

```bash
ECHOTIME_GOLDEN_PORTABLE=1 python -m pytest tests/test_acceleration_golden.py -q
python -m pytest tests/test_native_equivalence.py -q
```

portable 模式放宽快照数值为 `rtol=atol=1e-12`，结构与文本继续严格检查。
**portable 通过不能替代 A 类逐位等价门槛。** 应比较 Python、NumPy、SciPy、BLAS、
编译器和 CPU，再判断变化来自平台还是代码。不要自动改容差、隐藏失败或重写 golden。

## 4. 基准 profile 与成本边界

```bash
python benchmarks/run_suite.py --list
python benchmarks/run_suite.py --profile quick --list
python benchmarks/run_suite.py --profile server --list
python benchmarks/run_suite.py --profile full --list
```

`--list` 不导入 EchoTime，也不分配数据。默认 `smoke` 不会启动百万候选或长序列全对全。

| Profile | 数据量与用途 | 本机/服务器用途 |
|---|---|---|
| `smoke` | 最大 32 条候选，24–48 个时间点，3 通道 profile，单个真实 CSV | 检查路径、输出和回归，不能据此宣布大规模加速比 |
| `quick` | 16 metric 的 N=64/T=128，搜索 N=128，报告 T=290/1024，47 个 rolling 窗口，8 通道 profile，3 个真实 CSV | CPU 上可复现的快速前后对照 |
| `server` | 16 metric 的 N=10,000/T=256；DTW/ERP/TWED 另测 window=16；N=400/T=290 pairwise；T=290/C=400 profile；10k 搜索 | 服务器性能主矩阵，运行前先看 case 列表 |
| `full` | 在 server 基础上增加 N=100,000 搜索和 N=400/T=5470 pairwise | 显式重任务，不应作为普通 CI |

长序列 DTW/ERP pairwise 使用 `window=16`，避免把昂贵的 unrestricted DP 混在默认任务里。
该结果只说明这一窗口下的性能。suite 同时保留 unrestricted one-vs-many 和
adversarial DTW 检查；它们也不能替代未测过的 unrestricted T=5470 全对全。
本轮没有自动运行百万候选的命令。

## 5. 建立同机原版基线

使用独立 worktree，避免用改进后的 Python 模块配原版二进制，或反过来。

```bash
git worktree add --detach ../EchoTime-accel-baseline 08f7df742b364175105e957d39f9f81fe6211bb3
(
  cd ../EchoTime-accel-baseline
  python setup.py build_ext --inplace
)
```

主 checkout 的 benchmark harness 可以通过 `--source-tree` 测量这个旧版本，实际导入
文件路径、源文件 SHA256、扩展 SHA256 都会进入输出。显式设置 BLAS 线程可以降低和
EchoTime 原生线程的相互干扰：

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

python benchmarks/run_suite.py \
  --source-tree ../EchoTime-accel-baseline/src \
  --data-dir ../EchoTime-accel-baseline/examples/data \
  --profile quick --backend native --n-jobs 1 --repeats 9 --warmups 2 \
  --out benchmark-results/server/baseline-quick-t1.json

python benchmarks/run_suite.py \
  --source-tree src \
  --profile quick --backend native --n-jobs 1 --repeats 9 --warmups 2 \
  --baseline benchmark-results/server/baseline-quick-t1.json \
  --out benchmark-results/server/current-quick-t1.json
```

核对旧结果 `environment.source_commit` 为上述基线提交，并且实际包路径来自 baseline
worktree。新结果应来自当前工作目录。每个 JSON 自动生成同名 Markdown。
基线对照会拒绝配置、seed、backend、线程、策略、CPU/affinity、数值库或线程环境不同的
case；同名 case 也不会绕过这些条件。CPU 负载、温度、编译器差异仍需人工控制。

## 6. 服务器主矩阵

先测试单线程，再选一个不超过进程 CPU affinity 的线程数。下面以 8 为例；这只是配置
示例，不代表所有 RTX PRO 6000 服务器都拥有相同 CPU 或核心配额。

```bash
python benchmarks/run_suite.py \
  --source-tree ../EchoTime-accel-baseline/src \
  --profile server --backend native --n-jobs 1 --repeats 7 --warmups 2 \
  --out benchmark-results/server/baseline-server-t1.json

python benchmarks/run_suite.py \
  --source-tree src \
  --profile server --backend native --n-jobs 1 --repeats 7 --warmups 2 \
  --baseline benchmark-results/server/baseline-server-t1.json \
  --out benchmark-results/server/current-server-t1.json

python benchmarks/run_suite.py \
  --source-tree ../EchoTime-accel-baseline/src \
  --profile server --backend native --n-jobs 8 --repeats 7 --warmups 2 \
  --out benchmark-results/server/baseline-server-t8.json

python benchmarks/run_suite.py \
  --source-tree src \
  --profile server --backend native --n-jobs 8 --repeats 7 --warmups 2 \
  --baseline benchmark-results/server/baseline-server-t8.json \
  --out benchmark-results/server/current-server-t8.json
```

完整矩阵较慢时可以按 `--group` 分批，例如 `--group report --group rolling --group profile`，
或按 `--case` glob 精确挑选。先查看 `--list` 再运行，确保所选配置和预期一致。
每完成一个 case，JSON 会写入检查点。中断后可以读取已完成结果；缺少最终 `summary`
意味着这次运行没有完整结束。重新运行会重写指定输出文件，建议使用新的文件名。

更大的搜索与长 pairwise 分开执行：

```bash
python benchmarks/run_suite.py \
  --source-tree src --profile full --backend native --n-jobs 8 \
  --case 'search/*/*/n100000/*' --repeats 7 --warmups 2 \
  --out benchmark-results/server/search-100k-t8.json

python benchmarks/run_suite.py \
  --source-tree src --profile full --backend native --n-jobs 8 \
  --case 'pairwise/*/n400/t5470/*' --repeats 3 --warmups 1 \
  --out benchmark-results/server/pairwise-long-t8.json
```

旧版本没有 `SearchIndex`，因此 certified/approximate 的主要速度参照是**同机同数据**的
`search/.../brute/...` case。比较搜索延迟时还需报告 index build 成本。一次查询场景应
加上构建和准备开销；大量重复查询才可能摊薄这些费用。

## 7. 近似搜索：候选预算与召回

默认 approximate case 使用 `max(16, 2*floor(sqrt(N)))` 个候选，并上限裁到 N。
每个结果 JSON 的 `configuration.candidates` 记录实际请求预算。
可以用 `--candidates 1000` 覆盖 approximate 预算，用 `--bounds cheap` 或
`--bounds none` 量化显式下界的开销；`bounds=none` 仍可能使用 DP cutoff。
`--strategy` 支持当前 SearchIndex 暴露的 `multiview`、`pyramid`、`binary` 和可选
`faiss` / `faiss_hnsw`。
缺少可选 FAISS 包时会明确记录 unavailable；安装 `faiss-cpu` 也不启用 GPU FAISS。

```bash
python benchmarks/run_suite.py \
  --source-tree src --profile server --backend native --n-jobs 8 \
  --case 'search/*/approximate/*' --strategy pyramid --repeats 7 \
  --out benchmark-results/server/approximate-pyramid.json

python benchmarks/run_suite.py \
  --source-tree src --profile server --backend native --n-jobs 8 \
  --case 'search/*/approximate/*' --strategy binary --repeats 7 \
  --out benchmark-results/server/approximate-binary.json

python benchmarks/run_suite.py \
  --source-tree src --profile server --backend native --n-jobs 8 \
  --case 'search/*/approximate/*' --candidates 1000 --repeats 7 \
  --out benchmark-results/server/approximate-budget1000.json

python benchmarks/run_suite.py \
  --source-tree src --profile server --backend native --n-jobs 8 \
  --case 'search/*/approximate/*' --strategy faiss_hnsw --candidates 1000 --repeats 7 \
  --out benchmark-results/server/approximate-faiss-hnsw.json
```

最后一个命令需要安装可选 `faiss-cpu`。`faiss` 是 CPU `IndexFlatL2` 的完整向量扫描；
`faiss_hnsw` 是真正的 HNSW ANN 候选检索，并增加一层漏召回来源。多线程建图后，
跨重建的候选集合不保证完全相同。FAISS 的 `faiss_omp_max_threads` 是配置上限，
不等于 EchoTime `n_jobs`，也不等于实测活跃线程数；两者应分别记录。

suite 先用原始 `one_vs_many` 建立完整参考，再独立验证返回值、ID 和 Recall@k。
参考生成时间单独记录，排除在 search 调用计时之外。Certified 必须精确重现按
`(isnan(value), value, row_id)` 的排序，NaN 排在 infinity 后。Approximate 允许漏召回，
但返回的距离必须仍等于原始 metric 在相应 ID 上的距离。

目前每个 case 使用一个固定合成 query；重复计时重复同一 query。由此得出的 Recall@k
是单个 case 的实测值，**不是跨真实业务分布的召回保证**。`candidate_recall_at_k` 只有在
搜索 API 明确提供时才填入，否则为 null；不能把未知字段补成 1。

可以改变 seed 重复探索失败情形；改变 seed 会同时改变合成候选库和 query：

```bash
for echotime_bench_seed in 1001 1002 1003 1004 1005; do
  python benchmarks/run_suite.py \
    --source-tree src --profile server --backend native --n-jobs 8 \
    --case 'search/*/approximate/*' --seed "$echotime_bench_seed" --repeats 3 \
    --out "benchmark-results/server/recall-seed-${echotime_bench_seed}.json"
done
```

正式的召回验收还需要固定真实候选库和独立 held-out query 集，至少记录每个 query 的
真值、候选预算、最终 ID、耗时和失败模式。置信区间应以 query 为抽样单位；一个 query
内部的 k 个命中不能直接当成 k 个独立 Bernoulli 试验。本套 smoke/quick 输出没有证明
“所有查询 Recall@10≥0.99”之类的声明。

## 8. 怎样阅读性能结果

- `first_call_seconds` 是模块已导入、输入已生成、索引已建后的第一次 API 调用。
  它不等价于新进程启动的端到端冷启动。`run.import_seconds`、数据生成、prepared
  构建、index build、参考真值生成分别记录。
- `warm_samples_seconds` 保留所有重复计时，p50/p95/p99 基于这些样本计算。3、7 或 9 次
  重复能发现大幅变化，不能支撑生产服务的尾延迟承诺。
- `result.stats` 来自最后一次测量调用；其中阶段耗时不是所有重复的中位数，不能要求
  它们之和等于外部 `p50_seconds`。准备阶段字段则对应这次 case 的一次性准备。
- `database_candidate_series` 吞吐率用数据库总条数除以查询时间，包含被剪枝的条目；
  它与真实 DP 执行次数不同。应同时看 `exact_evaluations`、`pruned`、`cutoff_abandoned`、
  `cells_visited` 等实际存在的 stats。缺失统计保持缺失，不填 0。
- `rss_before_bytes` 和 `rss_after_bytes` 是进程 RSS 采样。
  `process_peak_rss_bytes` 是该进程的累计高水位，可能来自前一个 case，不能称为本 case
  的独立峰值。要测独立内存，可用 `--case` 每次启动一个新进程。
- raw report、score-only、prepared score 和 fast rolling 具有不同输出/准备合同。
  fast rolling 仅返回原始窗口的相关统计，不生成完整 similarity score；不能把它和完整
  report 的耗时差写成“同一任务无损加速”。
- 任何数字都应附 revision、source hash、backend、线程数、输入规模、窗口和精度合同。
  原始 CSV 使用文件 SHA256、所选列和行数记录。结果 checksum 用于识别 run，不替代浮点回归。

## 9. RTX PRO 6000 上仍需决定的工作

仓库提供了独立硬件探测脚本。服务器需要已有与其 CUDA/驱动匹配、可以使用 CUDA 的
PyTorch；本文件不猜测适用于所有服务器的 PyTorch/CUDA 安装组合。

```bash
python benchmarks/gpu_probe.py \
  --out benchmark-results/server/gpu-probe.json --require-gpu
```

该脚本测量 FP32/FP64 GEMM 的 GPU 驻留数据路径，以及上传、计算、结果回传路径。
本机未能执行 GPU 计算的实际结果保存在 `benchmark-results/gpu-probe-local.json`，状态为 unavailable。
`--require-gpu` 让服务器缺少所需环境时明确失败，避免把缺失测试视为成功。
这些结果只说明该矩阵乘法探测的运行情况。GEMM 的 GFLOPS、FP32/FP64 比值或
传输时间不能转换成 DTW、NCC、profile 或完整 EchoTime 的加速倍数。

这台服务器首先用于验证本轮 CPU/search 改动在更大数据上的实际行为。是否值得新增 GPU
取决于真实测量：如果大部分成本来自候选数量而 certified/approximate 已充分减少计算，
GPU kernel 未必是下一步主要收益；如果候选数仍大、计算足够规则且可批量复用，GPU 路线
才有明确的实验对象。

开始新的 GPU 实现之前，需要固定以下实验条件：

1. 明确目标 metric、归一化、窗口、缺失值、tie order、以及 FP64/FP32 的验收合同。
2. 对照当前最佳 CPU/search 路径，既测驻留 GPU 的重复查询，也测数据上传、布局转换、
   kernel、结果回传和最终原始分数重排的端到端成本。
3. 记录 GPU 型号、驱动、CUDA/runtime、显存占用和功耗/时钟相关设置；明确是否预热。
4. 用这一轮 golden、原始 batch 参考和 held-out queries 验证正确性/召回，保留失败样本。
5. 在 GPU 路径被实际实现并运行前，不报告 GPU 加速倍数，也不把 CPU FAISS 称为 GPU ANN。

本轮没有要求安装量子 SDK、申请量子硬件、或把量子算法原型纳入性能宣称。

## 10. 可直接交给服务器开发助手的提示词

```text
你接手 EchoTime 加速分支的服务器验收。请先读本仓库
docs/acceleration_server_handoff.md、tests/golden/README.md、当前 API 代码和
已存在的 benchmark-results。目标是独立验证当前已实现功能，不改写 golden 或隐藏失败。

机器有 RTX PRO 6000，但当前 benchmarks/run_suite.py 执行 CPU Python/C++ 路径。
请把“GPU 可见”“GPU 路径已实现”“GPU 路径已测试”三个状态分别报告。
如果没有真正 EchoTime GPU 实现，请明确写“EchoTime GPU 后端未实现、未测试”，
继续完成 CPU/大规模验收。独立的 GEMM 硬件探测不能称为 EchoTime GPU 后端。

工作顺序：
1. 保存当前 revision、dirty state、Python/NumPy/SciPy/BLAS、编译器、CPU affinity、
   线程配置、驱动和GPU型号。确认 native_available() 为 True。
   如果服务器已有匹配CUDA的PyTorch，运行：
   python benchmarks/gpu_probe.py --out benchmark-results/server/gpu-probe.json --require-gpu
   缺少环境则报告阻碍。区分FP32/FP64、GPU驻留与上传/计算/回传，不把GFLOPS当DTW倍数。
2. 运行完整 pytest、严格 golden、当前 Python/native equivalence。保留完整日志。
   有失败先定位。允许用显式 portable 模式诊断平台浮点差异，但不能据此宣布 A 类通过。
3. 创建原始08f7df742b364175105e957d39f9f81fe6211bb3独立worktree并编译扩展。
   用同一个harness的 --source-tree 测旧版和新版，核对实际导入路径及SHA256。
4. 先smoke/quick，再server。按文档做1线程与一个合理多线程配置，同机同数据同参数。
   大任务先 --list；100k搜索与T=5470 pairwise分批跑，每次输出独立JSON和Markdown。
5. Certified和完整one_vs_many稳定排序逐项对照，检查NaN、ties、近重复、无约束窗口、
   全库高相似等情况。Approximate记录策略、预算、原始重排值和每query Recall@k。
6. 报告first-call/warm、prepare/build/reference、p50/p95/p99、RSS定义、
   exact_evaluations/pruned/cells_visited等实际字段；没有测到的字段保持缺失。
7. 将服务器发现的性能回退和错误分别列出：可复现命令、输入配置、预期、实际、证据文件。
   小样本吞吐或单query召回不能写成一般保证。GPU收益不能从设备存在性推断。
8. 输出一份验收Markdown，明确通过/失败/未测、同机加速比、构建成本、召回限制和下一步。
   若需要改源码，先做最小修复并补充能暴露该错误的测试，保留原始失败证据。
   不发布PyPI，不自行合并主分支。任何GPU新开发都作为独立下一阶段，先给可审查方案。
```

建议交回整个 `benchmark-results/server/`、测试日志、依赖锁定信息和验收 Markdown。
这些材料足以区分代码问题、平台差异、工作负载条件以及尚未验证的性能目标。
