'use client'

import { useTranslations, useLocale } from 'next-intl'
import { Link, usePathname } from '@/lib/navigation'


// רכיב החלפת שפה — מציג את השפה הנוכחית ומאפשר מעבר
export default function LocaleSwitcher() {
  const t = useTranslations('locale')
  const locale = useLocale()
  const pathname = usePathname()

  // השפה שאליה רוצים לעבור
  const targetLocale = locale === 'he' ? 'en' : 'he'
  const label = locale === 'he' ? t('switch_to_en') : t('switch_to_he')

  return (
    <Link
      href={pathname}
      locale={targetLocale}
      className="text-xs font-medium text-gray-500 hover:text-gray-900 transition-colors px-2 py-1 rounded border border-gray-200 hover:border-gray-400"
    >
      {label}
    </Link>
  )
}
