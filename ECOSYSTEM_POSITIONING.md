# EchoTime in the time-series Python ecosystem

Positioning notes below are based on official documentation pages consulted on 2026-03-08. They describe what the packages publicly emphasize, not every edge capability they may contain.

EchoTime is **dataset-first**. It profiles, compares, and explains time-series datasets before or beside modelling. It does not try to replace the forecasting, estimator, DTW, or matrix-profile libraries that already do those jobs well.

## Honest positioning

| package | official emphasis | strongest fit | how echotime relates |
|---|---|---|---|
| tsfresh | Automatically calculates a large number of time-series characteristics and includes methods to evaluate their explaining power for regression or classification tasks. | large handcrafted feature extraction, feature filtering, series-as-features pipelines | EchoTime is not a feature-zoo replacement; it is dataset-first structural profiling. Use echotime when the first question is 'what kind of temporal dataset is this?' and tsfresh when you need a broad handcrafted feature matrix for downstream supervised learning. |
| aeon | A scikit-learn compatible toolkit for time-series tasks such as forecasting, classification, regression, clustering, anomaly detection, similarity search, and benchmarking. | estimators and pipelines, benchmarking, forecasting / classification / regression / clustering, similarity search | echotime sits earlier in the workflow: dataset characterization, ontology axes, summary cards, and compact context for collaborators or agents. aeon is the modelling-and-evaluation toolbox you use once you already know what sort of problem you have. |
| sktime | A unified toolbox for machine learning with time series, including algorithms, transformations, pipelining, tuning, ensembling, and forecasting/classification workflows. | forecasting pipelines, composite estimators, time-series transformations, evaluation and tuning | EchoTime is for structural triage, communication, and dataset cards; sktime is for building, tuning, and evaluating models. |
| tslearn | A Python package that provides machine-learning tools for the analysis of time series. | time-series clustering, classification and regression, distance-based learning | EchoTime is not primarily a learner library. It focuses on understanding and comparing datasets before or beside modelling, while tslearn focuses on machine-learning algorithms over time-series objects. |
| DTAIDistance | A library for time-series distances such as Dynamic Time Warping, with Python and faster C-backed implementations. | DTW distance, alignment paths, pairwise distance matrices, distance-based clustering | echotime does include high-level similarity summaries, but it is not a dedicated DTW engine. Use DTAIDistance when alignment paths, distance matrices, or lower-level DTW controls are the main deliverable. |
| STUMPY | Efficiently computes the matrix profile, a representation built from nearest-neighbor distances among subsequences within a time series. | motif discovery, subsequence anomaly search, matrix-profile workflows | EchoTime is not a matrix-profile or subsequence-mining library. It helps you profile whole datasets and summarize temporal structure at the dataset or pairwise-comparison level. |
| Darts | A user-friendly library for forecasting and anomaly detection on time series, with classical and deep models under a common fit/predict interface. | forecasting models, backtesting, anomaly detection, probabilistic forecasting | echotime does not train forecasting models. It helps decide whether the data look trend-dominant, rhythmic, bursty, nonstationary, heterogeneous, or irregular before forecasting choices are made. |
| Kats | A one-stop shop for time-series analysis including detection, forecasting, TSFeatures, multivariate analysis, and utilities. | forecasting, detection, TSFeatures, general-purpose analysis workflows | Kats spans multiple analysis tasks; EchoTime is narrower and more explicit about dataset ontology, structural profiling, agent context, and plain-language dataset reports. |

## When to choose echotime first

- You need to understand **what kind of temporal dataset** you have before selecting a modelling stack.
- You need a **dataset card**, **summary card**, or **narrative report** for non-method collaborators.
- You want to compare two curves or two datasets and keep the result interpretable.
- You want an **agent-friendly**, compact, low-token intermediate representation of the result.

## When echotime should be paired with other libraries

- Pair with **tsfresh** or **Kats TSFeatures** when you need a wide handcrafted feature matrix.
- Pair with **aeon**, **sktime**, or **tslearn** when you need estimators, pipelines, benchmarking, clustering, or supervised learning.
- Pair with **Darts**, **aeon**, **sktime**, or **Kats** when the main job is forecasting or anomaly detection.
- Pair with **DTAIDistance** for explicit DTW distance matrices or alignment paths.
- Pair with **STUMPY** for motif, discord, or matrix-profile workflows.

## Sources consulted

- tsfresh: tsfresh docs — https://tsfresh.readthedocs.io/en/latest/
- aeon: aeon docs — https://www.aeon-toolkit.org/en/v0.9.0/
- sktime: sktime docs — https://www.sktime.net/en/stable/user_guide/introduction.html
- tslearn: tslearn docs — https://tslearn.readthedocs.io/en/stable/
- DTAIDistance: DTAIDistance docs — https://dtaidistance.readthedocs.io/en/latest/
- STUMPY: STUMPY docs — https://stumpy.readthedocs.io/en/latest/Tutorial_The_Matrix_Profile.html
- Darts: Darts docs — https://unit8co.github.io/darts/
- Kats: Kats docs — https://facebookresearch.github.io/Kats/
