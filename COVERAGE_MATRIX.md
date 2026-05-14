# EchoTime capability coverage

Primary means EchoTime is a first-class solution. Complementary means echotime helps but another package usually does the heavy lifting. Out of scope means the job should be handed to another package family.

| capability | echotime role | best companion packages | notes |
|---|---|---|---|
| Dataset-first structural profiling | Primary | — | echotime's main job is to turn a dataset into ontology axes, archetypes, reliability summaries, and task hints. |
| Dataset card JSON / Markdown | Primary | — | Useful for benchmark curation, cross-team handoff, and plain-language documentation. |
| Plain-language summary card and narrative report | Primary | — | Built for non-method collaborators, dataset owners, and cross-disciplinary teams. |
| Explicit agent-driving and compact context | Primary | — | Helps an LLM or agent choose a lean path and emit a compact reusable context bundle. |
| Raw feature extraction matrix | Complementary | tsfresh, Kats TSFeatures | echotime intentionally avoids becoming a giant feature zoo. |
| Forecasting models and backtesting | Out of scope | Darts, sktime, aeon, Kats | Use echotime before or beside forecasting, not instead of it. |
| Classification / regression / clustering estimators | Out of scope | aeon, tslearn, sktime | echotime profiles datasets and compares trajectories; it does not train supervised estimators. |
| DTW engine and alignment paths | Complementary | DTAIDistance | echotime surfaces similarity summaries; DTAIDistance is for distance computation and warping control. |
| Subsequence motif discovery / matrix profile | Out of scope | STUMPY | echotime works at dataset and whole-series levels, not matrix-profile subsequence mining. |
| Irregular, event-stream, and longitudinal typed wrappers | Primary | pandas, xarray, MNE, nilearn, clinical ETL pipelines | The goal is to preserve observation semantics before analysis rather than silently flattening them away. |
