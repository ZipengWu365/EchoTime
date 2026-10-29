# Time-series similarity roundup: publication drafts

Prepared 2026-10-29. These drafts are saved for review and reuse; storing them here does not publish them to social platforms. The article contains the primary citations and implementation boundaries.

**English article:** https://github.com/ZipengWu365/EchoTime/blob/main/docs/articles/time-series-similarity-guide.en.md\
**中文文章：** https://github.com/ZipengWu365/EchoTime/blob/main/docs/articles/time-series-similarity-guide.zh-CN.md\
**Repository:** https://github.com/ZipengWu365/EchoTime

## LinkedIn — English

DTW, matrix profiles and learned embeddings can answer different questions about the same time series.

A complete recording may resemble another recording. A short event may recur inside an otherwise unrelated signal. Two datasets may have similar structural summaries. Each case needs its own definition of a useful match.

I've put together a practical comparison covering:

- what normalization and time alignment remove;
- when whole-series comparison and subsequence search need different evaluation;
- how DTW, SBD, shapeDTW and soft-DTW differ;
- what evidence is needed before using learned embeddings for retrieval;
- where aeon, tslearn, DTAIDistance, STUMPY, sktime and EchoTime fit.

One detail that matters: rerunning exact distances on a shortlist cannot recover a relevant candidate that approximate screening already discarded.

The guide links original papers and official documentation, including recent multivariate-distance and retrieval-augmented forecasting work. It also includes a small EchoTime example for sharing a component-level similarity report. No new cross-library performance ranking is claimed.

Read the comparison:
https://github.com/ZipengWu365/EchoTime/blob/main/docs/articles/time-series-similarity-guide.en.md

#TimeSeries #MachineLearning #OpenSource

## X — six-post English thread

Each numbered block below is one post. Publish them as a thread if approved for that platform.

### 1/6

Time-series similarity starts with the object you want to match: a complete recording, a short event, or a dataset's structural profile. The same pair can look similar under one definition and different under another.

### 2/6

For a nonconstant signal and positive scaling, z(3x + 7) = z(x). Standardization preserves that shape while removing its level and amplitude. Decide whether those differences matter before normalizing.

### 3/6

DTW permits local timing changes. SBD searches global shifts. shapeDTW compares local descriptors before alignment. Each choice allows different matches. Record the constraints and inspect the paths when timing matters.

### 4/6

A matrix profile records nearest-neighbour distances for fixed-length subsequences. State the window, normalization and self-match exclusions. A rare segment under that definition still needs evidence before it becomes a domain-specific anomaly.

### 5/6

TS2Vec and foundation-model embeddings are candidates for retrieval. Define relevance and evaluate ranking quality. Classification or forecast accuracy alone does not establish that the nearest retrieved examples answer your question.

### 6/6

Full comparison: DTW, matrix profiles, learned representations, six Python tools and a runnable EchoTime report example. Original sources and limitations included.
https://github.com/ZipengWu365/EchoTime/blob/main/docs/articles/time-series-similarity-guide.en.md

## 小红书／图文 — 中文标题与说明

**标题：时序相似性：DTW、矩阵轮廓怎么选**

两个信号看起来相似，到底相似在哪里？

可能是整段形状，也可能只有一个事件相似，或者只是频率成分接近。把这些问题分开，才知道应该用哪类方法、怎样评价结果。

整理了一份有原始论文和官方文档的盘点，比较 DTW、SBD、shapeDTW、矩阵轮廓和学习表示，也列出了 aeon、tslearn、DTAIDistance、STUMPY、sktime 与 EchoTime 的使用入口。

图里先讲五个选型判断。完整文章还包括预处理、调参、数据划分、近似检索评价，以及一个可以运行的结构报告示例。

中文全文：
https://github.com/ZipengWu365/EchoTime/blob/main/docs/articles/time-series-similarity-guide.zh-CN.md

#时间序列 #机器学习 #科研工具 #开源

## 五张卡片文字

### 卡片 1 — 先选问题，再选距离

**“相似”至少有四种比较对象。**

找相似的完整记录 → 整序列比较\
找再次出现的短事件 → 子序列搜索\
比较数据的结构特征 → 数据集画像\
让模型学习某种误差 → 损失函数

比较对象不同，正确答案也不同。

页脚：任务划分参考 aeon 官方相似性搜索文档；完整来源见文章。

### 卡片 2 — 标准化会丢掉你可能需要的信息

**曲线形状一致，绝对负荷可能相差很大。**

对非常数信号、正比例缩放：\
z(3x + 7) = z(x)

想忽略增益和零点差异，这个性质很有用。\
想保留能耗、幅度和绝对水平，先明确这些量如何进入比较。

页脚：公式直接由均值和标准差定义得到。

### 卡片 3 — 时间变化也要规定允许范围

**整体晚一点，与某一段持续更久，属于不同变化。**

SBD：寻找全局位移。\
DTW：允许局部时间规整。\
shapeDTW：先描述局部形状，再对齐。

选择方法时，同时写下允许的变化和必须保留的差异。

页脚：Paparrizos & Gravano, 2015；Zhao & Itti, 2018；tslearn 官方 DTW 文档。

### 卡片 4 — 找局部模式，窗口就是问题的一部分

**矩阵轮廓记录子序列与最近合格邻居的距离。**

窗口多长？\
是否标准化？\
排除哪些平凡自匹配？

这些设定共同决定什么算“重复”或“孤立”。\
孤立片段的具体领域含义，需要进一步证据。

页脚：STUMPY 官方矩阵轮廓与 AB-join 教程。

### 卡片 5 — 学习表示也需要任务证据

**先定义相关结果，再评价检索排序。**

TS2Vec、MOMENT 等提供学习表示的路线。\
分类或预测效果好，仍需另行验证本次检索需求。

完整盘点附六个 Python 工具的对照，以及 EchoTime 组件级报告示例。

查看全文：GitHub → ZipengWu365/EchoTime → docs/articles

页脚：Yue et al., 2022；Goswami et al., 2024。完整原始来源见文章。

## Reuse notes

- The worked example uses synthetic signals solely to show the reporting interface.
- None of these drafts claims a benchmark win, user growth, adoption, probability calibration or performance superiority.
- Do not replace the article link with a link to an unrelated product page; the promised comparison should remain immediately accessible.
- Claims were checked against the [article evidence ledger](../docs/articles/README.md). Future edits that add numbers or comparative results need their own evidence.
