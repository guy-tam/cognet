'use client'

import { useTranslations } from 'next-intl'
import { Link, usePathname } from '@/lib/navigation'
import LocaleSwitcher from '@/components/LocaleSwitcher'

interface NavigationProps {
  locale: string
}

// פריט ניווט בודד — עם אייקון ואפקט זוהר
function NavItem({
  href,
  icon,
  label,
  isActive,
  isRTL,
}: {
  href: string
  icon: string
  label: string
  isActive: boolean
  isRTL: boolean
}) {
  return (
    <Link
      href={href}
      className={[
        'group flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium',
        'transition-all duration-200 ease-out relative',
        isActive
          ? 'bg-white/10 text-white'
          : 'text-slate-400 hover:bg-white/5 hover:text-slate-200',
      ].join(' ')}
    >
      {/* פס מסמן פעיל */}
      {isActive && (
        <span
          className={[
            'absolute top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full',
            'bg-gradient-to-b from-indigo-400 to-purple-400',
            isRTL ? 'right-0' : 'left-0',
          ].join(' ')}
        />
      )}

      {/* אייקון */}
      <span className="text-base flex-shrink-0">{icon}</span>

      {/* תווית */}
      <span>{label}</span>

      {/* אפקט זוהר בריחוף */}
      {!isActive && (
        <span className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-r from-indigo-500/5 to-purple-500/5 pointer-events-none" />
      )}
    </Link>
  )
}

// ניווט צידי — רקע כהה פרמיום, RTL aware
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
        'w-60 min-h-screen sidebar-gradient flex flex-col',
        'border-white/5',
        isRTL ? 'border-l' : 'border-r',
      ].join(' ')}
    >
      {/* אזור לוגו עם זוהר */}
      <div className="px-5 py-6 border-b border-white/5">
        <div className="flex flex-col">
          <span className="text-xl font-bold gradient-text tracking-tight">
            COGNET
          </span>
          <span className="text-[11px] text-slate-500 mt-0.5 font-medium tracking-wide uppercase">
            Learning Demand Intelligence
          </span>
        </div>
      </div>

      {/* פריטי ניווט */}
      <nav className="flex-1 p-3 space-y-0.5 mt-2">
        <NavItem
          href="/"
          icon="🏠"
          label={t('dashboard')}
          isActive={isActive('/')}
          isRTL={isRTL}
        />
        <NavItem
          href="/demand"
          icon="📚"
          label={t('demand') || 'Learning Demand'}
          isActive={isActive('/demand')}
          isRTL={isRTL}
        />
        <NavItem
          href="/discover"
          icon="🌍"
          label={t('discover') || 'Market Scanner'}
          isActive={isActive('/discover') || isActive('/search')}
          isRTL={isRTL}
        />
        <NavItem
          href="/opportunities"
          icon="📊"
          label={t('opportunities')}
          isActive={isActive('/opportunities')}
          isRTL={isRTL}
        />
        <NavItem
          href="/pipeline"
          icon="⚙️"
          label={t('pipeline')}
          isActive={isActive('/pipeline')}
          isRTL={isRTL}
        />
      </nav>

      {/* תחתית — מחליף שפה */}
      <div className="p-4 border-t border-white/5">
        <LocaleSwitcher />
      </div>
    </aside>
  )
}
