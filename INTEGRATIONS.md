# Integration templates

Copyable templates for bringing your own CSV or DataFrame into EchoTime, then scaling up to tool-calling or MCP when needed.

## Templates

- pandas notebook template: examples/integrations/pandas_notebook_template.py
- OpenAI tool-calling template: examples/integrations/openai_tool_calling_template.py
- MCP server template: examples/integrations/mcp_server_template.py
- local live demo entry: echotime-demo --open-browser

## Bring your own data

- Use the pandas template when you already have a CSV, parquet file, or DataFrame and want the shortest path to a summary card plus HTML report.
- For wide tables, keep one `timestamp` column and one or more numeric measurement columns.
- For irregular long tables, rename columns to `subject`, `timestamp`, `channel`, and `value` before profiling.
- If your file uses different names, rename from aliases such as `time`, `measurement`, `sensor`, and `patient` before calling the API.
