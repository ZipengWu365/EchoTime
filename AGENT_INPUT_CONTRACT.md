# Agent input contract

This page explains what `data_ref`, `left_ref`, and `right_ref` are expected to mean when an external agent calls `echotime` tools.

## Accepted reference families

- inline numeric arrays
- caller-managed file paths or URIs
- DataFrame-like tables
- typed wrappers such as `FMRIInput`, `EEGInput`, `IrregularTimeSeriesInput`, or `EventStreamInput`
- timestamp arrays via `timestamps_ref`, `left_timestamps_ref`, and `right_timestamps_ref`

## Minimal examples

### Profile one dataset

```json
{
  "data_ref": [0.0, 0.2, 0.5, 0.7, 1.0],
  "input_kind": "array",
  "domain": "generic",
  "budget": "lean",
  "audience": "agent"
}
```

### Compare two curves

```json
{
  "left_ref": [0.0, 0.2, 0.5, 0.7, 1.0],
  "right_ref": [0.0, 0.1, 0.45, 0.8, 1.1],
  "mode": "auto",
  "budget": "lean"
}
```

### Route a task

```json
{
  "task": "Compare these two curves and stop early if the signal is clear.",
  "available_inputs": ["left_ref", "right_ref"],
  "has_reference": true
}
```

## Returned contract helpers

Agent tool results now include:

- `artifact_uri`
- `cost_hint`
- `input_digest`
- `cache_key`

These fields are meant for orchestration, memoization, and compact handoff, not for end-user narration.
