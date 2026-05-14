# Compatibility presets

echotime now ships concrete compatibility presets for clean venv installs, mixed scientific stacks, and zero-install Pages evaluation.

Recommended default: `mixed-scientific-stack`

## Clean virtual environment (`clean-venv`)

Recommended for first-time installs, CI, and reproducible examples.

When to use: Use when you want the cleanest installation and can isolate echotime from an existing modelling stack.

Install / export commands:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -c constraints/clean-venv.txt echotime
```

Constraints:

- `numpy>=1.22,<2.3`
- `scipy>=1.8,<1.16`
- `pandas>=2.0 ; extra == 'io'`
- `pyarrow>=14.0 ; extra == 'parquet'`

## Mixed scientific stack (`mixed-scientific-stack`)

Conservative pins for environments that already contain aeon, sktime, numba, or broader notebook tooling.

When to use: Use when echotime must coexist with broader time-series / scientific tooling and you want fewer resolver surprises.

Install / export commands:

```bash
pip install -c constraints/mixed-scientific-stack.txt echotime
# or create a dedicated reporting env and keep your modelling env separate
```

Constraints:

- `numpy>=1.22,<2.2`
- `scipy>=1.8,<1.15`
- `pandas>=2.0,<2.3`
- `numba>=0.58,<0.62`
- `aeon>=0.11,<1.0`
- `sktime>=0.27,<0.40`

## Zero-install / Pages-only (`pages-only`)

Preview the product surface without installing echotime into Python at all.

When to use: Use when you need evaluation, screenshots, or stakeholder review before installation.

Install / export commands:

```bash
Open docs/index.html locally or publish docs/ to GitHub Pages.
Run echotime-demo in a disposable environment only if you need live computation.
```

## Export constraints files

```bash
echotime --write-constraints constraints/mixed-scientific-stack.txt --constraint-profile mixed-scientific-stack
echotime --write-constraints constraints/clean-venv.txt --constraint-profile clean-venv
```
