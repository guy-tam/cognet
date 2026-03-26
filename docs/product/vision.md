# COGNET Learning Demand Intelligence Engine — Product Vision

**Version:** 1.0
**Status:** Active
**Last Updated:** 2026-03-26
**Owner:** Product / Intelligence Team

---

## 1. System Name and Purpose

**COGNET LDI Engine** (Learning Demand Intelligence Engine) is an internal intelligence platform that determines what people genuinely need to learn, in which markets, for which roles, and in which languages — based on real, quantifiable signals from the labor market, technology trend data, and internal content supply gaps.

The LDI Engine is the analytical brain behind Cognet's content strategy. It transforms raw, noisy signals from the external world into ranked, prioritized, human-reviewable **learning opportunities** — concrete, evidence-backed recommendations for what content Cognet should build, for whom, and with what urgency.

---

## 2. What This System Is NOT

Understanding what the LDI Engine is not is as important as understanding what it is.

| This system IS | This system is NOT |
|---|---|
| An internal intelligence tool | A public-facing consumer application |
| A signal aggregation and ranking engine | A course catalog or LMS |
| A decision-support system for content strategists | A learner-facing recommendation engine |
| A pipeline that generates ranked opportunities | A curriculum builder or authoring tool |
| A human-in-the-loop review workflow | A fully automated content commissioning system |
| An intelligence layer that feeds other systems | A standalone product sold to customers |

The LDI Engine does not publish courses. It does not onboard learners. It does not handle payments, enrollments, or completions. It does not replace human judgment — it informs it.

---

## 3. Core Thesis

> **Real learning demand is latent. It must be excavated from signals — not invented by product managers.**

The core thesis of the LDI Engine is that the market continuously broadcasts signals about what people need to learn: job postings describe required skills, search trends reveal emerging curiosity, skill gaps in hiring pipelines expose training deficits, and internal content libraries reveal what Cognet already covers versus what is missing.

These signals are fragmented, noisy, and multi-lingual. Left unprocessed, they are useless. Processed intelligently, they become a strategic asset.

The LDI Engine's job is to:

1. **Ingest** signals from diverse sources (structured and unstructured)
2. **Normalize** them into a consistent internal representation
3. **Enrich** them with taxonomy mappings (skills, roles, industries, geography, language)
4. **Compute signals** that quantify demand strength, trend velocity, and supply gap
5. **Rank** opportunities by composite score
6. **Generate** human-reviewable opportunity briefs
7. **Serve** those briefs to analysts and decision-makers

The intelligence layer does not make final decisions. It creates the best possible information environment for humans to make them.

---

## 4. Primary Questions the System Answers

The LDI Engine is designed to answer a specific, bounded set of strategic questions:

### 4.1 What Should Be Learned?
Given market signals, what skills, topics, or knowledge domains are seeing rising demand that is not yet well-served by available learning content?

### 4.2 Where Is the Demand Concentrated?
In which geographic markets (countries, regions, cities) is demand for a given skill or topic most acute? Is it global, regional, or hyper-local?

### 4.3 For Whom Is It Most Relevant?
Which job roles, seniority levels, or professional communities are generating this demand signal? Is this a demand for entry-level workers, senior practitioners, or a niche specialist segment?

### 4.4 In What Language Must the Content Be Delivered?
What is the primary language of the target market? Is there evidence of demand for Hebrew-language content specifically? Does the opportunity require RTL UI and localized terminology?

### 4.5 How Urgent Is It?
Is this a slow-burn structural shift or a fast-moving trend with a narrow window? What is the trend velocity and what does the demand trajectory look like over the past 90 days?

### 4.6 What Does Cognet Already Have?
Is there existing internal content (courses, modules, assessments) that partially or fully covers this demand? If so, what is the gap? Can existing assets be extended, or does a net-new build need to be commissioned?

---

## 5. Business Objective

The LDI Engine exists to give Cognet a durable competitive advantage in content strategy decisions.

**Without the LDI Engine:** Content decisions are driven by intuition, anecdote, informal market observation, and the loudest internal voice. This leads to content that is late to market, misaligned with actual learner need, and duplicative of existing supply.

**With the LDI Engine:** Content decisions are driven by ranked, evidence-backed intelligence with explicit confidence scores and source attribution. Teams know what to build, why it matters, for whom, and when the window of opportunity closes.

### Specific Business Outcomes

- **Reduce time-to-first-insight** on emerging skill demand from weeks (manual research) to hours (automated pipeline + human review)
- **Increase content-market fit** by commissioning content that maps to verifiable demand signals rather than assumptions
- **Eliminate duplicative builds** by surfacing what Cognet already has and identifying gaps precisely
- **Enable geographic expansion** decisions with localized demand data (Hebrew-language markets, specific countries)
- **Create an audit trail** for content investment decisions — every approved opportunity has documented evidence

---

## 6. Product Objective

The LDI Engine is an **internal intelligence tool**. Its primary users are:

- **Content Strategists** — who review opportunity briefs and decide what to commission
- **Market Analysts** — who investigate signals, enrich evidence, and provide domain context
- **Product Managers** — who use ranked opportunities to prioritize the content roadmap
- **Engineering / Data leads** — who monitor pipeline health and data quality

The product interface is an **Admin UI** (Next.js) that surfaces:
- A ranked list of learning opportunities with scores, evidence, and market context
- A review workflow for analysts to approve, reject, or request revision of generated opportunities
- Pipeline health and run status dashboards
- Taxonomy management (skills, topics, roles, industries)

The LDI Engine is not a self-service tool for all employees. Access is scoped to analysts and decision-makers who understand the data model and the review responsibilities.

---

## 7. MVP Success Definition

The Minimum Viable Product is considered successful when all of the following are true:

### Data Pipeline
- [ ] At least 2 live ingestion sources are active and running on schedule (e.g., job postings feed + trend/search signals)
- [ ] Raw records are ingested, normalized, and enriched with taxonomy mappings
- [ ] Signal computation runs produce `signal_snapshot` records per topic/skill/market combination
- [ ] Pipeline runs are tracked end-to-end with status, record counts, and failure reporting

### Opportunity Generation
- [ ] The system generates `opportunity_brief` records automatically from signal snapshots that exceed configured thresholds
- [ ] Each brief includes: title, summary, target market, estimated demand score, confidence level, evidence items, and a "why now" rationale
- [ ] Briefs are generated for both English and Hebrew market contexts where signal data supports it

### Review Workflow
- [ ] Analysts can view, approve, reject, and annotate opportunities via the Admin UI
- [ ] Approved opportunities are flagged for downstream consumption
- [ ] Review decisions are logged with reviewer identity, timestamp, and notes

### API
- [ ] A versioned REST API (`/v1/`) is live and serving opportunity data to authorized consumers
- [ ] Endpoints include: opportunity list, top opportunities, opportunities by market, pipeline status

### Quality Bar
- [ ] At least 10 approved opportunity briefs exist with documented evidence
- [ ] At least 1 opportunity has been approved for a Hebrew-language market
- [ ] An analyst can complete a full review cycle (ingest → normalize → enrich → rank → brief → review → approve) without engineering intervention

---

## 8. Non-Goals

The following are explicitly out of scope for v1 and the foreseeable roadmap:

### 8.1 Learner-Facing Features
The LDI Engine has no learner-facing UI, recommendations, or personalization. It is purely an internal tool.

### 8.2 Course Authoring or LMS Integration
The LDI Engine does not generate course outlines, write curricula, or push approved opportunities into an LMS or CMS automatically. Integration with downstream systems is a post-MVP concern.

### 8.3 Real-Time Streaming
The pipeline is batch-oriented. Near-real-time or streaming ingestion is not required for v1. Scheduled batch runs (daily or weekly cadence) are sufficient.

### 8.4 Public API
The API is internal. There is no public API, no API key marketplace, no external developer program.

### 8.5 Multi-Tenant Architecture
The LDI Engine is a single-tenant system serving Cognet's internal team. Multi-tenancy is not a v1 requirement.

### 8.6 A/B Testing or Experiment Frameworks
Signal weighting and ranking algorithms are deterministic and configurable. No A/B testing infrastructure is planned for v1.

### 8.7 Automated Content Commissioning
The system surfaces opportunities; humans approve them. Automated triggering of content production workflows is post-MVP.

---

## 9. Opportunity Lifecycle

Every learning opportunity in the system progresses through a defined lifecycle. State transitions are logged and immutable.

```
draft → surfaced → analyst_review → approved
                                 → rejected
                                 → archived (from any terminal or intermediate state)
```

### State Definitions

| State | Description | Who Sets It |
|---|---|---|
| `draft` | Auto-generated by the ranking/opportunity engine. Not yet visible to analysts. | System |
| `surfaced` | Promoted by the system once it passes minimum quality/confidence thresholds. Visible in the analyst queue. | System |
| `analyst_review` | An analyst has opened and is actively reviewing the opportunity. | Analyst action |
| `approved` | Analyst has approved the opportunity as actionable. Downstream systems can consume it. | Analyst |
| `rejected` | Analyst has rejected the opportunity (low quality, irrelevant, duplicate, etc.). Rejection reason required. | Analyst |
| `archived` | Opportunity is no longer active. May be manually archived or auto-archived after a staleness TTL. | System or Admin |

### Transition Rules
- Only the system can move opportunities from `draft` → `surfaced`
- Only authenticated analysts can move opportunities from `surfaced` → `analyst_review` → `approved` or `rejected`
- Any state can transition to `archived`
- `approved` and `rejected` are terminal states (no further transitions except to `archived`)
- State transitions are append-only audit log entries — no in-place mutation of state history

---

## 10. Bilingual Requirement (English + Hebrew, RTL)

The LDI Engine operates in a bilingual context. This affects both data and UI.

### Data Layer
- Opportunity briefs must support both English and Hebrew field variants for: title, summary, skill labels, topic labels, and why_now text
- Geography and role data must be enrichable with Hebrew translations
- Language context is a first-class attribute of every signal snapshot and opportunity brief

### UI Layer
- The Admin UI must support RTL layout when Hebrew is selected
- All UI strings must be externalized for i18n (no hardcoded English-only strings)
- Language toggle must persist per-user preference
- RTL support must not be an afterthought — it must be designed from the first component

### Signal Context
- Signals sourced from Hebrew-language job boards, Israeli tech publications, or Hebrew search trends must be ingested with `language: he` and `locale: il` metadata preserved end-to-end
- The ranking model must be able to generate Israel-specific or Hebrew-language-specific opportunity scores independently of global/English scores

---

## 11. Human Review Principle

**The LDI Engine augments human judgment; it does not replace it.**

All opportunity briefs generated by the system require human review before they are considered actionable. This is not a technical limitation — it is a deliberate design principle.

### Why Human Review Is Non-Negotiable

1. **Signal quality is imperfect.** Job posting data is noisy. Trend signals can reflect hype rather than durable demand. Humans must apply domain judgment.
2. **Context is irreplaceable.** An analyst may know that a particular skill spike reflects a single large company's hiring surge rather than market-wide demand. The system cannot know this.
3. **Strategic alignment matters.** Not every valid demand signal aligns with Cognet's strategic priorities. Humans must filter for organizational fit.
4. **Trust must be built.** For the LDI Engine to be trusted as a strategic tool, its outputs must be validated by humans who are accountable for the decisions.

### What the System Guarantees
- Every approved opportunity is traceable to its evidence items
- Every evidence item is traceable to its source run and raw record
- Every review decision is logged with reviewer, timestamp, and decision rationale
- No opportunity can be approved without a completed evidence chain

---

## 12. Guiding Principles Summary

| Principle | Statement |
|---|---|
| Signal-driven | Decisions are grounded in evidence, not intuition |
| Human-in-the-loop | Automation surfaces; humans decide |
| Traceable | Every output is traceable to its source |
| Bilingual-first | English and Hebrew are equal citizens |
| Modular | The system is built in composable, replaceable layers |
| Internal-grade | Optimized for analyst trust, not consumer delight |
| Honest about confidence | Every output carries an explicit confidence score |
