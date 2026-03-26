import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import type { ReactNode } from 'react'
import Navigation from '@/components/Navigation'
import '@/styles/globals.css'

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

  return (
    <html lang={locale} dir={dir}>
      <body className="font-sans bg-gray-50 text-gray-900 min-h-screen">
        <NextIntlClientProvider messages={messages}>
          <div className="flex min-h-screen">
            <Navigation locale={locale} />
            <main className="flex-1 p-6 overflow-auto">
              {children}
            </main>
          </div>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
