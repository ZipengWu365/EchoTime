# Local validation summary

Validated implementation commits: `5f60ab8` (feature preparation), `6567225`
(native cutoff), and `1ad5e3b` (certified/approximate retrieval). They retain the
user's planning commit `7ed374a` and the frozen baseline commit `033c98e`.
This summary reports local evidence; GitHub Actions and target-server results
must be reported separately.

| Check | Actual local result | Evidence |
|---|---|---|
| Complete repository suite, with native extension, FAISS and Markdown installed | **1,592 passed**, no skips, 83.75 s | [Final pytest log](local-pytest-final.log) |
| Complete suite after original-reference isolation and validation tests were added | **1,625 passed**, no skips, 85.36 s | [CI-hardening full log](local-pytest-ci-hardening.log) |
| Final sidecar dispatch validation, golden, and isolation checks | **801 passed in each of three environments**: original numerical stack, matching CI software versions, and controlled Haswell BLAS dispatch | [Original stack](local-dispatch-provenance-tests.log), [new stack](latest-dispatch-provenance-tests.log), [Haswell](haswell-dispatch-provenance-tests.log) |
| Original frozen golden contract | 383 fixtures / 767 parametrized checks included in the full pass | `tests/golden/acceleration_reference.json` |
| Same-harness smoke | 39/39 passed | [JSON](current-smoke.json) |
| Same-harness quick | 45/45 passed | [JSON](current-quick.json) |
| Independent search timing confirmation | 6/6 passed, all exact IDs/values match | [JSON](current-search-confirmation.json) |
| Wheel and source distribution | Built with GCC/G++; native extension present; golden JSON present in sdist | [Build log](local-build-final.log) |
| Distribution metadata | `python -m twine check dist/*.whl dist/*.tar.gz`: both PASSED | Local command result, development version `0.18.0.dev0` |
| Installed native wheel, fresh venv outside checkout | 15 exact metrics, all 5 candidate strategies, prepared score/report equality, save/load, 137 animations and 469 exported site entries passed | [Native install verification](local-wheel-verification.json) |
| Actual absent-extension fallback | Same verification passed from extracted wheel package without its `.so`; native_available=False | [Python-only verification](local-python-only-verification.json) |
| Reading bundle | 9 files verified | `tools/build_knowledge_pages.py --check` |
| Bundled runtime assets | 19 files verified | `tools/sync_runtime_assets.py --check` |
| Method animations | 137 regenerated numerical traces exactly match existing traces; all 412 assets verified | [Animation evidence](local-animation-validation.json) |
| Shared-input similarity lab | 147 states, 11 methods, 5 assets verified | `tools/build_similarity_lab.py --check` |
| GPU readiness probe | **Unavailable locally**; no GPU computation performed | [Probe result](gpu-probe-local.json) |

The 309 pytest warnings come from intentionally exercised undefined/empty input
paths and existing numerical warnings; they were not suppressed to fabricate a
cleaner result. The earlier run's two documentation skips were resolved by
installing the repository's specified Markdown 3.9 dependency before the final
complete run.

### Numerical-platform issue found by CI

The [first GitHub run](https://github.com/ZipengWu365/EchoTime/actions/runs/41884843447)
passed Python 3.11 and package/docs jobs. Python 3.10, 3.13 and the optional-search
job each failed 144 historical NCC fixture checks; no other test file failed.
Installing the same Python 3.12.15 / NumPy 2.5.4 / SciPy 1.18.1 / pandas 3.1.1
versions locally did **not** reproduce those A failures with default dispatch.

A controlled process using `OPENBLAS_CORETYPE=Haswell` did reproduce 144 failures,
with maximum absolute historical difference `2.220446049250313e-16`. The
**original commit produced those same differences**. All 242 original/current
NCC evaluations matched bit for bit under the same dispatch. A full original
source sidecar then passed all 767 current Python/native fixture checks under
Haswell. The historical failures remain in [their log](haswell-frozen-pytest.log);
they were not converted into passing historical A results. The first runner's
actual BLAS architecture was not recorded, so this establishes a reproducible
mechanism without claiming that runner used Haswell.

The resulting gate keeps the immutable fixture, verifies original source hashes
and imports, and compares A results strictly in the same environment. Historical
drift and portable compatibility are reported separately. Final provenance also
checks numerical build, CPU features and dispatch/thread variables; the new
dispatch-mismatch rejection adds one test after the 1,625-test complete run.
The three 801-test follow-ups include that guard. See
[the machine-readable evidence](numerical-portability.json) and
[the fixture protocol](../tests/golden/README.md).

The animation source fingerprints needed refreshing because two numerical
source files changed. Before refreshing them, all 137 examples were regenerated
and compared byte-for-byte with their stored traces; renderer sources, asset
hashes, explanation hashes and both asset copies were verified. Only source
fingerprints changed. No image or numerical trace was replaced.

Fresh native-wheel verification used Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0,
pandas 2.2.3 and faiss-cpu 1.15.1. A Linux x86-64 development wheel has been
tested locally. This does not establish Windows, macOS, manylinux portability,
other Python-version CI success, GPU execution or million-series acceptance.

Reproduce installed-package checks with the target interpreter:

```bash
python tools/verify_acceleration_install.py \
  --expect-installed --expect-backend native \
  --out benchmark-results/installed-verification.json
```

The pure-Python check uses the same script with `--expect-backend python`, and
requires an actually absent extension. Setting an environment variable to Python
while leaving the extension installed is deliberately insufficient for that
specific installation check.

For measured performance, including regressions and low approximate recall,
read [the complete evidence review](README.md). For the remaining acceptance work,
use [the server handoff](../docs/acceleration_server_handoff.md).
