# Method animations: implementation and verification plan

## Scope

EchoTime is a software/documentation repository. This change adds educational
animations to the existing Methods Atlas and Markdown documentation, preserving
the existing navigation, URLs and numerical APIs. Coverage is the 127 imported
registry entries and 10 native comparison components, each with an individual
animation and explanation. A reference animation does not establish that its
method is available as an EchoTime API.

## Evidence object

Each animation uses deterministic, explicitly illustrative small arrays. The
rendering script records its input, parameters, output and definition source.
Methods supported by EchoTime are checked against the relevant implementation
where applicable; reference definitions and generic encoder protocols carry
separate labels. No training, learned model performance or benchmark claim is
made. Formula conventions are stated where several variants exist.

## Execution

Small CPU-only plotting and documentation generation runs locally. No cluster,
GPU or production benchmark is needed. The build command will be
`python tools/build_method_animations.py`; the corresponding `--check` command
will verify coverage, sources and asset hashes without regenerating GIFs.

## Acceptance

- Every registry/native ID has explanatory text, source links, GIF and poster.
- Animations contain meaningful intermediate numerical states and method-specific
  labels, transformations or alignment choices.
- Reference-definition demonstrations remain distinct from current library APIs.
- GIFs have multiple frames; posters and representative intermediate frames are
  inspected for legibility, clipping and mathematical consistency.
- The existing page supports keyboard-controlled play/stop and static defaults;
  GIF download links and Markdown remain usable without JavaScript.
- Site export and the installed wheel include all required assets.
- Link/coverage tests and existing regression gates pass before publication.

Missing method coverage, broken links, stale assets, invalid numerical examples
or unexplained implementation differences constitute an incomplete build.
