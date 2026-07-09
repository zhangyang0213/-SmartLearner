'use client'

import Link from 'next/link'
import { BookOpen, FileText, Database, Route, ArrowRight, Sparkles } from 'lucide-react'

const modules = [
  {
    name: '课程问答助手',
    description: '基于课程知识库的智能问答，支持多文档检索与精准回答，让学习更高效',
    icon: BookOpen,
    color: 'blue',
    href: '/course',
    gradient: 'from-blue-500 to-blue-600',
    bgLight: 'bg-blue-50',
    textColor: 'text-blue-600',
    borderColor: 'border-blue-200',
  },
  {
    name: '论文精读教练',
    description: '苏格拉底式深度精读，AI引导提问与评估，助你真正读懂每一篇论文',
    icon: FileText,
    color: 'purple',
    href: '/paper',
    gradient: 'from-purple-500 to-purple-600',
    bgLight: 'bg-purple-50',
    textColor: 'text-purple-600',
    borderColor: 'border-purple-200',
  },
  {
    name: '知识库管家',
    description: '智能知识库管理，语义搜索与自然语言查询，知识触手可及',
    icon: Database,
    color: 'emerald',
    href: '/knowledge',
    gradient: 'from-emerald-500 to-emerald-600',
    bgLight: 'bg-emerald-50',
    textColor: 'text-emerald-600',
    borderColor: 'border-emerald-200',
  },
  {
    name: '学习路径规划',
    description: '个性化学习路径生成与追踪，科学规划你的成长之路',
    icon: Route,
    color: 'orange',
    href: '/learning',
    gradient: 'from-orange-500 to-orange-600',
    bgLight: 'bg-orange-50',
    textColor: 'text-orange-600',
    borderColor: 'border-orange-200',
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen gradient-bg">
      {/* Header */}
      <header className="border-b border-white/60 glass">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-white font-bold text-sm">
              SL
            </div>
            <span className="text-xl font-bold text-gray-900">SmartLearner</span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="mx-auto max-w-7xl px-4 pt-16 pb-12 sm:px-6 sm:pt-24 sm:pb-16 lg:px-8">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-medium text-primary-700 ring-1 ring-primary-200 mb-6">
            <Sparkles className="h-4 w-4" />
            基于RAG的智能学习平台
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl lg:text-6xl">
            SmartLearner
          </h1>
          <p className="mt-4 text-lg text-gray-600 sm:text-xl max-w-2xl mx-auto">
            你的AI学习伙伴
          </p>
          <p className="mt-3 text-base text-gray-500 max-w-xl mx-auto">
            融合检索增强生成与个性化学习策略，为你的学习之旅赋能
          </p>
        </div>
      </section>

      {/* Module Cards */}
      <section className="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {modules.map((module) => {
            const Icon = module.icon
            return (
              <Link
                key={module.name}
                href={module.href}
                className={`group relative overflow-hidden rounded-2xl border ${module.borderColor} bg-white p-6 sm:p-8 card-hover`}
              >
                <div className="flex items-start gap-4">
                  <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${module.bgLight}`}>
                    <Icon className={`h-6 w-6 ${module.textColor}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                      {module.name}
                    </h3>
                    <p className="mt-2 text-sm text-gray-500 leading-relaxed">
                      {module.description}
                    </p>
                    <div className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary-600 group-hover:gap-2 transition-all">
                      开始使用
                      <ArrowRight className="h-4 w-4" />
                    </div>
                  </div>
                </div>
                {/* Decorative gradient */}
                <div className={`absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gradient-to-br ${module.gradient} opacity-5 group-hover:opacity-10 transition-opacity`} />
              </Link>
            )
          })}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200/60 bg-white/60">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-400">
            SmartLearner - 个性化学习与知识管理平台
          </p>
        </div>
      </footer>
    </div>
  )
}
