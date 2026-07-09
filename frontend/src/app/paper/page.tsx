'use client'

import { useState, useCallback } from 'react'
import Sidebar from '@/components/Sidebar'
import { FileText, Upload, Loader2, X, Lightbulb, BookOpen, Network, Star, CheckCircle, ArrowRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'
import { uploadFiles, listKBs, summarize, generateSocratic, evaluateSocratic, recommendLiterature } from '@/lib/api'

type Tab = 'summary' | 'socratic' | 'recommend'

interface KBItem {
  kb_id: string
  name: string
  description: string
  doc_count: number
  chunk_count: number
}

interface SummaryData {
  title_guess: string
  abstract_summary: string
  key_contributions: string[]
  methodology_summary: string
  findings_summary: string
  limitations: string[]
  future_work: string
}

interface SocraticQuestion {
  id?: string
  question: string
  purpose: string
  hint: string
  depth_level: number
}

interface SocraticEval {
  understanding_level: string
  feedback: string
  follow_up_question: string
  key_points_missed: string[]
}

interface LiteratureRec {
  title: string
  authors_guess: string
  relevance_reason: string
  search_query: string
  topics_shared: string[]
}

export default function PaperPage() {
  const [paperKbId, setPaperKbId] = useState<string>('')
  const [paperTitle, setPaperTitle] = useState<string>('')
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('summary')
  const [error, setError] = useState<string>('')

  // Knowledge base for paper
  const [kbs, setKbs] = useState<KBItem[]>([])
  const [selectedKb, setSelectedKb] = useState<string>('')

  // Summary state
  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  // Socratic state
  const [socraticQuestions, setSocraticQuestions] = useState<SocraticQuestion[]>([])
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0)
  const [socraticResponse, setSocraticResponse] = useState('')
  const [socraticLoading, setSocraticLoading] = useState(false)
  const [evalLoading, setEvalLoading] = useState(false)
  const [evaluations, setEvaluations] = useState<Record<number, SocraticEval>>({})

  // Literature state
  const [recommendations, setRecommendations] = useState<LiteratureRec[]>([])
  const [litLoading, setLitLoading] = useState(false)

  // Drag state
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  // Load knowledge bases on mount
  React.useEffect(() => {
    loadKBs()
  }, [])

  async function loadKBs() {
    try {
      const data = await listKBs()
      setKbs(data.knowledge_bases || [])
    } catch {
      setKbs([])
    }
  }

  async function handleUploadFile(file: File) {
    if (!selectedKb) {
      setError('请先选择或创建一个知识库')
      return
    }
    setUploading(true)
    setError('')
    try {
      await uploadFiles(selectedKb, [file])
      setPaperKbId(selectedKb)
      setPaperTitle(file.name.replace(/\.(docx|doc|pdf)$/i, '').replace(/_/g, ' '))
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传论文失败')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && (file.name.endsWith('.docx') || file.name.endsWith('.doc') || file.name.endsWith('.pdf') || file.name.endsWith('.txt'))) {
      handleUploadFile(file)
    } else {
      setError('请上传 Word (.doc/.docx) 或 PDF 格式的论文文件')
    }
  }, [selectedKb])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleUploadFile(file)
  }, [selectedKb])

  async function handleLoadSummary() {
    if (!paperKbId) return
    setSummaryLoading(true)
    setError('')
    try {
      const data = await summarize(paperKbId)
      setSummary({
        title_guess: data.title_guess || '',
        abstract_summary: data.abstract_summary || '',
        key_contributions: data.key_contributions || [],
        methodology_summary: data.methodology_summary || '',
        findings_summary: data.findings_summary || '',
        limitations: data.limitations || [],
        future_work: data.future_work || '',
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取摘要失败')
    } finally {
      setSummaryLoading(false)
    }
  }

  async function handleLoadSocratic() {
    if (!paperKbId) return
    setSocraticLoading(true)
    setError('')
    try {
      const data = await generateSocratic(paperKbId)
      setSocraticQuestions(data.questions || [])
      setCurrentQuestionIdx(0)
      setEvaluations({})
      setSocraticResponse('')
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成问题失败')
    } finally {
      setSocraticLoading(false)
    }
  }

  async function handleEvaluateResponse() {
    if (!paperKbId || !socraticQuestions[currentQuestionIdx] || !socraticResponse.trim()) return
    setEvalLoading(true)
    setError('')
    try {
      const q = socraticQuestions[currentQuestionIdx]
      const data = await evaluateSocratic(paperKbId, q.question, socraticResponse)
      setEvaluations((prev) => ({
        ...prev,
        [currentQuestionIdx]: {
          understanding_level: data.understanding_level || '',
          feedback: data.feedback || '',
          follow_up_question: data.follow_up_question || '',
          key_points_missed: data.key_points_missed || [],
        },
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : '评估失败')
    } finally {
      setEvalLoading(false)
    }
  }

  async function handleLoadRecommendations() {
    if (!paperKbId) return
    setLitLoading(true)
    setError('')
    try {
      const data = await recommendLiterature(paperKbId, 5)
      setRecommendations(data.recommendations || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取推荐失败')
    } finally {
      setLitLoading(false)
    }
  }

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab)
    if (tab === 'summary' && !summary && paperKbId) handleLoadSummary()
    if (tab === 'socratic' && socraticQuestions.length === 0 && paperKbId) handleLoadSocratic()
    if (tab === 'recommend' && recommendations.length === 0 && paperKbId) handleLoadRecommendations()
  }

  const currentQ = socraticQuestions[currentQuestionIdx]
  const currentEval = currentQ ? evaluations[currentQuestionIdx] : null

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="flex h-16 items-center gap-4 px-4 sm:px-6 lg:px-8 pl-16 lg:pl-8">
            <FileText className="h-5 w-5 text-purple-600" />
            <h1 className="text-lg font-semibold text-gray-900">论文精读教练</h1>
            {paperTitle && (
              <span className="hidden sm:inline text-sm text-gray-500 truncate ml-2">— {paperTitle}</span>
            )}
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Upload Section */}
          {!paperKbId && (
            <div className="mb-6 space-y-3">
              {/* Knowledge base selector */}
              <div className="max-w-md">
                <label className="block text-xs font-medium text-gray-600 mb-1">选择目标知识库（用于存储论文）</label>
                <select
                  value={selectedKb}
                  onChange={(e) => setSelectedKb(e.target.value)}
                  className="input-field"
                >
                  <option value="">选择已有知识库，或新建一个</option>
                  {kbs.map((kb) => (
                    <option key={kb.kb_id} value={kb.kb_id}>{kb.name}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  提示：去"知识库管家"页面创建新知识库，专门用于存放你的论文
                </p>
              </div>

              {/* Upload Area */}
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={clsx(
                  'relative rounded-2xl border-2 border-dashed p-12 text-center transition-colors max-w-lg',
                  dragOver ? 'border-purple-400 bg-purple-50' : 'border-gray-300 hover:border-gray-400',
                  !selectedKb && 'opacity-50 cursor-not-allowed'
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".doc,.docx,.pdf,.txt"
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={!selectedKb}
                />
                <div className="flex flex-col items-center pointer-events-none">
                  <Upload className="h-10 w-10 text-purple-400 mb-3" />
                  <h3 className="text-base font-medium text-gray-900 mb-1">上传论文</h3>
                  <p className="text-sm text-gray-500">拖拽 Word (.doc/.docx) 或 PDF 文件到此处</p>
                  <p className="text-xs text-gray-400 mt-1">支持 .docx、.doc、.pdf、.txt 格式</p>
                </div>
              </div>

              {!selectedKb && (
                <p className="text-sm text-orange-600 max-w-lg">请先选择一个知识库来存储论文内容</p>
              )}
            </div>
          )}

          {uploading && (
            <div className="mb-6 flex items-center justify-center gap-2 py-8">
              <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
              <span className="text-sm text-gray-600">正在上传并解析论文...</span>
            </div>
          )}

          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              <span className="flex-1">{error}</span>
              <button onClick={() => setError('')}><X className="h-4 w-4" /></button>
            </div>
          )}

          {paperKbId && (
            <>
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm text-gray-600">当前论文：<strong>{paperTitle}</strong></p>
                <button onClick={() => { setPaperKbId(''); setPaperTitle(''); setSummary(null); setSocraticQuestions([]); setRecommendations([]); }}
                        className="text-xs text-gray-500 hover:text-red-600">
                  上传其他论文
                </button>
              </div>

              <div className="flex items-center gap-1 border-b border-gray-200 mb-6">
                {[
                  { id: 'summary' as Tab, label: '摘要', icon: BookOpen },
                  { id: 'socratic' as Tab, label: '深度精读', icon: Lightbulb },
                  { id: 'recommend' as Tab, label: '文献推荐', icon: Network },
                ].map((tab) => {
                  const Icon = tab.icon
                  return (
                    <button
                      key={tab.id}
                      onClick={() => handleTabChange(tab.id)}
                      className={clsx(
                        'flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors -mb-px',
                        activeTab === tab.id
                          ? 'border-purple-600 text-purple-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {tab.label}
                    </button>
                  )
                })}
              </div>

              {/* Summary Tab */}
              {activeTab === 'summary' && (
                <div>
                  {summaryLoading && (
                    <div className="flex items-center justify-center gap-2 py-16">
                      <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                      <span className="text-sm text-gray-600">正在生成摘要...</span>
                    </div>
                  )}
                  {summary && (
                    <div className="space-y-6 max-w-3xl">
                      <h2 className="text-xl font-bold text-gray-900">{summary.title_guess || paperTitle}</h2>

                      {summary.abstract_summary && (
                        <section className="rounded-xl border border-gray-200 bg-white p-6">
                          <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">概述</h3>
                          <p className="text-sm text-gray-700 leading-relaxed">{summary.abstract_summary}</p>
                        </section>
                      )}

                      {summary.key_contributions.length > 0 && (
                        <section className="rounded-xl border border-gray-200 bg-white p-6">
                          <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">核心贡献</h3>
                          <ul className="space-y-2">
                            {summary.key_contributions.map((c, i) => (
                              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                                <Star className="h-4 w-4 text-purple-400 shrink-0 mt-0.5" />
                                <span>{c}</span>
                              </li>
                            ))}
                          </ul>
                        </section>
                      )}

                      {summary.methodology_summary && (
                        <section className="rounded-xl border border-gray-200 bg-white p-6">
                          <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">研究方法</h3>
                          <p className="text-sm text-gray-700 leading-relaxed">{summary.methodology_summary}</p>
                        </section>
                      )}

                      {summary.findings_summary && (
                        <section className="rounded-xl border border-gray-200 bg-white p-6">
                          <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">主要发现</h3>
                          <div className="prose prose-sm max-w-none text-sm text-gray-700">
                            <ReactMarkdown>{summary.findings_summary}</ReactMarkdown>
                          </div>
                        </section>
                      )}

                      {(summary.limitations.length > 0 || summary.future_work) && (
                        <section className="rounded-xl border border-gray-200 bg-white p-6">
                          <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">局限性与未来工作</h3>
                          {summary.limitations.length > 0 && (
                            <ul className="space-y-2 mb-3">
                              {summary.limitations.map((l, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                                  <X className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                                  <span>{l}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                          {summary.future_work && (
                            <p className="text-sm text-gray-700">{summary.future_work}</p>
                          )}
                        </section>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Socratic Tab */}
              {activeTab === 'socratic' && (
                <div>
                  {socraticLoading && (
                    <div className="flex items-center justify-center gap-2 py-16">
                      <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                      <span className="text-sm text-gray-600">正在生成苏格拉底式问题...</span>
                    </div>
                  )}
                  {socraticQuestions.length > 0 && currentQ && (
                    <div className="max-w-3xl space-y-6">
                      <div className="flex items-center gap-2">
                        {socraticQuestions.map((_, i) => (
                          <div key={i} className={clsx(
                            'h-1.5 flex-1 rounded-full transition-colors',
                            i < currentQuestionIdx ? 'bg-purple-500' :
                            i === currentQuestionIdx ? 'bg-purple-400' : 'bg-gray-200'
                          )} />
                        ))}
                        <span className="text-xs text-gray-500 ml-2 shrink-0">
                          {currentQuestionIdx + 1} / {socraticQuestions.length}
                        </span>
                      </div>

                      <div className="rounded-xl border border-purple-200 bg-purple-50/50 p-6">
                        <div className="flex items-start gap-3 mb-3">
                          <Lightbulb className="h-5 w-5 text-purple-500 shrink-0 mt-0.5" />
                          <h3 className="text-base font-medium text-gray-900">{currentQ.question}</h3>
                        </div>
                        <p className="text-sm text-gray-500 ml-8">
                          <span className="font-medium text-purple-600">提示：</span>{currentQ.hint || currentQ.purpose}
                        </p>
                      </div>

                      {!currentEval ? (
                        <div className="space-y-3">
                          <textarea
                            value={socraticResponse}
                            onChange={(e) => setSocraticResponse(e.target.value)}
                            placeholder="写下你的理解和思考..."
                            rows={4}
                            className="input-field resize-none"
                          />
                          <button
                            onClick={handleEvaluateResponse}
                            disabled={evalLoading || !socraticResponse.trim()}
                            className="btn-primary gap-2"
                          >
                            {evalLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
                            提交回答
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <div className={clsx(
                            'rounded-xl border p-5',
                            currentEval.understanding_level === 'insightful' ? 'border-emerald-200 bg-emerald-50' :
                            currentEval.understanding_level === 'deep' ? 'border-yellow-200 bg-yellow-50' : 'border-red-200 bg-red-50'
                          )}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-semibold">理解程度：</span>
                              <span className={clsx(
                                'text-base font-bold',
                                currentEval.understanding_level === 'insightful' ? 'text-emerald-600' :
                                currentEval.understanding_level === 'deep' ? 'text-yellow-600' : 'text-red-600'
                              )}>
                                {currentEval.understanding_level === 'insightful' ? '深刻' :
                                 currentEval.understanding_level === 'deep' ? '较深' : '表面'}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 mb-3">{currentEval.feedback}</p>
                            {currentEval.follow_up_question && (
                              <p className="text-sm text-purple-600 italic">追问：{currentEval.follow_up_question}</p>
                            )}
                          </div>

                          {currentQuestionIdx < socraticQuestions.length - 1 ? (
                            <button
                              onClick={() => { setCurrentQuestionIdx((prev) => prev + 1); setSocraticResponse('') }}
                              className="btn-primary gap-2"
                            >
                              <ArrowRight className="h-4 w-4" />下一题
                            </button>
                          ) : (
                            <div className="rounded-xl border border-purple-200 bg-purple-50 p-5 text-center">
                              <CheckCircle className="h-8 w-8 text-purple-500 mx-auto mb-2" />
                              <p className="text-sm font-medium text-purple-700">精读完成！</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Recommend Tab */}
              {activeTab === 'recommend' && (
                <div>
                  {litLoading && (
                    <div className="flex items-center justify-center gap-2 py-16">
                      <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                      <span className="text-sm text-gray-600">正在分析文献关系...</span>
                    </div>
                  )}
                  {recommendations.length > 0 && (
                    <div className="space-y-4 max-w-3xl">
                      <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-4">推荐相关文献</h3>
                      <div className="space-y-3">
                        {recommendations.map((rec, i) => (
                          <div key={i} className="rounded-xl border border-gray-200 bg-white p-5 card-hover">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 min-w-0">
                                <h4 className="text-sm font-medium text-gray-900 mb-1">{rec.title}</h4>
                                <p className="text-xs text-gray-500">{rec.authors_guess || ''}</p>
                                <p className="text-sm text-gray-600 mt-2">{rec.relevance_reason}</p>
                                {rec.topics_shared && rec.topics_shared.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mt-2">
                                    {rec.topics_shared.map((t, j) => (
                                      <span key={j} className="inline-flex rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-700">{t}</span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
