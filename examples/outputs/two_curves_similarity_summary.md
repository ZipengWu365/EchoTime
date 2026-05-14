# echotime similarity summary

**Compared:** left vs right

## Headline

These two inputs show **very high** similarity overall (score 0.989).

left and right are strongly similar overall. The best agreement appears in spectral similarity and derivative similarity.

## Most important similarity dimensions

| plain-language label | score |
|---|---:|
| spectral similarity | 1.000 |
| derivative similarity | 0.994 |
| shape similarity | 0.994 |
| trend similarity | 0.991 |

## Recommended next actions

- Plot both series after z-score normalization to show the shared shape without scale differences.
- Run rolling or windowed similarity if you expect the relationship to change over time.
- Use structural-profile similarity when scales, frequencies, or observation modes differ too much for raw-shape comparison.
- Inspect spectral or seasonality-aware models because the two series share rhythm strongly.