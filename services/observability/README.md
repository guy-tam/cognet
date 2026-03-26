# Observability Service

## Purpose
Structured logging hooks and metrics for pipeline and service observability.

## Key Files
- `metrics.py` — `track_step` context manager, pipeline start/end logging

## MVP Approach
Structured logging with Python `logging` module. Designed for easy OpenTelemetry expansion.

## Usage
```python
from services.observability.metrics import track_step

with track_step("normalize", run_id="abc-123") as ctx:
    # do work
    ctx["record_count"] = 15
```
