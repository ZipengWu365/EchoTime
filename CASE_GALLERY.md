# EchoTime case gallery

These are high-visibility, cross-disciplinary time-series cases where EchoTime is meant to be useful.

## Web/app traffic and product analytics

**case key:** `web_product_traffic`  
**domains:** generic, product, web, traffic  
**audiences:** general, product, operations, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Why people care:** Traffic, conversion, and usage metrics are easy to explain to broad audiences and are often the first time-series many teams operationalize.

**Typical data:** Hourly or daily sessions, clicks, conversions, campaign spikes, release-day shocks, and multi-metric product dashboards.

**Common questions:**

- Is this mostly trend plus seasonality, or is it dominated by launches and bursts?
- Should we trust simple forecasting baselines, or is the system drifting too much?
- Which metrics move together strongly enough to justify multivariate modelling?

**Where EchoTime helps:** It gives a plain-language structural readout before teams jump into forecasting, anomaly detection, or KPI attribution debates.

**Recommended entrypoints:**

- `profile_dataset(dataframe, domain='traffic')`
- `profile_dataset(array, domain='product')`
- `profile.to_summary_card_markdown()`

**What to show non-method users:**

- summary card with top axes and plain-language meanings
- narrative report explaining whether the data are steady, seasonal, bursty, or drifting
- dataset card attached to experiment or dashboard documentation

**Practical value:**

- Explain why weekly seasonality matters before model selection.
- Flag that campaign bursts can distort average-based summaries.
- Communicate when traffic is stable enough for lightweight baselines.

## Retail demand, inventory, and operations planning

**case key:** `retail_demand_operations`  
**domains:** generic, retail, operations, supply_chain  
**audiences:** general, operations, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Why people care:** Demand planning is a high-visibility time-series use case because it directly affects stockouts, staffing, and revenue.

**Typical data:** Store- or SKU-level sales, promotion calendars, replenishment signals, and holiday-driven demand waves.

**Common questions:**

- How strong is the predictable seasonality relative to promo shocks?
- How heterogeneous are stores or SKUs?
- Should validation split by time only, or by store/product group as well?

**Where EchoTime helps:** It clarifies whether the dataset is mostly rhythmic, drift-heavy, bursty, or highly heterogeneous across units.

**Recommended entrypoints:**

- `profile_dataset(dataframe, domain='operations')`
- `profile.to_summary_card_markdown()`
- `profile.to_narrative_report()`

**What to show non-method users:**

- one-page summary card for merchants or operators
- narrative report that translates axes into replenishment implications

**Practical value:**

- Separate seasonality-heavy planning problems from campaign-shock problems.
- Justify store-aware or SKU-aware validation.
- Document when heterogeneity makes one pooled model hard to trust.

## Energy load, smart metering, and grid operations

**case key:** `energy_load_and_smart_metering`  
**domains:** generic, energy, operations, environmental  
**audiences:** general, operations, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, ml_benchmark

**Why people care:** Energy load is a classic public-facing time-series use case with clear seasonality, weather sensitivity, and operational stakes.

**Typical data:** Building load curves, feeder demand, smart-meter cohorts, distributed sensors, and weather-linked covariates.

**Common questions:**

- How much of the signal is predictable daily/weekly rhythm?
- Do sites behave similarly enough to pool them?
- Are drifts or regime changes strong enough to break static models?

**Where EchoTime helps:** It turns those questions into a structured profile that is easy to compare across sites or benchmark datasets.

**Recommended entrypoints:**

- `profile_dataset(array, domain='energy')`
- `profile_dataset(dataframe, domain='energy')`
- `profile.to_card_json()`

**What to show non-method users:**

- plain-language summary of rhythm, drift, and heterogeneity
- dataset card for benchmark governance or site comparison

**Practical value:**

- Show when seasonality dominates enough for strong baseline models.
- Flag when regime changes or drifts make historic averages unreliable.

## Wearable, digital biomarker, or recovery cohort

**case key:** `wearable_longitudinal_cohort`  
**domains:** wearable, clinical  
**audiences:** general, clinical, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Why people care:** Wearables are one of the highest-traffic modern time-series domains because they connect research, product, health, and consumer reporting.

**Typical data:** Heart rate, activity, sleep, recovery, repeated visits, device adherence gaps, and subject-level timelines.

**Common questions:**

- Is the problem dominated by adherence gaps and irregular follow-up?
- Are people more different from each other than days are within each person?
- Should evaluation split by subject, visit, or time?

**Where EchoTime helps:** It exposes longitudinal instability, dropout imbalance, and heterogeneity in a way clinicians and product teams can both read.

**Recommended entrypoints:**

- `profile_dataset(dataframe, domain='wearable')`
- `profile.to_summary_card_markdown()`
- `profile.to_narrative_report()`

**What to show non-method users:**

- summary card for study coordinators or clinicians
- narrative report explaining adherence, subject differences, and validation implications

**Practical value:**

- Make longitudinal cohort quality visible before model building.
- Show whether individual fingerprint structure is strong enough to matter.

## ICU, hospital telemetry, and irregular monitoring

**case key:** `icu_irregular_monitoring`  
**domains:** clinical  
**audiences:** general, clinical, cross-disciplinary  
**environments:** notebook, python_script, pandas_pipeline, cli_batch

**Why people care:** Irregular clinical monitoring is high-impact because timestamp quality, sparsity, and bursts of interventions strongly affect downstream claims.

**Typical data:** Irregular vitals, labs, interventions, alarms, asynchronous channels, and mixed event-plus-signal timelines.

**Common questions:**

- Are timing irregularity and missingness the main difficulty?
- Does the dataset behave like a sparse event process or a dense physiological signal?
- How much do patients differ structurally?

**Where EchoTime helps:** It keeps observation structure honest and gives non-method collaborators a reasoned explanation for why naive regular-grid assumptions may fail.

**Recommended entrypoints:**

- `profile_dataset(IrregularTimeSeriesInput(...), domain='clinical')`
- `profile_dataset(records_or_dataframe, domain='clinical')`
- `profile.to_narrative_report()`

**What to show non-method users:**

- narrative report for clinicians, data stewards, or protocol teams
- summary card that highlights irregularity, burstiness, and reliability caveats

**Practical value:**

- Document why explicit timestamps must be preserved.
- Flag when event bursts dominate over smooth trends.

## Resting-state or task fMRI cohort

**case key:** `resting_state_fmri`  
**domains:** fmri, neuro  
**audiences:** general, neuroscience, cross-disciplinary  
**environments:** notebook, python_script, neuro_stack, ml_benchmark

**Why people care:** fMRI is a flagship scientific time-series setting where multivariate coupling and cohort heterogeneity matter as much as single-node signals.

**Typical data:** Subject × time × ROI matrices, network labels, resting-state or task blocks, and cohort-level comparisons.

**Common questions:**

- How networked is the dataset?
- How much do subjects differ in temporal organization?
- Should models be framed as multivariate/network-aware rather than independent ROI series?

**Where EchoTime helps:** It turns networked temporal structure into a dataset card that non-method collaborators can actually read.

**Recommended entrypoints:**

- `profile_dataset(FMRIInput(...))`
- `profile.to_summary_card_markdown()`
- `profile.to_narrative_report()`

**What to show non-method users:**

- plain-language summary of coupling, heterogeneity, and rhythmic low-frequency structure
- narrative report suitable for supplements, preregistration, or lab onboarding

**Practical value:**

- Communicate why multivariate structure cannot be ignored.
- Summarize cohort-level differences before benchmarking new models.
