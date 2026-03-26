'use client'

import { useTranslations } from 'next-intl'
import ScoreBar from '@/components/ScoreBar'
import type { ScoreBreakdown as ScoreBreakdownType } from '@/types/api'

interface ScoreBreakdownProps {
  breakdown: ScoreBreakdownType
}

// מיפוי בין שדות ה-API למפתחות התרגום
const SCORE_FIELDS: Array<{
  key: keyof ScoreBreakdownType
  translationKey: string
}> = [
  { key: 'demand_score', translationKey: 'demand' },
  { key: 'growth_score', translationKey: 'growth' },
  { key: 'job_market_score', translationKey: 'job_market' },
  { key: 'trend_score', translationKey: 'trend' },
  { key: 'content_gap_score', translationKey: 'content_gap' },
  { key: 'localization_fit_score', translationKey: 'localization_fit' },
  { key: 'teachability_score', translationKey: 'teachability' },
  { key: 'strategic_fit_score', translationKey: 'strategic_fit' },
]

// רכיב פירוט ציונים — מציג את 8 מימדי הציון עם סרגלים
export default function ScoreBreakdown({ breakdown }: ScoreBreakdownProps) {
  const t = useTranslations('scores')

  return (
    <div className="space-y-3">
      {SCORE_FIELDS.map(({ key, translationKey }) => (
        <ScoreBar
          key={key}
          score={breakdown[key]}
          label={t(translationKey)}
        />
      ))}
    </div>
  )
}
