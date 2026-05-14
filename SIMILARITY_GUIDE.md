# EchoTime similarity guide

Similarity in EchoTime is not one thing. Sometimes you care about raw point-by-point shape, sometimes about shared rhythm, and sometimes about structural similarity at the dataset level.

## When to use raw-series similarity

Use raw-series similarity when two trajectories live on roughly compatible time scales and you want to ask whether the visible shape or timing is alike.

## When to use profile similarity

Use profile similarity when the datasets come from different scales, units, or observation modes, but you still want to compare their structural character.

## Best first moves

- Decide whether you are comparing levels, returns, increments, or z-scored shape.
- Preserve timestamps and event annotations instead of stripping them away.
- Use rolling similarity for regimes that probably change over time.
- Show both the numeric similarity report and a simple overlay plot.

## API pattern

- `compare_series(left, right) for direct shape comparison`
- `rolling_similarity(left, right, window=...) for changing relationships over time`
- `compare_profiles(left, right) for dataset-level structural analogies`

## How to explain the outputs to non-method users

- High shape similarity means the curves visibly move alike.
- High spectral similarity means the rhythms match even if peaks happen at slightly different times.
- High profile similarity means the datasets behave like the same kind of temporal problem even if the raw numbers differ.
