# Function-calling examples

## OpenAI-style tools

```json
{
  "schema_version": "1.0.0",
  "functions": [
    {
      "type": "function",
      "function": {
        "name": "ts_profile",
        "description": "Profile a time-series dataset for modelling handoff and return a compact structural summary.",
        "parameters": {
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
      }
    },
    {
      "type": "function",
      "function": {
        "name": "ts_compare",
        "description": "Compare two time-series inputs and stop early if the signal is already clear.",
        "parameters": {
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
      }
    },
    {
      "type": "function",
      "function": {
        "name": "ts_route",
        "description": "Route a natural-language time-series task to the right EchoTime entry point and companion tools.",
        "parameters": {
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
    }
  ]
}
```
