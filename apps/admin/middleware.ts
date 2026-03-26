import createMiddleware from 'next-intl/middleware'

// middleware לניתוב locale אוטומטי
export default createMiddleware({
  locales: ['en', 'he'],
  defaultLocale: 'en',
})

export const config = {
  // התאמה לכל הנתיבים חוץ מ-API, קבצי next ו-static assets
  matcher: ['/((?!api|_next|.*\\..*).*)'],
}
