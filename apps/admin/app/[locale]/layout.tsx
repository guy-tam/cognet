import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import type { ReactNode } from 'react'
import { Inter, Rubik } from 'next/font/google'
import Navigation from '@/components/Navigation'
import '@/styles/globals.css'

// טעינת גופנים — Inter לאנגלית, Rubik לעברית
const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const rubik = Rubik({
  subsets: ['latin', 'hebrew'],
  variable: '--font-rubik',
  display: 'swap',
})

interface LocaleLayoutProps {
  children: ReactNode
  params: { locale: string }
}

export default async function LocaleLayout({
  children,
  params,
}: LocaleLayoutProps) {
  const { locale } = params
  const messages = await getMessages()
  const dir = locale === 'he' ? 'rtl' : 'ltr'
  const isRTL = locale === 'he'

  return (
    <html lang={locale} dir={dir} className={`${inter.variable} ${rubik.variable}`}>
      <body
        className={[
          'min-h-screen text-slate-900',
          isRTL ? 'font-rubik' : 'font-sans',
        ].join(' ')}
        style={{ fontFamily: isRTL ? 'var(--font-rubik)' : 'var(--font-inter)' }}
      >
        <NextIntlClientProvider messages={messages}>
          <div className="flex min-h-screen">
            {/* סיידבר כהה */}
            <Navigation locale={locale} />

            {/* אזור תוכן ראשי */}
            <div className="flex-1 flex flex-col bg-slate-50/50 min-h-screen">
              {/* סרגל עליון עדין */}
              <header className="h-14 bg-white/80 backdrop-blur-sm border-b border-slate-200/60 flex items-center px-6 sticky top-0 z-10">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <span className="text-slate-500 font-medium">COGNET</span>
                  <span>/</span>
                  <span className="text-slate-700">Admin</span>
                </div>
              </header>

              {/* תוכן */}
              <main className="flex-1 p-6 overflow-auto animate-fade-in">
                {children}
              </main>
            </div>
          </div>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
