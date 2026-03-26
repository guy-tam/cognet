# Localization Service

## Purpose
Shared localization utilities for backend. Admin UI localization is handled by next-intl in /apps/admin/.

## Current State
- Language code utilities in `shared/i18n/language_codes.py`
- RTL detection, supported language checks, canonical language mapping
- Admin locale files: `/apps/admin/locales/{en,he}/common.json`

## Responsibilities
- Canonical language code resolution
- RTL language detection
- Supported language validation
- Future: opportunity content localization
