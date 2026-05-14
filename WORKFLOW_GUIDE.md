# EchoTime recommended workflow

**domain:** generic  
**environment:** notebook

**Recommended input setup:** Start with arrays or DataFrames; move to typed wrappers if semantic metadata matter.

**Priority axes:** predictability, drift_nonstationarity, trendness, rhythmicity, complexity

## Suggested steps

1. Organize the dataset in the most semantically faithful input form rather than stripping metadata too early.
2. Run profile_dataset(...) with domain-specific metadata such as sampling_rate, TR, channel names, visit columns, or explicit timestamps whenever available.
3. Inspect the priority axes together with reliability, notes, and domain/plugin metrics rather than reading any single score in isolation.
4. Export a dataset card so the profile can travel into papers, benchmark registries, or internal data catalogs.
5. Use task hints and reliability notes to guide model-family choice, validation design, and communication of caveats.

**Export tip:** Use profile.to_markdown() or profile.to_card_markdown() while exploring interactively.

## Relevant scenarios

### Environmental or industrial multichannel sensor datasets

Provides trend, rhythmicity, drift, coupling, and noise summaries before forecasting or anomaly pipelines.

**Best entrypoints:**

- `profile_dataset(array)`
- `profile_dataset(dataframe)`
- `profile_dataset(xarray_like_obj)`

### Sparse event streams, alerts, clicks, or treatment logs

Quantifies burstiness, event diversity, and dataset-level event archetypes before point-process or event modelling.

**Best entrypoints:**

- `profile_dataset(EventStreamInput(...))`
- `profile_dataset(records_or_table)`
