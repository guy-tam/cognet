'use client'

import { useTranslations, useLocale } from 'next-intl'
import { Link, usePathname } from '@/lib/navigation'

// רכיב החלפת שפה — שני כפתורי גלולה זה לצד זה
export default function LocaleSwitcher() {
  const t = useTranslations('locale')
  const locale = useLocale()
  const pathname = usePathname()

  return (
    <div className="flex items-center gap-1 p-1 rounded-lg bg-white/5">
      {/* כפתור אנגלית */}
      <Link
        href={pathname}
        locale="en"
        className={[
          'flex-1 text-center text-xs font-medium py-1.5 px-3 rounded-md',
          'transition-all duration-200',
          locale === 'en'
            ? 'bg-indigo-500/20 text-indigo-300 shadow-sm'
            : 'text-slate-500 hover:text-slate-300 hover:bg-white/5',
        ].join(' ')}
      >
        🇺🇸 EN
      </Link>

      {/* כפתור עברית */}
      <Link
        href={pathname}
        locale="he"
        className={[
          'flex-1 text-center text-xs font-medium py-1.5 px-3 rounded-md',
          'transition-all duration-200',
          locale === 'he'
            ? 'bg-indigo-500/20 text-indigo-300 shadow-sm'
            : 'text-slate-500 hover:text-slate-300 hover:bg-white/5',
        ].join(' ')}
      >
        🇮🇱 עב
      </Link>
    </div>
  )
}
