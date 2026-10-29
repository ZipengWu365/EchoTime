# Method animations: verification record

## Delivered scope

The existing Methods Atlas is extended in place. Its navigation and URL remain
unchanged. Coverage is **137 entries**, consisting of the 10 native report
components/reference metrics and all 127 imported registry rows, including
variants and related comparison conventions. This count is not a claim of 137
distinct newly implemented algorithms.

| Family | Entries |
| --- | ---: |
| Native report components/reference metrics | 10 |
| Lock-step | 34 |
| Sliding | 12 |
| Elastic | 24 |
| Kernel | 10 |
| Feature-based | 18 |
| Model-based | 5 |
| Embedding | 24 |

Each entry includes a GIF, static final image, English/Chinese interpretation,
four detailed stages, concise on-image stages, input/parameter JSON, numerical
intermediate states, definition sources and limitations. Nine Markdown pages
provide an index and eight family guides. Existing atlas rows link to the
corresponding explanation.

## Numerical evidence and boundaries

- All 24 entries labeled **Checked against EchoTime** include numerical checks
  against the actual current implementation: 10 report quantities and 14
  low-level functions. Additional adapter checks are recorded in their traces.
- The other entries explicitly identify a reference formula (107) or a specified
  illustrative protocol (6). They do not claim new public APIs, pretrained
  encoders, reproduced published performance or benchmark superiority.
- Every final frame readout agrees with its recorded result. Strict JSON
  serialization rejects nonfinite numbers; unavailable DP cells use `null`.
- An explicit enumeration of all three paths through a 2-by-2 lattice verifies
  DTW, soft-DTW, GAK and discrete Fréchet objectives independently of the DP.
- Finite differences verify the soft-DTW occupancy derivative. Displayed DTW
  paths reproduce their objectives; MSM move/split/merge hand cases pass.
- Full orthogonal Haar preserves Euclidean norm to floating-point precision;
  the illustrative PAA and SAX lower bounds, truncated-Haar norm bound, stable AR
  fits and row-stochastic Markov matrices were checked.
- Multichannel examples either label the displayed channel explicitly or break
  the raw curve between concatenated display lanes. Per-channel alignments are
  computed separately before the stated aggregation.
- Ambiguous conventions are named. Examples include first-difference DDTW,
  descriptor-space shapeDTW, modified-Gaussian GAK, unweighted rFFT magnitude,
  finite-bin distributions, and explicitly chosen generic encoder/model rules.

## Executed local checks

| Check | Observed result |
| --- | --- |
| Complete test collection | **174 passed in 297.13 seconds** |
| Focused numerical/asset/atlas integration | 11 passed |
| Final presentation and asset integration selection | 8 passed in 21.91 seconds |
| Full animation coverage and artifact hashes | 137 methods; 412 hashed bundle files plus the manifest |
| GIF encoding and full frame decoding | All 137 GIFs decoded successfully; **2,878 frames** |
| Media size | GIFs: 16,233,103 bytes; posters: 6,940,573 bytes |
| Complete canonical animation bundle | 25,888,307 bytes, including traces/catalog/manifest |
| Reading and runtime resource freshness | 7 reading files and 19 runtime files verified |
| JavaScript syntax | Player script passed Node syntax checking |
| Static-first HTML and internal download links | 137 lazy posters, 137 inactive play controls, all local animation links resolve |
| Source/wheel build and metadata validation | Both artifacts built; `twine check` passed |
| Fresh wheel environment outside the checkout | 137 entries and 413 resources loaded; complete 461-file website exported |
| Runtime dependency isolation | No Pillow, Matplotlib or Markdown installed in the fresh wheel environment |

Representative final and intermediate images were inspected across pointwise,
lag, alignment, soft occupancy, spectral, symbolic, model, and embedding views.
Concise stage captions fit within the image layout; the full explanations remain
in the HTML/Markdown. The source's final wording was reconciled with all saved
traces after numerical rendering, checking that every image-affecting field was
unchanged.

The complete suite used Python 3.12.14, NumPy 2.3.5 and SciPy 1.17.0. The fresh
wheel environment resolved NumPy 2.5.4 and SciPy 1.18.1 and ran from `/tmp`,
asserting that the imported module belonged to that environment. A final
contrast adjustment uses the existing dark-theme surface/text tokens for the
search input and formula panels; the final targeted integration selection
passed after that change. Live browser verification is a post-deployment gate,
reported alongside the published commit. CI runs the complete suite on Python 3.10,
3.11 and 3.13 and separately verifies the wheel away from the source checkout.
Its latest status is available in the repository Actions tab.

## Reproduction

```bash
python -m pip install -e '.[dev,docs]' build twine
python tools/build_method_animations.py
python tools/build_method_animations.py --check
python tools/build_knowledge_pages.py --check
python tools/sync_runtime_assets.py --check
python -m pytest -q
python -m build
python -m twine check dist/*
echotime --export-pages docs
```

`tools/release_refresh.py` regenerates and mirrors the assets for both existing
site snapshots. Normal wheel imports and site export read prebuilt files and
require no Pillow or Matplotlib installation. Only CPU work is needed to build
the teaching assets. No PyPI release or social-platform post is part of this
documentation update.
