# Security Policy

## Supported versions

| version | status |
|---|---|
| `0.16.x` | supported |
| `main` | best-effort support |
| `< 0.17.1` | not supported for security fixes |

## Reporting a vulnerability

Please report suspected vulnerabilities privately to `zxw365@student.bham.ac.uk`.

When possible, include:

- affected version or commit
- impact and attack surface
- clear reproduction steps
- whether the issue is local-only or remotely triggerable
- a synthetic proof of concept rather than real sensitive data

Please do not open a public GitHub issue for an undisclosed vulnerability.

## What belongs here

Security-relevant reports include issues such as:

- unintended code execution or shell injection
- unsafe file writes or path traversal
- local demo server exposure or unsafe defaults
- secret leakage in generated artifacts or logs
- dependency confusion or packaging integrity problems
- unsafe HTML/report generation that could execute attacker-controlled content

For ordinary bugs, docs corrections, feature requests, or hardening ideas without active security impact, use the public issue tracker instead.

## Response expectations

- acknowledgement target: within 5 business days
- triage update: after initial reproduction and severity review
- coordinated disclosure: preferred after a fix or mitigation is available

This is a small research-oriented project, so timelines are best-effort rather than formally guaranteed.

## Privacy note

Do not send real patient, clinical, or otherwise regulated data in a security report. Minimal synthetic reproductions are preferred.
