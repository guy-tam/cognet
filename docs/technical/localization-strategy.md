# Localization Strategy — COGNET LDI Engine

## Overview

The COGNET admin interface is a bilingual product: English (EN) and Hebrew (HE). Hebrew is not cosmetic — it is a first-class language for the internal analysts who will use this tool daily. This document defines the canonical architecture, conventions, and constraints for all localization work in the admin shell.

---

## 1. Bilingual Requirement

| Dimension | English | Hebrew |
|---|---|---|
| UI labels, navigation, headings | Required | Required |
| Opportunity content (topic names, summaries) | Canonical | Future (see §9) |
| Error messages | Required | Required |
| Empty states | Required | Required |
| Pipeline status messages | Required | Required |
| Code, identifiers, API fields | Always English | Never |
| Database column names | Always English | Never |
| Translation key names | Always English | Never |

Hebrew is the operational language of primary users. English is included for consistency, external readability, and future expansion. All UI strings must be available in both languages at all times.

---

## 2. RTL Support Requirement

Hebrew is a right-to-left language. RTL is not optional and is not an afterthought. The layout engine must correctly mirror when the active locale is `he`.

RTL requirements:

- `<html dir="rtl">` and `<body dir="rtl">` when locale is `he`
- Tailwind CSS RTL classes (`rtl:` variant prefix) must be used wherever directional layout is applied
- No hardcoded `left` / `right` directional CSS values in components — use logical properties or Tailwind RTL variants
- All flexbox row layouts must be direction-aware
- Navigation, sidebars, and table column order must respect reading direction
- Icons with inherent direction (arrows, chevrons) must flip in RTL
- Score bar charts and evidence lists must anchor correctly in RTL

---

## 3. Language Separation Principles

The following separation is strict and non-negotiable:

**Canonical data is always in English.**
- Opportunity topic names stored in the database are in English
- Signal source names are in English
- Classification labels (`immediate`, `near_term`, `watchlist`) are English identifiers
- Score field names are English

**Code is always in English.**
- Variable names, function names, component names, file names
- Translation key identifiers
- API response field names

**UI strings are always localized.**
- No hardcoded human-readable string may appear in any component
- Every visible string goes through the translation system
- This applies equally to loading messages, error states, tooltips, and ARIA labels

---

## 4. Localization Architecture

### 4.1 Locale File Locations

```
apps/admin/locales/
  en/
    common.json
  he/
    common.json
```

Both files must be kept in sync. Missing keys in `he/common.json` fall back to `en/common.json` (see §8). New keys must be added to both files simultaneously. A key present in English but absent in Hebrew is a build warning, not a silent omission.

### 4.2 Recommended i18n Library

Use **next-intl** for App Router compatibility with React Server Components and full TypeScript key safety. Alternatively, **i18next with react-i18next** is acceptable if the team has existing familiarity.

The choice must be made once and applied consistently. No mixing of i18n libraries.

**next-intl configuration sketch:**

```ts
// apps/admin/i18n.ts
import { getRequestConfig } from 'next-intl/server';

export default getRequestConfig(async ({ locale }) => ({
  messages: (await import(`./locales/${locale}/common.json`)).default,
}));
```

```ts
// apps/admin/middleware.ts
import createMiddleware from 'next-intl/middleware';

export default createMiddleware({
  locales: ['en', 'he'],
  defaultLocale: 'en',
});
```

### 4.3 TypeScript Key Safety

Translation keys must be typed. Using next-intl's `useTranslations` hook with typed message paths prevents key typos and detects missing keys at compile time.

```ts
// Generated or manually maintained type
type Messages = typeof import('./locales/en/common.json');
declare global {
  interface IntlMessages extends Messages {}
}
```

---

## 5. Translation Key Organization

All keys live in `common.json`. Keys are namespaced by functional area using nested objects.

### 5.1 Key Namespaces

| Namespace | Purpose |
|---|---|
| `common` | Shared labels: save, cancel, loading, error, yes, no |
| `navigation` | Sidebar links, top nav items, breadcrumbs |
| `opportunities` | Opportunity list, detail view, field labels |
| `pipeline` | Pipeline status page, run history, step labels |
| `status` | Lifecycle state labels: immediate, near_term, watchlist, etc. |
| `filters` | Filter panel labels, placeholders, reset |
| `errors` | Error messages: API failure, not found, timeout |
| `empty` | Empty state headings and body text |
| `scoring` | Score family labels, confidence labels, weight labels |
| `locale` | Locale switcher labels |

### 5.2 Example Key Structure

```json
{
  "common": {
    "loading": "Loading...",
    "error": "Something went wrong",
    "save": "Save",
    "cancel": "Cancel",
    "back": "Back"
  },
  "navigation": {
    "dashboard": "Dashboard",
    "opportunities": "Opportunities",
    "pipeline": "Pipeline Status",
    "settings": "Settings"
  },
  "opportunities": {
    "title": "Learning Opportunities",
    "table": {
      "topic": "Topic",
      "market": "Market",
      "score": "Score",
      "confidence": "Confidence",
      "classification": "Classification",
      "created": "Created"
    },
    "detail": {
      "scoreBreakdown": "Score Breakdown",
      "evidence": "Evidence",
      "whyNow": "Why Now",
      "marketContext": "Market Context",
      "recommendedFormat": "Recommended Format"
    }
  },
  "status": {
    "immediate": "Immediate",
    "near_term": "Near Term",
    "watchlist": "Watchlist",
    "low_priority": "Low Priority",
    "rejected": "Rejected"
  },
  "errors": {
    "api_unreachable": "Unable to reach the server. Please try again.",
    "not_found": "Not found.",
    "unknown": "An unexpected error occurred."
  },
  "empty": {
    "opportunities_title": "No opportunities found",
    "opportunities_body": "Try adjusting your filters or run the pipeline.",
    "pipeline_title": "No pipeline runs yet",
    "pipeline_body": "The pipeline has not been executed."
  }
}
```

Hebrew `common.json` mirrors this structure exactly with Hebrew string values.

---

## 6. Locale Switching Mechanism

### 6.1 Switching Methods

Locale may be determined by one of two mechanisms (choose one per deployment):

**Option A — URL prefix (recommended for next-intl):**
- `cognet.internal/en/opportunities`
- `cognet.internal/he/opportunities`
- Locale is part of the route. Switching navigates to the equivalent path in the other locale.
- Clean, shareable, bookmark-safe.

**Option B — localStorage persistence:**
- Locale stored in `localStorage` under key `cognet_locale`
- On initial load, read from localStorage; default to `en` if absent
- Switching updates localStorage and triggers instant re-render via context

**For MVP, Option A (URL prefix with next-intl middleware) is preferred.** It aligns with App Router conventions and avoids hydration mismatches.

### 6.2 Instant Switch Without Page Reload

When using URL-prefix routing, locale switch is a client-side navigation using `router.push()` — no full page reload. When using localStorage, the locale context provider re-renders children on change. Either way, the user must not see a full browser refresh.

### 6.3 Persistence

If URL-based: the locale is encoded in the URL and persists naturally.
If localStorage-based: persists across sessions until cleared.

A locale preference set by the user is remembered. The system does not reset to default on return visits.

---

## 7. RTL Layout Behavior

### 7.1 HTML Direction Attribute

When locale is `he`, set `dir="rtl"` at the `<html>` element level. This is the only way to correctly trigger browser-native RTL behaviors (form inputs, text alignment, scrollbars).

```tsx
// apps/admin/app/[locale]/layout.tsx
export default function RootLayout({ children, params }) {
  const { locale } = params;
  return (
    <html lang={locale} dir={locale === 'he' ? 'rtl' : 'ltr'}>
      <body>{children}</body>
    </html>
  );
}
```

### 7.2 Tailwind RTL Classes

Use `rtl:` variant prefix from Tailwind CSS (built-in since v3.3 with `dir` attribute support):

```html
<!-- Sidebar: left in LTR, right in RTL -->
<aside class="fixed left-0 rtl:left-auto rtl:right-0">

<!-- Navigation icon margin -->
<span class="mr-2 rtl:mr-0 rtl:ml-2">

<!-- Table cell alignment -->
<td class="text-left rtl:text-right">
```

### 7.3 Layout-Aware Components

Every component that has directional behavior must be RTL-aware:

| Component | LTR behavior | RTL behavior |
|---|---|---|
| Sidebar navigation | Left-anchored | Right-anchored |
| Breadcrumbs | Left-to-right | Right-to-left |
| Table columns | Left-aligned text | Right-aligned text |
| Score bar fill | Fills left-to-right | Fills right-to-left |
| Evidence list bullets | Left-side bullet | Right-side bullet |
| Modal close button | Top-right | Top-left |
| Filter panel | Opens from right | Opens from left |
| Pagination arrows | Left/right chevrons | Flipped |
| Chevron icons | Points right | Points left |

### 7.4 RTL Testing Checklist

Before any release, verify the following in `he` locale:

- [ ] HTML `dir="rtl"` is present
- [ ] Sidebar renders on right side
- [ ] All navigation labels render right-to-left
- [ ] Opportunity table columns align correctly
- [ ] Score breakdown bars fill from right
- [ ] Evidence list items indent correctly
- [ ] Filter panel opens and closes from correct side
- [ ] Modal close button is top-left
- [ ] Pagination controls are mirrored
- [ ] No text truncation due to misaligned containers
- [ ] No horizontal scroll caused by directional overflow
- [ ] Form inputs (filters, search) align correctly
- [ ] Error and empty states are correctly aligned
- [ ] Loading skeletons respect direction

---

## 8. Missing Key Fallback Behavior

If a translation key exists in `en/common.json` but is absent from `he/common.json`, the system falls back to the English value. It does not display a raw key or an empty string.

Fallback chain: `he` → `en` → key path string (never shown in production).

Fallback usage must be logged as a warning in development mode so missing keys are caught before release.

```ts
// next-intl fallback config
{
  defaultLocale: 'en',
  // next-intl handles key fallback natively when onError is configured
}
```

Missing keys in production are a bug, not an acceptable state. Hebrew translations must be complete before shipping any new UI surface.

---

## 9. Opportunity Content Localization

### 9.1 Current State (MVP)

Opportunity content — topic name, summary, why-now text, recommended format notes — is stored and displayed in English only. The canonical language for all intelligence data is English.

### 9.2 Future Localization Path

Opportunity content localization is architecturally supported but not activated in MVP. The data model must accommodate it from the start:

```ts
// Data model supports localized content fields
interface OpportunityContent {
  topic_name: string;               // English canonical
  topic_name_he?: string;           // Hebrew optional
  summary: string;                  // English canonical
  summary_he?: string;              // Hebrew optional
  why_now_summary: string;          // English canonical
  why_now_summary_he?: string;      // Hebrew optional
}
```

When a Hebrew locale is active and `topic_name_he` is present, display it. Otherwise fall back to `topic_name`.

The admin UI should expose a content translation interface in a future iteration (manual or LLM-assisted). Do not block MVP on this.

---

## 10. Hebrew Date and Number Formatting

Use `Intl.DateTimeFormat` and `Intl.NumberFormat` with the active locale code. Do not hardcode date or number format patterns.

```ts
// Date formatting
const formatDate = (date: Date, locale: string) =>
  new Intl.DateTimeFormat(locale === 'he' ? 'he-IL' : 'en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);

// Score percentage
const formatScore = (score: number, locale: string) =>
  new Intl.NumberFormat(locale === 'he' ? 'he-IL' : 'en-US', {
    style: 'percent',
    maximumFractionDigits: 0,
  }).format(score);
```

Hebrew uses Western Arabic numerals (0-9) in modern Israeli contexts. Do not use Arabic-Indic numeral form unless explicitly required.

---

## 11. No Hardcoded Strings Policy

The following are violations and must never appear in merged code:

```tsx
// VIOLATION — hardcoded English string
<h1>Learning Opportunities</h1>

// VIOLATION — hardcoded Hebrew string
<span>אין הזדמנויות</span>

// CORRECT
const t = useTranslations('opportunities');
<h1>{t('title')}</h1>
```

This policy applies to:
- All page headings
- All button labels
- All table column headers
- All filter labels and placeholders
- All error messages
- All empty state text
- All loading indicators with text
- All ARIA labels and title attributes

Automated linting rules (eslint-plugin-i18n or similar) should be configured to flag raw string literals in JSX.

---

## 12. Summary of Decisions

| Decision | Choice |
|---|---|
| i18n library | next-intl (preferred) or i18next |
| Locale switching | URL-prefix routing |
| RTL mechanism | `dir` attribute on `<html>` + Tailwind `rtl:` variants |
| Canonical data language | English |
| Fallback language | English |
| Opportunity content | English only in MVP, model supports future Hebrew |
| Hardcoded strings | Prohibited |
| Key organization | Single `common.json` with namespaced keys |
| TypeScript safety | Typed message paths via next-intl |
| Number/date formatting | `Intl` API with locale code |
