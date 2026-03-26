// layout שורש — נדרש על ידי Next.js App Router
// ה-locale layout בתוך [locale]/ מטפל בכל הלוגיקה האמיתית
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
