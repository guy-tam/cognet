# services/ingestion

## Purpose
Source connectors for raw data collection. Each connector fetches data from one source family and parses it into `RawSourceRecord` objects for downstream normalization.

## Source Families
| Family | Connector | Status |
|---|---|---|
| `job_postings` | `connectors/job_postings.py` | Stub (MVP) |
| `trend_signals` | `connectors/trend_signals.py` | Stub (MVP) |
| `internal_supply` | `connectors/internal_supply.py` | Stub (MVP) |

## Connector Interface
All connectors extend `BaseConnector` (`base_connector.py`), which defines:
- `fetch(run_id, **kwargs) -> list[dict]` — fetch raw payloads from source
- `parse(raw_item, run_id) -> RawSourceRecord | None` — parse a single raw item
- `run(run_id, **kwargs) -> tuple[list[RawSourceRecord], list[Exception]]` — full fetch+parse cycle with error collection

Partial success is valid — errors are collected, not raised.

## Adding New Connectors
Follow the source addition policy in `docs/governance/source-catalog.md`:
1. Subclass `BaseConnector` and implement `fetch` and `parse`.
2. Register the source in the source catalog with trust tier and data freshness SLA.
3. Add unit tests for both happy-path and parse-failure cases.
4. Do not modify existing connectors to add new source logic — one file per source.
