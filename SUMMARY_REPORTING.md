# Summary card and narrative report guide

This document explains the two reporting layers added for cross-disciplinary teams.

## Why they exist

In many projects, the bottleneck is not computing a metric. The bottleneck is explaining to another person:

- what kind of time-series dataset this is
- what the main structural issues are
- why those issues matter for the project
- what the team should do next

The summary card and the narrative report are built for that step.

## Summary card

Use the summary card when someone wants a **short, practical readout**.

Typical readers:

- clinicians
- product managers
- study coordinators
- operations partners
- collaborators outside the method team

What it emphasizes:

- executive summary
- top structure axes in plain language
- main watchouts
- analysis opportunities
- recommended next actions

API:

```python
profile.to_summary_card_markdown()
profile.to_summary_card_json()
```

CLI:

```bash
EchoTime data.npy --format summary-card
```

## Narrative report

Use the narrative report when someone wants a **full prose explanation**.

Typical readers:

- domain experts reviewing a dataset handoff
- coauthors writing methods-light sections
- lab members onboarding to a dataset
- project teams deciding validation strategy

What it emphasizes:

- what the dataset is in everyday language
- what stands out structurally
- why that matters for common tasks
- what could go wrong if structure is ignored
- practical next steps
- reliability and interpretation guardrails

API:

```python
profile.to_narrative_report()
```

CLI:

```bash
EchoTime data.npy --format narrative
```

## How to use them together

A good pattern is:

1. Run the full profile for technical inspection.
2. Export a dataset card for reproducibility.
3. Export a summary card for the broader team.
4. Export a narrative report when decisions need explanation.

## Good defaults by audience

### General cross-disciplinary audience
Use the default audience.

### Clinical audience
Use `audience="clinical"` when you want the surrounding workflow and examples to stay clinically framed.

### Product or operations audience
Use `audience="product"` or `audience="operations"` if the dataset is closer to traffic, demand, or operational telemetry.

### Neuroscience audience
Use `audience="neuroscience"` when you want the surrounding examples to match neural time-series work.
