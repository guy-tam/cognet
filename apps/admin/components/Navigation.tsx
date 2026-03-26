'use client'

import { useTranslations } from 'next-intl'
import { Link, usePathname } from '@/lib/navigation'
import LocaleSwitcher from '@/components/LocaleSwitcher'

interface NavigationProps {
  locale: string
}

// פריט ניווט בודד
function NavItem({
  href,
  label,
  isActive,
}: {
  href: string
  label: string
  isActive: boolean
}) {
  return (
    <Link
      href={href}
      className={[
        'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors',
        isActive
          ? 'bg-blue-50 text-blue-700'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
      ].join(' ')}
    >
      {label}
    </Link>
  )
}

// ניווט צידי — RTL aware, עם לינקים לכל הסקציות
export default function Navigation({ locale }: NavigationProps) {
  const t = useTranslations('nav')
  const pathname = usePathname()

  const isRTL = locale === 'he'

  // בדיקה האם נתיב נוכחי תואם לקישור
  function isActive(path: string) {
    if (path === '/') return pathname === '/'
    return pathname.startsWith(path)
  }

  return (
    <aside
      className={[
        'w-56 min-h-screen bg-white border-gray-200 flex flex-col',
        isRTL ? 'border-l' : 'border-r',
      ].join(' ')}
    >
      {/* לוגו / כותרת */}
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="flex flex-col">
          <span className="text-base font-bold text-gray-900 tracking-tight">COGNET</span>
          <span className="text-xs text-gray-400 mt-0.5">LDI Engine</span>
        </div>
      </div>

      {/* פריטי ניווט */}
      <nav className="flex-1 p-3 space-y-1">
        <NavItem
          href="/"
          label={t('dashboard')}
          isActive={isActive('/')}
        />
        <NavItem
          href="/opportunities"
          label={t('opportunities')}
          isActive={isActive('/opportunities')}
        />
        <NavItem
          href="/discover"
          label={t('discover') || '🌍 Market Scanner'}
          isActive={isActive('/discover') || isActive('/search')}
        />
        <NavItem
          href="/demand"
          label={t('demand') || '📚 Learning Demand'}
          isActive={isActive('/demand')}
        />
        <NavItem
          href="/pipeline"
          label={t('pipeline')}
          isActive={isActive('/pipeline')}
        />
      </nav>

      {/* תחתית — מחליף שפה */}
      <div className="p-4 border-t border-gray-100">
        <LocaleSwitcher />
      </div>
    </aside>
  )
}
