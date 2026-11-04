# Acceleration reference fixtures

`acceleration_reference.json` was captured from the original Python backend at
commit `08f7df742b364175105e957d39f9f81fe6211bb3`, before modifying tracked
implementation files. It contains **383 cases**, their input arrays, complete
outputs, expected exceptions, source hashes, and generating environment. Inputs
and finite outputs are stored as hexadecimal floating-point strings. NaN and
infinity are explicitly represented; JSON contains no nonstandard numeric values.

## What is frozen

- All 16 batch metrics with `pairwise_distance_matrix`, `one_vs_many`, and
  `paired_distances`; a cross-distance case and row/column layout cases.
- Random walks, constant signals, exact ties, NaNs, unequal lengths, and
  multichannel input; nondefault windows, normalization and metric parameters.
- TWED with irregular timestamps and the existing fast-resampling path for
  LCSS, EDR, ERP, and TWED above the 512-sample threshold.
- Complete `compare_series`, `rolling_similarity`, `profile_dataset`, and
  `profile_series` results, including structure, interpretation text, notes,
  suggestions, metadata, and component details. Unsupported multivariate methods
  retain their original exception type and message.

## Contracts and portability

Contract A checks exact finite float hex values, including signed zero, and
exact integer results. NaN matches NaN without requiring the same NaN payload;
infinity signs must agree. This applies to elastic and NCC metrics. Contract B
uses both absolute and relative tolerance `1e-12` for embedding and high-level
numeric values; strings, keys, lengths, shapes, and dtypes remain exact.

Only the value of `package_version` is exempted from comparison, because releases
change it. Its key and a nonempty string value are still required. Schema
versions, all other metadata, and all user-visible text remain checked.

Floating-point libraries, CPU architectures, and SciPy versions may change a
last bit even before any EchoTime optimization. Default tests deliberately expose
such a mismatch. To diagnose portability explicitly, run:

```bash
ECHOTIME_GOLDEN_PORTABLE=1 python -m pytest tests/test_acceleration_golden.py -q
```

This applies the B tolerance to snapshot numerics while preserving all structure
and text checks. **It does not establish contract A equivalence.** Run
`tests/test_native_equivalence.py` on the same machine to compare the current
Python and native implementations directly. Do not silently switch a failed
strict CI job to portable mode or regenerate expected values from changed code.

### Strict comparison with the original source in a new environment

For another Python, NumPy/SciPy build or CPU, also run the **original source**
under that exact environment. The sidecar generator below reads the committed
input arrays and case definitions; it never calls `fixture_cases()` or imports
the accelerated implementation to calculate expected values.

```bash
git fetch --no-tags origin 08f7df742b364175105e957d39f9f81fe6211bb3
git worktree add --detach ../EchoTime-reference 08f7df742b364175105e957d39f9f81fe6211bb3
python tools/verify_reference_environment.py \
  --reference-source ../EchoTime-reference \
  --out benchmark-results/environment-reference.json
ECHOTIME_REFERENCE_SNAPSHOT=benchmark-results/environment-reference.json \
  python -m pytest tests/test_acceleration_golden.py -q
```

The tool verifies the full original commit, a clean tracked source tree, every
original Python source SHA256 and the actual import path. An isolated subprocess
loads only verified original source, bypasses stale bytecode and blocks the
native extension. The committed fixture SHA256, numerical environment and
case-by-case drift from the historical results remain in the sidecar. Existing
output files and the immutable fixture cannot be overwritten.

The test loader rejects sidecars with changed inputs, case definitions,
contracts, source hashes, environment versions or missing provenance. A sidecar
also records and checks the NumPy build configuration, CPU model/features,
BLAS dispatch overrides and relevant numerical thread variables. It must be
regenerated when these change; copying a SkylakeX result into a Haswell run is
not a same-environment comparison. A sidecar
cannot be combined with `ECHOTIME_GOLDEN_PORTABLE=1`: A checks remain exact
float-hex checks, and B retains its declared tolerance. A same-environment pass
establishes equivalence to original EchoTime on that environment; it does not
claim that a numerical library produces identical bits on every platform.

CI keeps three distinct checks: strict original-source sidecars across the
Python matrix; an explicitly labeled historical portability comparison; and a
recorded historical bitwise status with the capture's Python/NumPy/SciPy versions.
The last job also requires strict same-runner original equivalence: pinning
dependency versions does not pin a hosted runner's CPU or BLAS kernel. Its
historical status must agree with the independently measured original-source
drift. A historical bitwise mismatch remains a mismatch in that artifact and is
never relabeled as an A pass. Sidecars and the historical logs are retained as
CI artifacts; numerical/structural compatibility remains a separate required gate.

## Running and reproducing

```bash
python -m pytest tests/test_acceleration_golden.py -q
```

The test runs each case on Python and native backends, skipping only the native
variant if the compiled extension is absent. The snapshot contract adds one test,
so a native-enabled run has **767 tests**.

To audit regeneration, create a separate checkout at the recorded reference
commit and copy `tools/acceleration_golden.py` and
`tools/generate_acceleration_golden.py` into its `tools/` directory. Install the
recorded NumPy/SciPy versions, then run in that checkout:

```bash
python tools/generate_acceleration_golden.py \
  --reference-commit 08f7df742b364175105e957d39f9f81fe6211bb3 \
  --out /tmp/acceleration_reference_audit.json
```

The generator rejects a different HEAD or modified tracked implementation files.
Untracked additions are excluded from reference source hashes. Generation is a
manual audit operation, never a step in the regression tests. Compare the audited
fixture with the committed one and explain any numerical difference before
considering a reference update.
