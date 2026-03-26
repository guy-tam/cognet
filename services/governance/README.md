# Governance Service

## Purpose
Scoring governance, taxonomy change tracking, and source trust policy enforcement.

## Current State (MVP)
- Scoring weights defined in `services/ranking/weights.py` with documented governance process
- Source trust tiers defined in `shared/enums/signals.py`
- Classification thresholds in `services/ranking/engine.py`
- Governance documentation in `docs/governance/`

## Rules
- Weight changes require: docs update + unit test update + version note
- Taxonomy changes require: alias mapping + docs update + migration
- Source additions require: documentation per source-catalog.md policy
