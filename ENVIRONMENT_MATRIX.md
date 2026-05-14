# EchoTime environment matrix

| environment | title | best for | typical inputs | what echotime adds | usual outputs |
|---|---|---|---|---|---|
| notebook | Jupyter or interactive notebook | Exploration, teaching, hypothesis generation, and profile inspection. | arrays; DataFrames; typed wrappers | Lets you move from raw data to a readable structural profile in a few lines and inspect notes, cards, and reliability interactively. | profile.axes; Markdown report; dataset card; API guide functions |
| python_script | Plain Python script or package pipeline | Reusable profiling steps in research codebases or internal libraries. | arrays; typed wrappers; tables; custom adapted objects | Makes structural profiling reproducible and scriptable for data intake, QC, or benchmark preparation. | JSON payloads; card files; profile.to_dict() |
| cli_batch | CLI and shell batch jobs | Quick audits, CI checks, and dataset-card generation without writing Python glue. | .npy/.npz arrays; .csv/.json/.jsonl/.parquet tables | Turns profile generation into a shell-friendly step and now also exposes guide content from the command line. | stdout text; Markdown report; card JSON/Markdown; guide documents |
| pandas_pipeline | Pandas / parquet / tabular data pipeline | Clinical, wearable, and observational data already organized as long or wide tables. | DataFrame; parquet path; CSV/TSV/JSON/JSONL path; record lists | Keeps you in the same tabular ecosystem while adding structural profiling, longitudinal interpretation, and dataset cards. | profile axes; longitudinal plugin metrics; card exports |
| neuro_stack | Neuro stack (MNE-like / xarray-like / ROI arrays) | Neural time-series workflows that already use ecosystem-specific containers. | MNE-like objects; xarray-like objects; FMRIInput; EEGInput | Adds a structure-aware summary layer without forcing you to abandon domain-native containers. | domain-aware plugin metrics; network summaries; cards for publications/benchmarks |
| ml_benchmark | ML benchmark or evaluation pipeline | Benchmark curation, dataset coverage analysis, and metadata generation for model comparisons. | any adapted dataset form | Provides stable ontology axes, schema versioning, reliability summaries, and machine-readable cards that can travel with a benchmark suite. | card JSON; schema export; comparable axis vectors |

## Notes by environment

### Jupyter or interactive notebook (`notebook`)

- Best environment for first contact with a new dataset.
- Combine with about(), api_reference(), and scenario_guide() to onboard collaborators.

### Plain Python script or package pipeline (`python_script`)

- Good fit when you want deterministic artifact generation.
- The registry API is easiest to integrate from scripts.

### CLI and shell batch jobs (`cli_batch`)

- Useful for data release pipelines and benchmark registries.
- Parquet support depends on the runtime having a parquet engine installed.

### Pandas / parquet / tabular data pipeline (`pandas_pipeline`)

- Ideal when your storage layer is already tabular.
- Longitudinal columns such as subject, visit, time, and channel unlock richer interpretation.

### Neuro stack (MNE-like / xarray-like / ROI arrays) (`neuro_stack`)

- Use typed wrappers when you want explicit metadata such as TR or channel names.
- echotime complements, rather than replaces, domain packages.

### ML benchmark or evaluation pipeline (`ml_benchmark`)

- Best environment when you need repeatable cards across many datasets.
- The package is descriptive infrastructure, not a benchmark runner.
