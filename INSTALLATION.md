# Installation notes

Installation is intentionally minimal, but older scientific Python environments can still surface resolver noise.

- Use a fresh environment when possible. aeon/sktime/numba ecosystems can produce resolver warnings even when echotime itself installs correctly.
- Core install stays intentionally small: numpy and scipy.
- For tabular IO use echotime[io]. For parquet support use echotime[parquet].
- For mixed scientific stacks, export a compatibility preset and install with constraints instead of doing a bare install.
- If you only want to evaluate product value first, use the static playground or starter notebooks before integrating into a larger stack.
- Zero-install and low-friction entry points in this version: static playground, local live demo server, Colab notebook, and uvx CLI pattern.

# Environment doctor

Environment looks clean.

## Watchouts

- No immediate watchouts detected.

## Recommended next steps

- Your environment looks straightforward for a normal install and CLI use.
- Use `echotime-demo --open-browser` to evaluate the product surface without wiring echotime into an existing notebook stack.
- Use `echotime --export-pages docs` to generate a GitHub-Pages-ready static demo bundle.
- Use `echotime --write-constraints constraints/clean-venv.txt --constraint-profile clean-venv` to export a concrete constraints file.
