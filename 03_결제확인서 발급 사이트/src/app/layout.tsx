import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '결제 확인서 발급 - CMDSPACE',
  description: 'CMDSPACE 강의 결제 확인서 발급 서비스',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50">
        {children}
      </body>
    </html>
  )
}
