# Contributing

Thanks for considering a contribution.

EchoTime is a compare-first time-series project. Good contributions make the package easier to trust, easier to try in the first minute, and easier to hand off between humans and agents.

## Good first contributions

- onboarding and documentation improvements
- new starter datasets or notebook walkthroughs
- report examples, demo packs, and visual polish
- domain-specific plugins or input adaptors
- compatibility and environment-doctor improvements
- bug fixes with regression tests

## Local setup

1. Create a Python 3.10+ virtual environment for the repo.
2. Install the package in editable mode with dev dependencies: `pip install -e .[dev]`
3. Run `pytest` before opening a pull request.
4. For documentation builds, install `pip install -e '.[dev,docs]'`. Edit the
   generating source for generated guides. Then run `python tools/release_refresh.py`.

## Articles and references

Author the cited reading pages in `docs/articles/` and `docs/references/`. Run
`python tools/build_knowledge_pages.py` after editing them; `--check` verifies that
the bundled copies match their sources. The renderer checks local link targets
and bundles the HTML, JSON, and BibTeX with the wheel. `echotime --export-pages docs`
then exports these pages along with the existing site. New pages also need an
intentional description in `src/echotime/seo.py`.

If runtime tutorial snapshots, gallery scripts, or required visual assets change,
run `python tools/sync_runtime_assets.py` to update the small bundled resource set.
Its `--check` mode verifies byte equality and the source-hash manifest. The complete
release refresh also performs this synchronization.

For a new reference, record the primary URL, publication status, the claim it
supports, and the limits of that evidence. A paper appearing in the reading list
does not mean its method is implemented in EchoTime. Performance comparisons need
a shared task, data, preprocessing, parameters, and reproducible measurements.

## Development expectations

- keep changes focused on a real user or developer problem
- add or update tests when behavior changes
- keep the `echotime` public surface coherent and preserve legacy `tsontology` compatibility unless the change is explicitly a migration step
- prefer interpretable summaries, stable agent envelopes, and honest scope statements over opaque cleverness
- keep docs, notebooks, and generated showcase artifacts aligned with the actual package behavior

## Pull request checklist

1. Create a branch from your working baseline.
2. Summarize the problem, the change, and any compatibility impact.
3. Mention the tests you ran.
4. Include screenshots or report previews when the change affects docs, visuals, or HTML output.
5. Link related issues if they exist.

## Reporting issues

- Use GitHub issues for bugs, docs gaps, and feature requests.
- Use the contact in `SECURITY.md` for privately reported vulnerabilities.
- Include the input shape, expected behavior, actual behavior, Python version, and install path when possible.

## Design principles

- keep the first minute simple
- prefer interpretable outputs over opaque cleverness
- document scope honestly
- keep agent-facing schemas stable
