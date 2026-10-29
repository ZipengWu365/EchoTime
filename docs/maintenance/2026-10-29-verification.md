# Verification record — 29 October 2026

This record separates tests, package installation, source review, and research
claims. The update adds no new scientific benchmark result.

## Executed checks

| Check | Observed result |
| --- | --- |
| Original complete test suite at `320b7e65c74be6decef665cea87f56c5dc88ccd2` | 111 passed in 243.55 seconds |
| Numerical correctness and existing similarity-method tests | 62 passed; includes 49 new parameterized regression cases |
| Integrated complete suite after numerical and reading-page changes | 163 passed in 255.11 seconds |
| Final resource, reading-page, atlas and CLI integration selection | 10 passed in 21.45 seconds, including the 3 subsequently added runtime-resource tests |
| Markdown reading bundle freshness | 7 bundled files match their authoring sources |
| Runtime-resource freshness | 18 resources and 1 source-hash manifest match the source files |
| Wheel and source-distribution build | Both built successfully |
| `python -m twine check dist/*` | Both artifacts passed metadata/description validation |
| Fresh wheel environment, working directory outside the checkout | `echotime` and legacy `tsontology` imported from the installed wheel |
| Numerical checks in that fresh environment | Multichannel NCC/SBD identities and the hand-calculated TWED boundary case passed |
| Complete Pages bundle in that fresh environment | 48 files generated, including both articles and JSON/BibTeX references |
| Git whitespace check and workflow/issue-form YAML parsing | Passed |
| Browser screenshot check | Not completed: the temporary Chromium download returned an invalid archive. No browser-rendering claim is made. |

The original and integrated suites used Python 3.12.14, NumPy 2.3.5, SciPy
1.17.0, pandas 2.2.3, and pytest 9.2.0. The fresh wheel test installed only the
wheel's declared runtime dependencies and resolved NumPy 2.5.4 and SciPy 1.18.1.
It ran away from the source checkout and asserted the installed module path.

The repository now contains 166 collected tests. The final integration selection
was run after the small runtime-resource repair and documentation-copy corrections.
The new GitHub Actions workflow runs the complete collection on Python 3.10,
3.11 and 3.13; its individual run status is available in the repository Actions tab.

## Reproduction

```bash
python -m pip install -e '.[dev,docs]' build twine
python -m pytest -q
python tools/build_knowledge_pages.py --check
python tools/sync_runtime_assets.py --check
python -m build
python -m twine check dist/*
```

To check the wheel independently, create another virtual environment, install the
built wheel, change to an empty directory, import both package names, and run
`echotime --export-pages exported-docs`. The CI configuration performs this import
and bundle-generation check outside the checkout.

## Content and compatibility review

- The English article's Python example was executed successfully and produced its
  summary and HTML report. The quickstart's displayed prefix was checked against
  an actual result.
- The literature files contain 30 matching Markdown headings, JSON IDs and
  BibTeX keys; all 12 claim-map rows refer to existing records.
- Sources distinguish original papers, surveys, publication status, abstract-only
  checks, and full-text checks. Recent representation and forecasting results are
  kept separate from direct retrieval evidence.
- The article renderer validates local link targets; tests check generated local
  links and fragments, bundled bibliography consistency, and Chinese metadata.
- The full generated site was refreshed from the existing Python templates. This
  also reconciles previously stale tracked site snapshots with those templates.
- README image choices were preserved in the generator. Demo descriptions were
  checked against the bundled source data; legacy filenames and slugs remain
  compatible.
- Numerical changes and their recomputation implications are recorded in
  [CHANGELOG.md](../../CHANGELOG.md) and the [code audit](2026-10-29-code-audit.md).
- No release was uploaded to PyPI. Repository version 0.17.1 is retained until a
  separate release. Social posts are reusable drafts stored in the repository.

## Scope limits

This is a targeted maintenance pass and narrative literature guide. It does not
verify every entry of the 127-method registry, reproduce all cited studies, claim
universal retrieval relevance, or measure an EchoTime advantage over other
libraries. The literature map records source-access limitations beside the
affected records.
