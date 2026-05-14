# Start here

A single landing point for compare-first quickstart, bringing your own data, zero-install preview, local live demo, environment diagnostics, and GitHub Pages export.

## Fast paths

- Open start-here.html or docs/start-here.html to choose the fastest path.
- Use the static playground if you only want to inspect similarity demos and visuals.
- Run echotime-demo --open-browser when you want real computation on pasted arrays.
- Run echotime --guide doctor before installing into a noisy scientific environment.
- Run echotime --write-constraints constraints/mixed-scientific-stack.txt --constraint-profile mixed-scientific-stack before installing into a busy scientific stack.
- Use echotime --export-pages docs to generate a Pages bundle for GitHub publishing.

## If you already have your own data

- Single numeric CSV column: load the column into pandas and call `profile_series(...)` for the fastest first report.
- Wide table: keep one `timestamp` column and one or more numeric columns, then call `profile_dataset(df, domain=...)`.
- Irregular long table: rename columns to `subject`, `timestamp`, `channel`, and `value`, then call `profile_dataset(df, domain=...)`.
- Two columns to compare: call `compare_series(df['left'], df['right'])` and write the HTML report to disk.
- If your names differ, rename from aliases such as `time`, `measurement`, `sensor`, and `patient` before calling the API.
- Edit `examples/integrations/pandas_notebook_template.py` when you want a concrete file instead of starting from a blank notebook.
