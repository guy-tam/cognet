import { createNavigation } from 'next-intl/navigation'

// הגדרת ניווט משותפת — משמש את כל הרכיבים שצריכים Link או usePathname
export const { Link, usePathname, useRouter, redirect } = createNavigation({
  locales: ['en', 'he'],
  defaultLocale: 'en',
})
