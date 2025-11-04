import './globals.css'
import { AntdRegistry } from '@ant-design/nextjs-registry'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'CPG2PVG-AI | 临床指南转化系统',
  description: '将临床医学指南(CPG)转化为公众医学指南(PVG)的智能系统',
  keywords: ['医学指南', 'CPG', 'PVG', '人工智能', '医疗AI'],
  authors: [{ name: 'CPG2PVG-AI Team' }],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <AntdRegistry>{children}</AntdRegistry>
      </body>
    </html>
  )
}