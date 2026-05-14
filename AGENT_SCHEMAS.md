# Agent and function-calling schemas

v0.17.0 exposes a compare-first tool surface that stays callable from outside the package:

- `ts_profile({data_ref, input_kind, timestamps_ref, domain, budget, audience})`
- `ts_compare({left_ref, right_ref, left_timestamps_ref, right_timestamps_ref, mode, budget})`
- `ts_route({task, available_inputs, has_reference})`

All three tools return a stable envelope with:

- `schema_version`
- `tool`
- `ok`
- `input_contract`
- `confidence`
- `limitations`
- `evidence`
- `recommended_next_step`
- `next_actions`
- `error`

## OpenAI-style function specs

```json
{
  "schema_version": "2.4.0",
  "functions": [
    {
      "type": "function",
      "function": {
        "name": "ts_profile",
        "description": "Profile a time-series dataset for modelling handoff and return a compact structural summary.",
        "parameters": {
          "type": "object",
          "properties": {
            "data_ref": {
              "description": "Array-like data, typed wrapper, DataFrame-like table, or a caller-managed path/URI.",
              "oneOf": [
                {
                  "type": "string",
                  "description": "Path, URI, or caller-managed handle."
                },
                {
                  "type": "array",
                  "description": "Inline array-like numeric values."
                },
                {
                  "type": "object",
                  "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
                }
              ]
            },
            "input_kind": {
              "type": "string",
              "enum": [
                "auto",
                "array",
                "table",
                "irregular",
                "event_stream",
                "path_or_uri",
                "dataframe_like",
                "typed_wrapper"
              ]
            },
            "timestamps_ref": {
              "description": "Optional timestamps aligned with data_ref for irregular or explicitly timed series.",
              "oneOf": [
                {
                  "type": "string",
                  "description": "Path, URI, or caller-managed handle."
                },
                {
                  "type": "array",
                  "description": "Inline array-like numeric values."
                },
                {
                  "type": "object",
                  "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
                }
              ]
            },
            "domain": {
              "type": "string",
              "description": "Optional domain hint such as generic, traffic, clinical, wearable, fmri, or eeg."
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
              "type": "string",
              "description": "general, agent, clinical, product, neuroscience, etc."
            },
            "safe": {
              "type": "boolean"
            }
          },
          "required": [
            "data_ref"
          ],
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
            "left_ref": {
              "description": "Primary series or dataset reference.",
              "oneOf": [
                {
                  "type": "string",
                  "description": "Path, URI, or caller-managed handle."
                },
                {
                  "type": "array",
                  "description": "Inline array-like numeric values."
                },
                {
                  "type": "object",
                  "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
                }
              ]
            },
            "right_ref": {
              "description": "Reference series or dataset to compare against.",
              "oneOf": [
                {
                  "type": "string",
                  "description": "Path, URI, or caller-managed handle."
                },
                {
                  "type": "array",
                  "description": "Inline array-like numeric values."
                },
                {
                  "type": "object",
                  "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
                }
              ]
            },
            "left_timestamps_ref": {
              "description": "Optional timestamps for left_ref.",
              "oneOf": [
                {
                  "type": "string",
                  "description": "Path, URI, or caller-managed handle."
                },
                {
                  "type": "array",
                  "description": "Inline array-like numeric values."
                },
                {
                  "type": "object",
                  "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
                }
              ]
            },
            "right_timestamps_ref": {
              "description": "Optional timestamps for right_ref.",
              "oneOf": [
                {
                  "type": "string",
                  "description": "Path, URI, or caller-managed handle."
                },
                {
                  "type": "array",
                  "description": "Inline array-like numeric values."
                },
                {
                  "type": "object",
                  "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
                }
              ]
            },
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
            },
            "safe": {
              "type": "boolean"
            }
          },
          "required": [
            "left_ref",
            "right_ref"
          ],
          "additionalProperties": true
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "ts_route",
        "description": "Route a natural-language time-series task to the smallest useful echotime tool and expected output.",
        "parameters": {
          "type": "object",
          "properties": {
            "task": {
              "type": "string"
            },
            "available_inputs": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "Optional caller-side hints such as ['data_ref'] or ['left_ref', 'right_ref']."
            },
            "has_reference": {
              "type": "boolean"
            },
            "safe": {
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

## MCP-style tool descriptors

```json
{
  "schema_version": "2.4.0",
  "tools": [
    {
      "name": "ts_profile",
      "description": "Profile a time-series dataset for modelling handoff and return a compact structural summary.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "data_ref": {
            "description": "Array-like data, typed wrapper, DataFrame-like table, or a caller-managed path/URI.",
            "oneOf": [
              {
                "type": "string",
                "description": "Path, URI, or caller-managed handle."
              },
              {
                "type": "array",
                "description": "Inline array-like numeric values."
              },
              {
                "type": "object",
                "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
              }
            ]
          },
          "input_kind": {
            "type": "string",
            "enum": [
              "auto",
              "array",
              "table",
              "irregular",
              "event_stream",
              "path_or_uri",
              "dataframe_like",
              "typed_wrapper"
            ]
          },
          "timestamps_ref": {
            "description": "Optional timestamps aligned with data_ref for irregular or explicitly timed series.",
            "oneOf": [
              {
                "type": "string",
                "description": "Path, URI, or caller-managed handle."
              },
              {
                "type": "array",
                "description": "Inline array-like numeric values."
              },
              {
                "type": "object",
                "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
              }
            ]
          },
          "domain": {
            "type": "string",
            "description": "Optional domain hint such as generic, traffic, clinical, wearable, fmri, or eeg."
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
            "type": "string",
            "description": "general, agent, clinical, product, neuroscience, etc."
          },
          "safe": {
            "type": "boolean"
          }
        },
        "required": [
          "data_ref"
        ],
        "additionalProperties": true
      }
    },
    {
      "name": "ts_compare",
      "description": "Compare two time-series inputs and stop early if the signal is already clear.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "left_ref": {
            "description": "Primary series or dataset reference.",
            "oneOf": [
              {
                "type": "string",
                "description": "Path, URI, or caller-managed handle."
              },
              {
                "type": "array",
                "description": "Inline array-like numeric values."
              },
              {
                "type": "object",
                "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
              }
            ]
          },
          "right_ref": {
            "description": "Reference series or dataset to compare against.",
            "oneOf": [
              {
                "type": "string",
                "description": "Path, URI, or caller-managed handle."
              },
              {
                "type": "array",
                "description": "Inline array-like numeric values."
              },
              {
                "type": "object",
                "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
              }
            ]
          },
          "left_timestamps_ref": {
            "description": "Optional timestamps for left_ref.",
            "oneOf": [
              {
                "type": "string",
                "description": "Path, URI, or caller-managed handle."
              },
              {
                "type": "array",
                "description": "Inline array-like numeric values."
              },
              {
                "type": "object",
                "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
              }
            ]
          },
          "right_timestamps_ref": {
            "description": "Optional timestamps for right_ref.",
            "oneOf": [
              {
                "type": "string",
                "description": "Path, URI, or caller-managed handle."
              },
              {
                "type": "array",
                "description": "Inline array-like numeric values."
              },
              {
                "type": "object",
                "description": "Typed wrapper, mapping, DataFrame-like object, or caller-side structured payload."
              }
            ]
          },
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
          },
          "safe": {
            "type": "boolean"
          }
        },
        "required": [
          "left_ref",
          "right_ref"
        ],
        "additionalProperties": true
      }
    },
    {
      "name": "ts_route",
      "description": "Route a natural-language time-series task to the smallest useful echotime tool and expected output.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "task": {
            "type": "string"
          },
          "available_inputs": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Optional caller-side hints such as ['data_ref'] or ['left_ref', 'right_ref']."
          },
          "has_reference": {
            "type": "boolean"
          },
          "safe": {
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
