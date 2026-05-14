# Zero-install and low-friction entry points

Four ways to try the product surface before committing to a full environment install.

## Options

- Static playground: Preview similarity reports, visuals, and flagship cases without installing Python or starting a server.
- Colab quickstart: Open a starter notebook in a hosted notebook environment.
- uvx CLI: Run the CLI in an isolated ephemeral environment when packaging allows it.
- Local demo server: Run a tiny local web app that turns pasted values into similarity verdicts on your own machine.

## Example commands

- Open docs/index.html or playground.html locally to inspect the report layer without Python.
- Run `echotime-demo --open-browser` to launch the local live demo with pasted arrays and starter cases.
- Open examples/notebooks/11_colab_quickstart.ipynb in Colab or another hosted notebook service.
- Use `uvx --from echotime echotime --guide quickstart` when you want an ephemeral CLI path.
