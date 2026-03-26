# services/agents

## Purpose
Bounded specialist components for domain analysis. Agents are **not** autonomous swarms — each agent has a single defined purpose, typed inputs/outputs, and explicit non-goals. Agent outputs are schema-bound. LLM-backed agents (future) must validate their output against the defined schema before returning.

## Operational MVP Agents
These agents are wired into the pipeline and produce real output:

| Agent | File | Purpose |
|---|---|---|
| `TrendAnalysisAgent` | `trend_analysis_agent.py` | Analyze trend/search signals per market to identify rising topics |
| `JobDemandAgent` | `job_demand_agent.py` | Quantify employer skill/topic demand from job posting data |
| `SkillGapAgent` | `skill_gap_agent.py` | Compare demanded skills against internal supply to identify gaps |
| `TopicPrioritizationAgent` | `topic_prioritization_agent.py` | Combine trend, job demand, and gap signals into a unified topic ranking |

## Scaffold-Only Agents (Not Operational in MVP)
These agents exist as typed placeholders. They return `success=False` with an informative error message. Do not wire them into the pipeline until they are implemented.

| Agent | File | Planned Purpose |
|---|---|---|
| `MarketResearchAgent` | `market_research_agent.py` | Broader market context — economic indicators, industry reports |
| `RegionCultureFitAgent` | `region_culture_fit_agent.py` | Regional learning culture and language preference signals |
| `LearningOpportunityAgent` | `learning_opportunity_agent.py` | Expand identified opportunities into specific content proposals |
| `ConsistencyValidationAgent` | `consistency_validation_agent.py` | Cross-agent output validation and data quality flagging |

## Rules
- All agent outputs must be **schema-bound** — define the output structure in the agent's docstring and return it consistently.
- LLM-backed agents (when introduced) must validate LLM output against the schema before returning `AgentResult`.
- Agents must not access databases or external APIs directly — pass pre-fetched data via `run(**inputs)`.
- Log every invocation with: `agent_name`, `run_id`, `input_summary`, `output_summary`, `duration_ms`.
- Failures must return `AgentResult(success=False, error=...)` — never raise unhandled exceptions from `run()`.

## Base Interface
See `base_agent.py` — `BaseAgent` (ABC) and `AgentResult` dataclass.
