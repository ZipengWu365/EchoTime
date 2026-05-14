# Routing and tool contracts

Stable compare-first input contracts for agent tools in v0.17.0.

## Stable tool surfaces

- `ts_profile({data_ref, input_kind, timestamps_ref, domain, budget, audience})`
- `ts_compare({left_ref, right_ref, left_timestamps_ref, right_timestamps_ref, mode, budget})`
- `ts_route({task, available_inputs, has_reference})`

## Required output fields

- `schema_version`
- `tool`
- `ok`
- `input_contract`
- `artifact_uri`
- `cost_hint`
- `input_digest`
- `cache_key`
- `confidence`
- `limitations`
- `evidence`
- `recommended_next_step`
- `next_actions`
- `error`
