# Background Jobs — COGNET LDI Engine

## Choice: Celery with Redis broker

Celery was chosen over Dramatiq for:
- Mature ecosystem and broad community support
- Native Redis broker support
- Built-in periodic scheduling (Celery Beat)
- Good monitoring tools (Flower)

## Tasks

| Task | Name | Description |
|------|------|-------------|
| `run_full_pipeline` | `cognet.pipeline.run_full` | Full intelligence pipeline: ingest → normalize → agents → signals → rank → opportunities |
| `run_ingestion_only` | `cognet.pipeline.run_ingestion_only` | Ingestion step only (for testing connectors) |

## Running

```bash
# Start worker
celery -A app.jobs.celery_app worker --loglevel=info

# Start beat scheduler
celery -A app.jobs.celery_app beat --loglevel=info

# Start Flower monitoring (optional)
celery -A app.jobs.celery_app flower --port=5555
```

## Triggering manually

```python
from app.jobs.pipeline_tasks import run_full_pipeline
result = run_full_pipeline.delay(country_code="IL", language_code="he")
print(result.get(timeout=120))
```

## Schedule

| Job | Frequency | Args |
|-----|-----------|------|
| Full Pipeline (IL/he) | Every 24 hours | country_code="IL", language_code="he" |

## Cost Awareness
- Pipeline runs are expensive (LLM calls if enabled, source API calls)
- Default schedule is daily — do not reduce to sub-hourly without reviewing cost implications
- Use `run_ingestion_only` for testing without full pipeline overhead
