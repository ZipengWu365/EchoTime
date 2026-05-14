# EchoTime agent-driving guide

Agent-driving is a lightweight orchestration layer that helps an LLM or application choose the smallest useful EchoTime workflow and export a compact context bundle.

## Token-saving principles

- Start with the cheapest informative move.
- Stop early when the signal is already clear.
- Upgrade to structural comparison only when raw shape is ambiguous or the question is structural.
- Render summary cards and narratives from existing profiles instead of recomputing analysis.
- Pass compact context bundles back into the agent instead of full raw reports when the next step only needs the gist.

## Main API

- `AgentDriver(goal=..., budget='lean|balanced|deep')`
- `agent_drive(data, reference=None, goal=..., budget=...)`
- `agent_context(profile_or_similarity_report, budget='lean')`

## Budget modes

- **lean:** Do the cheapest sufficient move and stop when the signal is clear.
- **balanced:** Add structural/profile comparison when ambiguity remains.
- **deep:** Allow rolling similarity and a fuller context bundle for regime-sensitive questions.

## Good goal prompts

- Explain this dataset to a non-technical collaborator
- Decide whether repo A's growth curve resembles repo B
- Compare these two assets but keep the context compact for another LLM step
- Find out whether two datasets are the same kind of temporal problem
