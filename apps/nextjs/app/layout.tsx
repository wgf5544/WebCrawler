import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'WebCrawler App',
  description: 'A web crawler application',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}