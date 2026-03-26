# COGNET LDI Engine — API Contracts

**Version:** 1.0 (v1)
**Status:** Active
**Last Updated:** 2026-03-26
**Owner:** Engineering

---

## 1. API Versioning Approach

All production endpoints are versioned under `/v1/`. The version prefix is part of the URL path, not a header. This makes versions explicit and cacheable.

```
https://api.cognet.internal/v1/opportunities
https://api.cognet.internal/v1/pipeline/status
```

**Version lifecycle:**
- A new major version (`/v2/`) is introduced only when breaking changes are required (field removal, type changes, semantic changes to existing fields)
- Additive changes (new optional fields, new endpoints) are made within the existing version without bumping
- Deprecated versions will remain available for a minimum of 90 days after the deprecation notice

**Version negotiation:** Clients may optionally pass `Accept: application/vnd.cognet.v1+json` but the URL path version takes precedence.

---

## 2. Auth Assumption for MVP

**MVP (v1):** The API is an internal tool accessible only within the private network (VPN or internal k8s network). Authentication is enforced via one of:

1. **IP allowlist** at the Nginx/load balancer level — requests from outside the allowed CIDR range are rejected with `403 Forbidden`
2. **Static API key** passed in the `X-API-Key` header — a single shared key for the Admin UI and any internal consumers

**Post-MVP:** JWT-based authentication with role claims (`analyst`, `admin`, `read_only`). The Admin UI will authenticate users via an identity provider (e.g., Google Workspace SSO) and exchange for short-lived JWTs. The API will validate JWTs and enforce role-based access on mutation endpoints.

**For MVP, all endpoints are read-only.** Mutation operations (review decisions, taxonomy updates) are performed through the Admin UI backend-for-frontend layer, not directly through this public-facing API.

---

## 3. Common Conventions

### Base URL
```
https://api.cognet.internal
```

### Content Type
All requests and responses use `application/json`. Requests with a body must include `Content-Type: application/json`.

### Timestamps
All timestamps in responses are ISO 8601 format with UTC timezone: `2026-03-26T14:30:00Z`

### Dates
All dates (without time component) are `YYYY-MM-DD` format: `2026-03-01`

### Numeric Scores
All scores are floats in the range `[0.0, 1.0]` unless otherwise specified. Represented as JSON numbers with up to 4 decimal places.

### Language Codes
ISO 639-1 two-letter codes: `en`, `he`

### Country Codes
ISO 3166-1 alpha-2 two-letter codes: `IL`, `US`, `DE`

### Null vs. Omitted Fields
Fields that are not applicable for a given record are returned as `null` (not omitted). This ensures client code can rely on a stable schema shape.

---

## 4. Error Response Format

All errors follow a consistent structure:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object | null",
    "request_id": "string (UUID, matches X-Request-ID response header)"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|---|---|---|
| `400 Bad Request` | `INVALID_PARAMS` | Request parameters fail validation |
| `400 Bad Request` | `INVALID_FILTER` | A filter value is not a recognized enum member |
| `401 Unauthorized` | `AUTH_REQUIRED` | No credentials provided |
| `403 Forbidden` | `ACCESS_DENIED` | Credentials provided but insufficient permissions |
| `404 Not Found` | `NOT_FOUND` | Resource does not exist |
| `422 Unprocessable Entity` | `SCHEMA_ERROR` | Request body fails schema validation |
| `429 Too Many Requests` | `RATE_LIMITED` | Request rate exceeded (not enforced in MVP) |
| `500 Internal Server Error` | `INTERNAL_ERROR` | Unexpected server error |
| `503 Service Unavailable` | `SERVICE_UNAVAILABLE` | Database or dependent service unreachable |

### Example Error Response

```json
{
  "error": {
    "code": "INVALID_PARAMS",
    "message": "Parameter 'time_window_days' must be one of: 30, 90, 180",
    "details": {
      "field": "time_window_days",
      "received": 45,
      "allowed": [30, 90, 180]
    },
    "request_id": "a3f2c1d4-89ab-4c3e-b12f-7e9d5e3a0012"
  }
}
```

---

## 5. Pagination Semantics

Large result sets use **cursor-based pagination** (not offset-based). Cursor pagination is stable under concurrent writes and performs better at scale.

### Pagination Request Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 20 | Records per page. Max: 100 |
| `cursor` | string (opaque) | null | Cursor from previous response `pagination.next_cursor`. Pass null or omit for first page. |

### Pagination Response Object

```json
{
  "pagination": {
    "limit": 20,
    "total_count": 147,
    "has_next": true,
    "next_cursor": "eyJpZCI6InV1aWQiLCJzY29yZSI6MC43NX0=",
    "has_previous": false,
    "previous_cursor": null
  }
}
```

`next_cursor` and `previous_cursor` are base64-encoded opaque strings. Clients must not attempt to decode or construct cursors manually.

`total_count` reflects the total matching the applied filters, not just the current page.

---

## 6. Filtering and Sorting Semantics

### Filter Parameters

Filters are passed as query string parameters. Multiple values for a single filter use repeated parameters: `?country=IL&country=US`

All filter parameters are optional. Omitted filters return all records.

### Sort Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sort_by` | string | `composite_score` | Field to sort by |
| `sort_dir` | string | `desc` | `asc` or `desc` |

Sortable fields for opportunities: `composite_score`, `created_at`, `status_changed_at`, `record_count`, `confidence`

---

## 7. Endpoints

---

### 7.1 GET /health

**Purpose:** Liveness check. Returns 200 if the API process is running. Does not check database connectivity.

**Method:** `GET`
**Route:** `/health`
**Auth Required:** No
**Rate Limited:** No

**Request Parameters:** None

**Response: 200 OK**
```json
{
  "status": "ok",
  "timestamp": "2026-03-26T14:30:00Z"
}
```

**Error States:**
- This endpoint does not return errors. If the process is running, it returns 200. If the process is down, the connection is refused.

---

### 7.2 GET /ready

**Purpose:** Readiness check. Returns 200 only if all critical dependencies (database, Redis) are reachable. Used by load balancers to gate traffic.

**Method:** `GET`
**Route:** `/ready`
**Auth Required:** No
**Rate Limited:** No

**Request Parameters:** None

**Response: 200 OK**
```json
{
  "status": "ready",
  "timestamp": "2026-03-26T14:30:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

**Response: 503 Service Unavailable** (when any check fails)
```json
{
  "status": "not_ready",
  "timestamp": "2026-03-26T14:30:00Z",
  "checks": {
    "database": "ok",
    "redis": "error: connection refused"
  }
}
```

**Notes:**
- Database check executes `SELECT 1` via the connection pool
- Redis check executes `PING`
- Response time target: < 200ms

---

### 7.3 GET /v1/opportunities

**Purpose:** List opportunity briefs with filtering, sorting, and pagination.

**Method:** `GET`
**Route:** `/v1/opportunities`
**Auth Required:** Yes (MVP: IP allowlist or X-API-Key)

**Request Parameters (Query String):**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `status` | string (repeatable) | No | `surfaced,analyst_review,approved` | Filter by status. Allowed values: `draft`, `surfaced`, `analyst_review`, `approved`, `rejected`, `archived` |
| `country` | string (repeatable) | No | all | ISO 3166-1 alpha-2 country code(s) |
| `language` | string (repeatable) | No | all | ISO 639-1 language code(s) |
| `entity_type` | string | No | all | `skill` or `topic` |
| `time_window_days` | int (repeatable) | No | all | Filter by signal time window: 30, 90, or 180 |
| `min_score` | float | No | 0.0 | Minimum composite score (0.0–1.0) |
| `min_confidence` | float | No | 0.0 | Minimum confidence score (0.0–1.0) |
| `sort_by` | string | No | `composite_score` | Field to sort by |
| `sort_dir` | string | No | `desc` | Sort direction: `asc` or `desc` |
| `limit` | int | No | 20 | Records per page (1–100) |
| `cursor` | string | No | null | Pagination cursor |
| `locale` | string | No | `en` | Response locale for translated fields: `en` or `he` |

**Response: 200 OK**

```json
{
  "data": [<OpportunityBriefObject>, ...],
  "pagination": {
    "limit": 20,
    "total_count": 147,
    "has_next": true,
    "next_cursor": "eyJ...",
    "has_previous": false,
    "previous_cursor": null
  },
  "filters_applied": {
    "status": ["surfaced", "analyst_review", "approved"],
    "country": null,
    "language": null,
    "entity_type": null,
    "time_window_days": null,
    "min_score": 0.0,
    "min_confidence": 0.0
  }
}
```

**Error States:**
- `400 INVALID_PARAMS` — if `limit` is out of range or `time_window_days` is not in [30, 90, 180]
- `400 INVALID_FILTER` — if `status`, `entity_type`, `sort_by`, or `sort_dir` is not a recognized value
- `500 INTERNAL_ERROR` — database query failure

---

### 7.4 GET /v1/opportunities/top

**Purpose:** Return the top-N highest-scoring approved or surfaced opportunities globally or for a given market. Optimized for dashboard use.

**Method:** `GET`
**Route:** `/v1/opportunities/top`
**Auth Required:** Yes

**Request Parameters (Query String):**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `n` | int | No | 10 | Number of top opportunities to return (1–50) |
| `country` | string | No | null | ISO 3166-1 alpha-2. If null, returns global top-N across all markets |
| `language` | string | No | null | ISO 639-1. If null, includes all languages |
| `time_window_days` | int | No | 90 | Signal time window: 30, 90, or 180 |
| `status` | string (repeatable) | No | `approved,surfaced` | Statuses to include |
| `locale` | string | No | `en` | Response locale: `en` or `he` |

**Response: 200 OK**

```json
{
  "data": [<OpportunityBriefObject>, ...],
  "query_context": {
    "country": "IL",
    "language": "he",
    "time_window_days": 90,
    "n": 10,
    "as_of": "2026-03-26T14:30:00Z"
  }
}
```

**Notes:**
- Results are sorted by `composite_score DESC` always (no custom sort for this endpoint)
- Response is not paginated (max N = 50)
- `as_of` reflects the `computed_at` timestamp of the most recent pipeline run included in the results

**Error States:**
- `400 INVALID_PARAMS` — `n` out of range, invalid time_window_days

---

### 7.5 GET /v1/opportunities/by-market

**Purpose:** Return opportunities grouped and summarized by market (country + language combination). Useful for market comparison views.

**Method:** `GET`
**Route:** `/v1/opportunities/by-market`
**Auth Required:** Yes

**Request Parameters (Query String):**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `time_window_days` | int | No | 90 | Signal time window: 30, 90, or 180 |
| `min_score` | float | No | 0.55 | Minimum composite score to include |
| `status` | string (repeatable) | No | `approved,surfaced` | |
| `top_n_per_market` | int | No | 5 | Top-N opportunities per market (1–20) |
| `locale` | string | No | `en` | |

**Response: 200 OK**

```json
{
  "data": [
    {
      "market": {
        "country_code": "IL",
        "country_name": "Israel",
        "language_code": "he",
        "language_name": "Hebrew",
        "is_rtl": true
      },
      "summary": {
        "total_opportunities": 23,
        "avg_composite_score": 0.7234,
        "top_score": 0.9101,
        "opportunities_this_run": 4
      },
      "top_opportunities": [<OpportunityBriefObject (condensed)>, ...]
    },
    {
      "market": {
        "country_code": "US",
        "country_name": "United States",
        "language_code": "en",
        "language_name": "English",
        "is_rtl": false
      },
      "summary": {
        "total_opportunities": 71,
        "avg_composite_score": 0.6891,
        "top_score": 0.9445,
        "opportunities_this_run": 12
      },
      "top_opportunities": [<OpportunityBriefObject (condensed)>, ...]
    }
  ],
  "meta": {
    "time_window_days": 90,
    "markets_found": 7,
    "generated_at": "2026-03-26T14:30:00Z"
  }
}
```

**Condensed Opportunity Object** (as used in `top_opportunities` arrays):

```json
{
  "id": "uuid",
  "title": "string (locale-appropriate)",
  "entity_type": "skill | topic",
  "composite_score": 0.0,
  "confidence": 0.0,
  "status": "string"
}
```

**Error States:**
- `400 INVALID_PARAMS` — invalid time_window_days or top_n_per_market out of range

---

### 7.6 GET /v1/pipeline/status

**Purpose:** Return current and recent pipeline run status. Used by Admin UI dashboard and monitoring integrations.

**Method:** `GET`
**Route:** `/v1/pipeline/status`
**Auth Required:** Yes

**Request Parameters (Query String):**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `limit` | int | No | 5 | Number of recent pipeline runs to return (1–20) |
| `include_stages` | bool | No | true | Whether to include per-stage breakdown in response |

**Response: 200 OK**

```json
{
  "current_run": <PipelineRunObject | null>,
  "recent_runs": [<PipelineRunObject>, ...],
  "system_health": {
    "last_successful_run_at": "2026-03-26T06:00:00Z",
    "hours_since_last_success": 8,
    "consecutive_failures": 0,
    "status": "healthy"
  }
}
```

**`system_health.status` values:**

| Value | Condition |
|---|---|
| `healthy` | Last run succeeded, `hours_since_last_success < 28` |
| `stale` | No successful run in > 28 hours (missed daily cadence) |
| `degraded` | Last run was `partially_failed` |
| `failing` | `consecutive_failures >= 2` |

**Error States:**
- `500 INTERNAL_ERROR`

---

## 8. Opportunity Brief Object Schema (Full)

Used in `GET /v1/opportunities` and `GET /v1/opportunities/top` responses.

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "surfaced",
  "status_changed_at": "2026-03-25T10:00:00Z",
  "created_at": "2026-03-25T09:50:00Z",
  "updated_at": "2026-03-25T10:00:00Z",

  "entity": {
    "id": "uuid",
    "type": "topic",
    "slug": "llm-application-development",
    "name": "LLM Application Development",
    "name_he": "פיתוח יישומי LLM"
  },

  "market": {
    "country_code": "IL",
    "country_name": "Israel",
    "language_code": "he",
    "language_name": "Hebrew",
    "is_rtl": true
  },

  "time_window": {
    "days": 90,
    "window_start": "2025-12-26",
    "window_end": "2026-03-26"
  },

  "content": {
    "locale": "he",
    "title": "פיתוח יישומי בינה מלאכותית עם מודלי שפה גדולים",
    "title_en": "LLM Application Development",
    "title_he": "פיתוח יישומי בינה מלאכותית עם מודלי שפה גדולים",
    "summary": "string (locale-appropriate summary text)",
    "summary_en": "string",
    "summary_he": "string",
    "why_now": "string (locale-appropriate urgency text)",
    "why_now_en": "string",
    "why_now_he": "string"
  },

  "score_breakdown": {
    "composite_score": 0.8724,
    "confidence": 0.912,
    "components": {
      "demand": {
        "raw_value": 342,
        "normalized_value": 0.891,
        "weight": 0.35,
        "contribution": 0.312
      },
      "velocity": {
        "raw_value": 0.47,
        "normalized_value": 0.784,
        "weight": 0.25,
        "contribution": 0.196
      },
      "gap": {
        "raw_value": 0.89,
        "normalized_value": 0.89,
        "weight": 0.30,
        "contribution": 0.267
      },
      "search": {
        "raw_value": 72.0,
        "normalized_value": 0.720,
        "weight": 0.10,
        "contribution": 0.072
      }
    },
    "rank_within_window": 3,
    "score_version": "v1.0"
  },

  "demand_metrics": {
    "posting_volume": 342,
    "posting_volume_prior_window": 233,
    "trend_velocity_pct": 46.8,
    "search_interest_score": 72.0,
    "search_interest_velocity_pct": 12.3,
    "supply_coverage_score": 0.11,
    "supply_gap_score": 0.89,
    "record_count": 342,
    "seniority_distribution": {
      "entry": 45,
      "mid": 148,
      "senior": 122,
      "lead": 27,
      "unknown": 0
    }
  },

  "evidence": {
    "count": 10,
    "items": [
      {
        "id": "uuid",
        "type": "job_posting",
        "label": "Senior LLM Engineer at Wix, Tel Aviv",
        "label_he": "מהנדס LLM בכיר בוויקס, תל אביב",
        "display_date": "2026-03-20",
        "value": null,
        "value_unit": null
      },
      {
        "id": "uuid",
        "type": "skill_cluster",
        "label": "LangChain mentioned in 89 postings in Israel (90d)",
        "label_he": "LangChain מוזכר ב-89 משרות בישראל (90 ימים)",
        "display_date": "2026-03-26",
        "value": 89,
        "value_unit": "job_postings"
      },
      {
        "id": "uuid",
        "type": "trend_signal",
        "label": "Search interest for 'LLM development' +47% in Israel (90d)",
        "label_he": "עניין חיפוש ב'פיתוח LLM' עלה ב-47% בישראל (90 ימים)",
        "display_date": "2026-03-26",
        "value": 47.0,
        "value_unit": "percent_change"
      },
      {
        "id": "uuid",
        "type": "supply_gap",
        "label": "Cognet has 1 course partially covering this topic (coverage: 11%)",
        "label_he": "לקוגנט יש קורס אחד המכסה חלקית נושא זה (כיסוי: 11%)",
        "display_date": "2026-03-26",
        "value": 0.11,
        "value_unit": "coverage_fraction"
      }
    ]
  },

  "pipeline_context": {
    "pipeline_run_id": "uuid",
    "signal_snapshot_id": "uuid",
    "computed_at": "2026-03-26T06:30:00Z"
  },

  "locale_hints": {
    "response_locale": "he",
    "is_rtl": true,
    "title_field": "title_he",
    "summary_field": "summary_he"
  }
}
```

---

## 9. Pipeline Run Object Schema

Used in `GET /v1/pipeline/status` response.

```json
{
  "id": "uuid",
  "status": "completed",
  "triggered_by": "schedule",
  "triggered_at": "2026-03-26T06:00:00Z",
  "started_at": "2026-03-26T06:00:05Z",
  "completed_at": "2026-03-26T06:47:23Z",
  "duration_seconds": 2838,
  "stages": {
    "ingestion": {
      "status": "completed",
      "records_in": 0,
      "records_out": 12847,
      "errors": 0,
      "duration_ms": 124500
    },
    "normalization": {
      "status": "completed",
      "records_in": 12847,
      "records_out": 11203,
      "errors": 14,
      "duration_ms": 98200
    },
    "enrichment": {
      "status": "completed",
      "records_in": 11203,
      "records_out": 11203,
      "errors": 47,
      "duration_ms": 412000
    },
    "signals": {
      "status": "completed",
      "snapshots_created": 847,
      "entities_covered": 312,
      "duration_ms": 34200
    },
    "ranking": {
      "status": "completed",
      "snapshots_ranked": 847,
      "duration_ms": 8100
    },
    "opportunities": {
      "status": "completed",
      "candidates_evaluated": 234,
      "briefs_created": 18,
      "briefs_updated": 43,
      "briefs_skipped": 173,
      "duration_ms": 156300
    }
  },
  "error_summary": null,
  "config_snapshot": {
    "rank_weights": {
      "demand": 0.35,
      "velocity": 0.25,
      "gap": 0.30,
      "search": 0.10
    },
    "opportunity_score_threshold": 0.55,
    "signal_time_windows": [30, 90, 180]
  }
}
```

---

## 10. Response Headers

All API responses include:

| Header | Value | Description |
|---|---|---|
| `Content-Type` | `application/json; charset=utf-8` | Always |
| `X-Request-ID` | UUID | Unique request identifier for log correlation |
| `X-API-Version` | `v1` | API version served |
| `Cache-Control` | `no-store` (default) or `max-age=N` for `/top` | Caching guidance |
| `X-Response-Time` | milliseconds as string, e.g., `"142"` | Server processing time |

### Caching Notes

`GET /v1/opportunities/top` responses may be cached for up to 5 minutes at the Nginx layer (configurable). All other endpoints return `Cache-Control: no-store` to ensure analysts always see current state.

---

## 11. Pagination Example Walkthrough

**Page 1 request:**
```
GET /v1/opportunities?status=surfaced&country=IL&limit=3&sort_by=composite_score&sort_dir=desc
```

**Page 1 response (partial):**
```json
{
  "data": [...3 items...],
  "pagination": {
    "limit": 3,
    "total_count": 23,
    "has_next": true,
    "next_cursor": "eyJpZCI6InV1aWQtMyIsInNjb3JlIjowLjg0fQ==",
    "has_previous": false,
    "previous_cursor": null
  }
}
```

**Page 2 request:**
```
GET /v1/opportunities?status=surfaced&country=IL&limit=3&sort_by=composite_score&sort_dir=desc&cursor=eyJpZCI6InV1aWQtMyIsInNjb3JlIjowLjg0fQ==
```

All filter and sort parameters must be repeated identically across paginated requests. Changing sort or filter parameters while passing a cursor from a previous query returns `400 INVALID_PARAMS` with error code `CURSOR_CONTEXT_MISMATCH`.

---

## 12. OpenAPI / Swagger

A machine-readable OpenAPI 3.1 specification is auto-generated by FastAPI and served at:

```
GET /docs        → Swagger UI (interactive browser)
GET /redoc       → ReDoc UI (read-only documentation)
GET /openapi.json → Raw OpenAPI 3.1 JSON schema
```

These endpoints are only accessible within the internal network (same access restrictions as the API itself).
