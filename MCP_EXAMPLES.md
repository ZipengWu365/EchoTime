# MCP tool descriptors

```json
{
  "schema_version": "1.0.0",
  "tools": [
    {
      "name": "ts_profile",
      "description": "Profile a time-series dataset for modelling handoff and return a compact structural summary.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "domain": {
            "type": "string",
            "description": "Optional domain hint such as generic, traffic, clinical, wearable, fmri, eeg."
          },
          "budget": {
            "type": "string",
            "enum": [
              "lean",
              "balanced",
              "deep"
            ]
          },
          "audience": {
            "type": "string"
          }
        },
        "additionalProperties": true
      }
    },
    {
      "name": "ts_compare",
      "description": "Compare two time-series inputs and stop early if the signal is already clear.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "mode": {
            "type": "string",
            "enum": [
              "auto",
              "series",
              "profile"
            ]
          },
          "budget": {
            "type": "string",
            "enum": [
              "lean",
              "balanced",
              "deep"
            ]
          }
        },
        "additionalProperties": true
      }
    },
    {
      "name": "ts_route",
      "description": "Route a natural-language time-series task to the right EchoTime entry point and companion tools.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "task": {
            "type": "string"
          },
          "has_reference": {
            "type": "boolean"
          }
        },
        "required": [
          "task"
        ],
        "additionalProperties": false
      }
    }
  ]
}
```
