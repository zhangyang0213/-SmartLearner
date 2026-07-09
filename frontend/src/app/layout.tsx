import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SmartLearner - 个性化学习与知识管理',
  description: '基于AI的个性化学习与知识管理平台，助力高效学习',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen font-sans">
        {children}
      </body>
    </html>
  )
}
