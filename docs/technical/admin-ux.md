# Admin UX Specification — COGNET LDI Engine

## Overview

The COGNET admin interface is an internal intelligence tool used by learning strategists and content analysts to review, validate, and act on learning demand signals. It is not a consumer product. The UX must prioritize clarity, scanability, and trust — not visual novelty.

---

## 1. Internal Tool UX Principles

These principles govern every design and implementation decision in the admin shell:

**1. Clarity over aesthetics.**
Every element earns its place by communicating something useful. Remove anything decorative that does not aid comprehension.

**2. Fast to scan.**
Analysts review many opportunities in a session. Tables, score breakdowns, and evidence lists must be readable at a glance. Dense-but-readable is the goal. Whitespace is used to aid parsing, not to pad.

**3. Explanation-friendly.**
The engine produces opaque scores. The UI must surface the reasoning: what signals drove the score, what evidence exists, why the confidence level was assigned. Every score must be explainable without opening a database console.

**4. Practical above all.**
The analyst needs to make a decision: approve, reject, defer. The UI must support this workflow. The primary call to action on any opportunity is always visible.

**5. Low clutter.**
Secondary information (metadata, timestamps, IDs) is present but visually subordinate. It does not compete with actionable information.

**6. Predictable behavior.**
Loading states, error states, and empty states are always handled. The UI never shows a blank page or a spinner that runs forever without feedback.

---

## 2. Tech Stack

| Layer | Choice |
|---|---|
| Framework | Next.js 14+ with App Router |
| Language | TypeScript (strict mode) |
| Styling | Tailwind CSS with RTL support |
| Data fetching | Server Components + typed API client |
| State management | React context for locale/UI state; server state via Next.js cache |
| i18n | next-intl |
| Component pattern | Composable, typed, locale-aware |

All components are TypeScript-first. No untyped props. API response types are shared from a central `types/` package.

---

## 3. Component Structure

```
apps/admin/components/
  layout/
    AppShell.tsx          # outer layout wrapper, sets dir attribute
    Sidebar.tsx           # navigation sidebar
    TopBar.tsx            # header with locale switcher
  navigation/
    NavLink.tsx           # locale-aware nav link
    Breadcrumb.tsx        # page breadcrumb trail
  opportunities/
    OpportunityTable.tsx  # paginated sortable table
    OpportunityCard.tsx   # summary card for list views
    OpportunityDetail.tsx # full detail view layout
    ScoreBreakdown.tsx    # score family table + bar visualization
    EvidenceList.tsx      # expandable evidence items
    WhyNowSummary.tsx     # narrative summary block
    ClassificationBadge.tsx
  pipeline/
    PipelineStatusCard.tsx  # run summary card
    RunHistoryTable.tsx     # recent runs
    StepSummary.tsx         # per-step status
  filters/
    FilterPanel.tsx         # market, language, classification, score filters
    FilterChip.tsx          # active filter indicator
  shared/
    LocaleSwitcher.tsx      # EN/HE toggle
    LoadingSkeleton.tsx     # generic skeleton loader
    ErrorBoundary.tsx       # catches render errors
    ErrorState.tsx          # full-page and inline error displays
    EmptyState.tsx          # no-data illustrations and prompts
    ScoreBar.tsx            # single score visualization bar
    ConfidenceBadge.tsx     # confidence level indicator
```

---

## 4. Pages

### 4.1 Dashboard

**Route:** `/[locale]/dashboard`

**Purpose:** Landing page. Gives the analyst an immediate read on the system state.

**Layout:**

```
┌─────────────────────────────────────────────┐
│ [TopBar: COGNET LDI | locale switcher]       │
├──────────┬──────────────────────────────────┤
│          │  Pipeline Status                  │
│ Sidebar  │  Last run: 2 hours ago — OK       │
│          │                                   │
│          │  Opportunities Summary            │
│          │  ┌────────┬────────┬────────────┐ │
│          │  │ Total  │Immed.  │ Near Term  │ │
│          │  │  142   │  18    │    44      │ │
│          │  └────────┴────────┴────────────┘ │
│          │                                   │
│          │  Top 5 Opportunities              │
│          │  [condensed opportunity cards]    │
└──────────┴──────────────────────────────────┘
```

**Data displayed:**

- Pipeline last run timestamp and status (success / failed / running)
- Total opportunity count, broken down by classification tier
- Top 5 opportunities by total score (score, topic, market, classification badge)
- Any active pipeline errors or warnings

**Behavior:**

- Data is server-rendered on page load
- Pipeline status card auto-refreshes every 60 seconds (client-side polling)
- Clicking an opportunity card navigates to the detail view
- Clicking "View all" navigates to the opportunities list

---

### 4.2 Opportunities List

**Route:** `/[locale]/opportunities`

**Purpose:** Full paginated, filterable list of all opportunities in the system.

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  Opportunities                                  [+ Filters]  │
│                                                              │
│  Market: [All ▾]  Language: [All ▾]  Class: [All ▾]  Score ≥ [0.5] │
│  Active filters: [Israel ×] [Hebrew ×]                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Topic             Market   Score  Conf.  Class   Date  │  │
│  │ ──────────────────────────────────────────────────── │  │
│  │ Python for Data…  Israel   0.87   High   Immed.  Mar 1│  │
│  │ Cloud Security    Israel   0.81   Med    Immed.  Mar 1│  │
│  │ React Native      IL/US    0.76   High   Near T. Feb28│  │
│  │ ...                                                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Page 1 of 12    [< Prev]  [Next >]                          │
└─────────────────────────────────────────────────────────────┘
```

**Table columns:**

| Column | Description | Sortable |
|---|---|---|
| Topic | Opportunity topic name | Yes |
| Market | Target market identifier | Yes |
| Score | Total opportunity score (0–1, 2 decimal places) | Yes |
| Confidence | Confidence level badge (High / Medium / Low) | Yes |
| Classification | Classification tier badge | Yes |
| Created | Creation timestamp (locale-formatted date) | Yes |

**Default sort:** Score descending.

**Filters:**

| Filter | Type | Values |
|---|---|---|
| Market | Multi-select dropdown | All markets from current data |
| Language | Multi-select dropdown | en, he, ar, ... |
| Classification | Multi-select dropdown | immediate, near_term, watchlist, low_priority, rejected |
| Score threshold | Numeric input (0.0–1.0) | Minimum score cutoff |

Active filters are shown as dismissible chips below the filter bar. "Reset all filters" clears all active filters.

**Pagination:** 25 rows per page. Page navigation at bottom. Total count shown.

**Row interaction:** Clicking a row navigates to the opportunity detail view.

**Locale behavior:** Dates formatted using active locale. Classification labels use translated strings. Score displayed as decimal (not percent) for precision.

**Loading state:** Skeleton table rows (5) while data loads.

**Empty state:** "No opportunities found" with body text and a "Reset filters" action if filters are active, or "Run the pipeline" link if no data exists at all.

---

### 4.3 Opportunity Detail View

**Route:** `/[locale]/opportunities/[id]`

**Purpose:** Full analysis view for a single opportunity. The primary decision-making screen.

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Opportunities                                     │
│                                                              │
│  Python for Data Engineering                    [Immediate]  │
│  Market: Israel · Language: Hebrew · Score: 0.87             │
│                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐   │
│  │  Score Breakdown        │  │  Why Now                 │   │
│  │  demand_score    0.91 ██│  │  Strong hiring growth in │   │
│  │  growth_score    0.84 █ │  │  data roles across IL    │   │
│  │  job_market      0.88 ██│  │  tech sector, combined   │   │
│  │  content_gap     0.79 █ │  │  with sparse Hebrew-     │   │
│  │  confidence      0.85   │  │  language content supply.│   │
│  └─────────────────────────┘  └─────────────────────────┘   │
│                                                              │
│  Evidence (7 items)                                          │
│  ▼ Job posting spike on LinkedIn IL — 340 postings (Mar '25) │
│  ▼ Google Trends: "python data engineer" +62% YoY (IL)      │
│  ▼ Internal content gap: 0 existing courses on this topic   │
│  ...                                                         │
│                                                              │
│  Market Context          Language Context                    │
│  Israeli tech sector,    No Hebrew-language content          │
│  mid-to-senior roles     available from COGNET or            │
│                          major competitors                   │
│                                                              │
│  Recommended Format      Lifecycle State                     │
│  Video course, 4–6 hrs   Immediate → [Approve] [Defer]       │
└─────────────────────────────────────────────────────────────┘
```

**Sections:**

**Header:**
- Topic name (large, prominent)
- Classification badge (color-coded)
- Market, language, total score
- Created / updated timestamps

**Score Breakdown:**
- Table listing each score family with its value and a visual bar
- Weighted total score shown at bottom
- Score version and run ID shown as metadata (collapsed by default)
- See §5 for visualization approach

**Why Now Summary:**
- LLM-generated narrative (clearly labeled as AI-generated)
- 2–4 sentence summary of the primary demand drivers
- Timestamp of when the summary was generated

**Confidence Note:**
- Confidence score value
- Confidence level label (High / Medium / Low)
- Brief explanation of any confidence downgrades (e.g., "Low agreement between sources")

**Evidence List:**
- Expandable list of evidence items
- Each item shows: source name, signal type, value, date, trust tier badge
- See §6 for display approach

**Market Context:**
- Structured text block describing the target market for this opportunity
- Industry segments, seniority levels, geographic scope

**Language Context:**
- Notes on language-specific demand signals
- Competitive content landscape in that language

**Recommended Format:**
- Suggested content format (e.g., video course, workshop, micro-course)
- Estimated duration
- Key topics to cover

**Lifecycle Actions:**
- Current lifecycle state
- Available state transitions: Approve, Defer, Reject
- Confirmation required for Reject
- Actions write back to the API and update state in place

---

### 4.4 Pipeline Status Page

**Route:** `/[locale]/pipeline`

**Purpose:** Operational visibility into pipeline execution.

**Layout:**

```
┌──────────────────────────────────────────────────────────┐
│  Pipeline Status                                          │
│                                                          │
│  Last run: March 25, 2026 at 03:00 UTC — Success         │
│  Duration: 14m 32s · Opportunities generated: 8           │
│                                                          │
│  Steps                                                   │
│  ┌────────────────────────┬──────────┬──────────────┐    │
│  │ Step                   │ Status   │ Duration     │    │
│  │ signal_ingestion       │ ✓ OK     │ 3m 12s       │    │
│  │ enrichment             │ ✓ OK     │ 6m 04s       │    │
│  │ scoring                │ ✓ OK     │ 1m 44s       │    │
│  │ ranking                │ ✓ OK     │ 0m 18s       │    │
│  │ llm_summaries          │ ✓ OK     │ 3m 14s       │    │
│  └────────────────────────┴──────────┴──────────────┘    │
│                                                          │
│  Run History                                             │
│  [table of recent runs]                                  │
└──────────────────────────────────────────────────────────┘
```

**Data displayed:**

- Most recent run: timestamp, duration, status, opportunity count produced
- Per-step status table: step name, status, duration, error count
- Run history table: last 20 runs with timestamps, status, duration
- Any active errors with expandable detail

**Error display:** If a step failed, the status cell shows a warning icon and the row is expandable to show the error message and stack trace summary.

**Empty state:** "Pipeline has not been run yet. No run history available."

**Auto-refresh:** Page polls every 30 seconds when a run is in progress (detected by status = `running`).

---

## 5. Score Breakdown Visualization

Score families are displayed in a two-column table with an inline bar chart per row.

**Approach:** Table-based with inline percentage bars (CSS width, not SVG). This renders correctly in RTL, is accessible, and works in low-bandwidth environments.

```
┌────────────────────┬────────┬────────────────────────┐
│ Score Family       │ Value  │ Bar                    │
├────────────────────┼────────┼────────────────────────┤
│ Demand             │ 0.91   │ ████████████████████░  │
│ Growth             │ 0.84   │ ████████████████░░░░░  │
│ Job Market         │ 0.88   │ █████████████████░░░░  │
│ Content Gap        │ 0.79   │ ███████████████░░░░░░  │
│ Localization Fit   │ 0.72   │ ██████████████░░░░░░░  │
│ Teachability       │ 0.80   │ ████████████████░░░░░  │
│ Strategic Fit      │ 0.65   │ █████████████░░░░░░░░  │
├────────────────────┼────────┼────────────────────────┤
│ Total Score        │ 0.87   │ (weighted)              │
└────────────────────┴────────┴────────────────────────┘
```

Bar fill direction is CSS `width` percentage. In RTL mode, bar fills from right using `rtl:` Tailwind classes.

Score bars are color-coded:
- 0.80–1.00: green
- 0.60–0.79: amber
- 0.00–0.59: red

Weight values for each score family are shown in a collapsed "Weights" section beneath the table, visible on expand.

---

## 6. Evidence Display

Evidence items are displayed in an expandable list. Default state shows the first 3 items; "Show all" expands to full list.

Each evidence item renders:

```
▼ [Trust Tier Badge] Source Name — Signal Type
   Value: 340 job postings  |  Date: March 2025
   "Senior Python Data Engineer" postings on LinkedIn Israel,
   62% increase from same period last year.
```

**Trust tier badges:**

| Tier | Label | Color |
|---|---|---|
| Tier 1 | Verified | Green |
| Tier 2 | Aggregated | Blue |
| Tier 3 | Experimental | Orange |

Tier 3 items include an analyst review flag: "This evidence is from an experimental source. Verify independently before acting."

Evidence items are sorted by trust tier descending (Tier 1 first).

---

## 7. Locale Switcher

**Component:** `LocaleSwitcher.tsx`

**Placement:** Top-right of the TopBar (top-left in RTL mode).

**Appearance:**

```
[EN] | [HE]
```

Active locale is visually indicated (bold, underline, or background highlight). Inactive locale is a clickable link.

**Behavior:**
- Switching locale is a client-side navigation to the equivalent URL in the other locale
- The current page, scroll position, and open panel state are preserved where possible
- Does not trigger a full page reload

**Accessibility:** `aria-label` on the container: "Switch language / החלף שפה". Each button has a `lang` attribute matching the language it switches to.

---

## 8. Loading States

All data views must have loading states. Loading states use skeleton components, not spinners, to prevent layout shift.

| View | Loading behavior |
|---|---|
| Dashboard summary cards | 3 skeleton cards at correct dimensions |
| Opportunities table | 5 skeleton table rows |
| Opportunity detail | Skeleton layout matching section structure |
| Pipeline status | Skeleton step table |
| Score breakdown | Skeleton bar rows |
| Evidence list | 3 skeleton evidence items |

Loading skeletons use a pulsing animation (`animate-pulse` in Tailwind). They match the approximate dimensions of real content to prevent layout reflow on load.

---

## 9. Empty States

| Scenario | Heading | Body | Action |
|---|---|---|---|
| No opportunities match filters | "No opportunities found" | "Try adjusting your filters." | "Reset filters" button |
| No opportunities in system | "No opportunities yet" | "The pipeline has not generated any results." | "View pipeline status" link |
| Pipeline never run | "Pipeline not run yet" | "No run history is available." | — |
| Opportunity detail not found | "Opportunity not found" | "This opportunity may have been deleted." | "Back to list" link |

Empty states include a simple neutral illustration or icon (no heavy graphics). They are never just a blank area.

---

## 10. Error States

**API unreachable:**
- Full-page error state on initial load failure
- Heading: "Unable to reach the server"
- Body: "Please check your connection or try again."
- "Retry" button that re-fetches

**Backend error (5xx):**
- Heading: "Something went wrong"
- Body: "An error occurred on the server. If this continues, contact the engineering team."
- Error ID shown (from API response) for support reference

**Not found (404):**
- Heading: "Page not found"
- Navigation back to dashboard

**Inline errors** (within a component, not full-page):
- Used when one section fails but the rest of the page is functional
- Red-bordered card with error icon and message
- Does not break layout of surrounding content

All error states are wrapped in `ErrorBoundary` components. Unhandled render errors fall back to the nearest boundary and display an inline error card.

---

## 11. RTL Layout Verification

See the Localization Strategy document for the full RTL checklist. UX-specific notes:

- **Tables:** Column order does not reverse in RTL. Reading direction affects alignment, not column sequence.
- **Score bars:** Fill direction reverses. This is intentional and correct.
- **Navigation:** The sidebar moves to the right. The main content area occupies the left.
- **Modals:** The close button moves to the top-left. Confirm/cancel button order reverses.
- **Breadcrumbs:** Separator chevron flips direction.
- **Pagination:** Previous/next button labels and arrow icons flip appropriately.

---

## 12. Accessibility Requirements

- All interactive elements are keyboard-navigable
- Focus ring is always visible (no `outline: none` without replacement)
- Tables have `<caption>` or `aria-label`
- Score bars include `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Images and icons have `alt` text or `aria-hidden` if decorative
- Color is never the only means of conveying information (score bars also show numeric values)
- ARIA labels on the locale switcher and filter controls are bilingual where practical

---

## 13. Design Tokens

| Token | Value |
|---|---|
| Primary color | `#2563EB` (blue-600) |
| Success / Immediate | `#16A34A` (green-600) |
| Warning / Near Term | `#D97706` (amber-600) |
| Caution / Watchlist | `#9333EA` (purple-600) |
| Muted / Low Priority | `#6B7280` (gray-500) |
| Danger / Rejected | `#DC2626` (red-600) |
| Background | `#F9FAFB` (gray-50) |
| Surface | `#FFFFFF` |
| Border | `#E5E7EB` (gray-200) |
| Text primary | `#111827` (gray-900) |
| Text muted | `#6B7280` (gray-500) |
| Font | Inter (Latin) + Rubik (Hebrew) |

Hebrew text must render with Rubik or a comparable Hebrew-optimized font. Inter does not include Hebrew glyphs. Use a CSS font stack: `font-family: 'Rubik', 'Inter', sans-serif;` with Rubik loaded conditionally or universally (it covers Latin well).
