'use client'

import { useState, useCallback } from 'react'
import Sidebar from '@/components/Sidebar'
import { FileText, Upload, Loader2, X, Lightbulb, BookOpen, Network, Star, CheckCircle, ArrowRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'
import { uploadPaper, summarize, generateSocratic, evaluateSocratic, recommendLiterature } from '@/lib/api'

type Tab = 'summary' | 'socratic' | 'recommend'

interface SummaryData {
  title: string
  key_contributions: string[]
  methodology: string
  findings: string[]
  limitations: string[]
}

interface SocraticQuestion {
  id: string
  question: string
  hint: string
  key_points: string[]
}

interface SocraticEval {
  score: number
  feedback: string
  key_points_covered: string[]
  suggestions: string[]
}

interface LiteratureRec {
  title: string
  authors: string
  year: number
  relevance: number
  reason: string
}

export default function PaperPage() {
  const [paperId, setPaperId] = useState<string>('')
  const [paperTitle, setPaperTitle] = useState<string>('')
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('summary')
  const [error, setError] = useState<string>('')

  // Summary state
  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  // Socratic state
  const [socraticQuestions, setSocraticQuestions] = useState<SocraticQuestion[]>([])
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0)
  const [socraticResponse, setSocraticResponse] = useState('')
  const [socraticLoading, setSocraticLoading] = useState(false)
  const [evalLoading, setEvalLoading] = useState(false)
  const [evaluations, setEvaluations] = useState<Record<string, SocraticEval>>({})

  // Literature state
  const [recommendations, setRecommendations] = useState<LiteratureRec[]>([])
  const [litLoading, setLitLoading] = useState(false)
  const [literatureMap, setLiteratureMap] = useState<{ nodes: Array<{ id: string; label: string; group: string }>; edges: Array<{ source: string; target: string; weight: number }> } | null>(null)

  // Drag state
  const [dragOver, setDragOver] = useState(false)

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true)
    setError('')
    try {
      const data = await uploadPaper(file)
      setPaperId(data.paper_id)
      setPaperTitle(data.title || file.name)
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传论文失败')
    } finally {
      setUploading(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && (file.type === 'application/pdf' || file.name.endsWith('.pdf'))) {
      handleUpload(file)
    } else {
      setError('请上传PDF格式的论文文件')
    }
  }, [handleUpload])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleUpload(file)
  }, [handleUpload])

  async function handleLoadSummary() {
    if (!paperId) return
    setSummaryLoading(true)
    setError('')
    try {
      const data = await summarize(paperId)
      setSummary({
        title: data.title,
        key_contributions: data.key_contributions,
        methodology: data.methodology,
        findings: data.findings,
        limitations: data.limitations,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取摘要失败')
    } finally {
      setSummaryLoading(false)
    }
  }

  async function handleLoadSocratic() {
    if (!paperId) return
    setSocraticLoading(true)
    setError('')
    try {
      const data = await generateSocratic(paperId)
      setSocraticQuestions(data.questions)
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
    if (!paperId || !socraticQuestions[currentQuestionIdx] || !socraticResponse.trim()) return
    setEvalLoading(true)
    setError('')
    try {
      const data = await evaluateSocratic(paperId, socraticQuestions[currentQuestionIdx].id, socraticResponse)
      setEvaluations((prev) => ({
        ...prev,
        [socraticQuestions[currentQuestionIdx].id]: {
          score: data.score,
          feedback: data.feedback,
          key_points_covered: data.key_points_covered,
          suggestions: data.suggestions,
        },
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : '评估失败')
    } finally {
      setEvalLoading(false)
    }
  }

  async function handleLoadRecommendations() {
    if (!paperId) return
    setLitLoading(true)
    setError('')
    try {
      const data = await recommendLiterature(paperId)
      setRecommendations(data.recommendations)
      setLiteratureMap(data.literature_map)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取推荐失败')
    } finally {
      setLitLoading(false)
    }
  }

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab)
    if (tab === 'summary' && !summary && paperId) handleLoadSummary()
    if (tab === 'socratic' && socraticQuestions.length === 0 && paperId) handleLoadSocratic()
    if (tab === 'recommend' && recommendations.length === 0 && paperId) handleLoadRecommendations()
  }

  const currentQ = socraticQuestions[currentQuestionIdx]
  const currentEval = currentQ ? evaluations[currentQ.id] : null

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="lg:pl-60">
        {/* Header */}
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
          {!paperId && (
            <div className="mb-6">
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={clsx(
                  'relative rounded-2xl border-2 border-dashed p-12 text-center transition-colors',
                  dragOver ? 'border-purple-400 bg-purple-50' : 'border-gray-300 hover:border-gray-400'
                )}
              >
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="flex flex-col items-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-purple-50 mb-4">
                    <Upload className="h-7 w-7 text-purple-500" />
                  </div>
                  <h3 className="text-base font-medium text-gray-900 mb-1">上传论文</h3>
                  <p className="text-sm text-gray-500">拖拽PDF文件到此处，或点击选择文件</p>
                </div>
              </div>
            </div>
          )}

          {/* Upload indicator */}
          {uploading && (
            <div className="mb-6 flex items-center justify-center gap-2 py-8">
              <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
              <span className="text-sm text-gray-600">正在上传并解析论文...</span>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              <span className="flex-1">{error}</span>
              <button onClick={() => setError('')}><X className="h-4 w-4" /></button>
            </div>
          )}

          {/* Content - only show after upload */}
          {paperId && (
            <>
              {/* Tab Navigation */}
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
                      <h2 className="text-xl font-bold text-gray-900">{summary.title}</h2>

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

                      <section className="rounded-xl border border-gray-200 bg-white p-6">
                        <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">研究方法</h3>
                        <p className="text-sm text-gray-700 leading-relaxed">{summary.methodology}</p>
                      </section>

                      <section className="rounded-xl border border-gray-200 bg-white p-6">
                        <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">主要发现</h3>
                        <ul className="space-y-2">
                          {summary.findings.map((f, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                              <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                              <span>{f}</span>
                            </li>
                          ))}
                        </ul>
                      </section>

                      <section className="rounded-xl border border-gray-200 bg-white p-6">
                        <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">局限性</h3>
                        <ul className="space-y-2">
                          {summary.limitations.map((l, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                              <X className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                              <span>{l}</span>
                            </li>
                          ))}
                        </ul>
                      </section>
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
                      {/* Progress */}
                      <div className="flex items-center gap-2">
                        {socraticQuestions.map((_, i) => (
                          <div
                            key={i}
                            className={clsx(
                              'h-1.5 flex-1 rounded-full transition-colors',
                              i < currentQuestionIdx ? 'bg-purple-500' :
                              i === currentQuestionIdx ? 'bg-purple-400' : 'bg-gray-200'
                            )}
                          />
                        ))}
                        <span className="text-xs text-gray-500 ml-2 shrink-0">
                          {currentQuestionIdx + 1} / {socraticQuestions.length}
                        </span>
                      </div>

                      {/* Question Card */}
                      <div className="rounded-xl border border-purple-200 bg-purple-50/50 p-6">
                        <div className="flex items-start gap-3 mb-3">
                          <Lightbulb className="h-5 w-5 text-purple-500 shrink-0 mt-0.5" />
                          <h3 className="text-base font-medium text-gray-900">{currentQ.question}</h3>
                        </div>
                        <p className="text-sm text-gray-500 ml-8">
                          <span className="font-medium text-purple-600">提示：</span>{currentQ.hint}
                        </p>
                      </div>

                      {/* Response Input */}
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
                          {/* Evaluation Result */}
                          <div className={clsx(
                            'rounded-xl border p-5',
                            currentEval.score >= 70 ? 'border-emerald-200 bg-emerald-50' :
                            currentEval.score >= 40 ? 'border-yellow-200 bg-yellow-50' : 'border-red-200 bg-red-50'
                          )}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-semibold">评分：</span>
                              <span className={clsx(
                                'text-lg font-bold',
                                currentEval.score >= 70 ? 'text-emerald-600' :
                                currentEval.score >= 40 ? 'text-yellow-600' : 'text-red-600'
                              )}>
                                {currentEval.score}分
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 mb-3">{currentEval.feedback}</p>
                            {currentEval.key_points_covered.length > 0 && (
                              <div className="mb-2">
                                <p className="text-xs font-medium text-gray-500 mb-1">已覆盖要点：</p>
                                <div className="flex flex-wrap gap-1.5">
                                  {currentEval.key_points_covered.map((p, i) => (
                                    <span key={i} className="inline-flex rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs text-emerald-700">{p}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {currentEval.suggestions.length > 0 && (
                              <div>
                                <p className="text-xs font-medium text-gray-500 mb-1">改进建议：</p>
                                <ul className="space-y-1">
                                  {currentEval.suggestions.map((s, i) => (
                                    <li key={i} className="text-xs text-gray-600">• {s}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Next button */}
                          {currentQuestionIdx < socraticQuestions.length - 1 ? (
                            <button
                              onClick={() => {
                                setCurrentQuestionIdx((prev) => prev + 1)
                                setSocraticResponse('')
                              }}
                              className="btn-primary gap-2"
                            >
                              <ArrowRight className="h-4 w-4" />
                              下一题
                            </button>
                          ) : (
                            <div className="rounded-xl border border-purple-200 bg-purple-50 p-5 text-center">
                              <p className="text-sm font-medium text-purple-700">精读完成！</p>
                              <p className="text-xs text-purple-600 mt-1">
                                平均得分：{Math.round(Object.values(evaluations).reduce((s, e) => s + e.score, 0) / Object.values(evaluations).length)}分
                              </p>
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
                    <div className="space-y-6 max-w-3xl">
                      {/* Literature Map Visualization */}
                      {literatureMap && literatureMap.nodes.length > 0 && (
                        <section className="rounded-xl border border-gray-200 bg-white p-6">
                          <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-4">文献关系图谱</h3>
                          <div className="relative w-full h-64 bg-gray-50 rounded-lg overflow-hidden">
                            <svg viewBox="0 0 600 250" className="w-full h-full">
                              {literatureMap.nodes.map((node, i) => {
                                const cols = Math.ceil(Math.sqrt(literatureMap.nodes.length))
                                const x = 80 + (i % cols) * (440 / cols)
                                const y = 50 + Math.floor(i / cols) * (180 / Math.ceil(literatureMap.nodes.length / cols))
                                return (
                                  <g key={node.id}>
                                    <circle
                                      cx={x}
                                      cy={y}
                                      r={node.id === paperId ? 14 : 10}
                                      fill={node.id === paperId ? '#7c3aed' : '#6366f1'}
                                      opacity={0.8}
                                    />
                                    <text
                                      x={x}
                                      y={y + 24}
                                      textAnchor="middle"
                                      className="text-[8px] fill-gray-600"
                                    >
                                      {node.label.length > 12 ? node.label.slice(0, 12) + '...' : node.label}
                                    </text>
                                  </g>
                                )
                              })}
                              {literatureMap.edges.map((edge, i) => {
                                const sourceIdx = literatureMap.nodes.findIndex((n) => n.id === edge.source)
                                const targetIdx = literatureMap.nodes.findIndex((n) => n.id === edge.target)
                                if (sourceIdx === -1 || targetIdx === -1) return null
                                const cols = Math.ceil(Math.sqrt(literatureMap.nodes.length))
                                const x1 = 80 + (sourceIdx % cols) * (440 / cols)
                                const y1 = 50 + Math.floor(sourceIdx / cols) * (180 / Math.ceil(literatureMap.nodes.length / cols))
                                const x2 = 80 + (targetIdx % cols) * (440 / cols)
                                const y2 = 50 + Math.floor(targetIdx / cols) * (180 / Math.ceil(literatureMap.nodes.length / cols))
                                return (
                                  <line
                                    key={i}
                                    x1={x1} y1={y1} x2={x2} y2={y2}
                                    stroke="#c4b5fd"
                                    strokeWidth={Math.max(1, edge.weight * 2)}
                                    opacity={0.5}
                                  />
                                )
                              })}
                            </svg>
                          </div>
                        </section>
                      )}

                      {/* Recommendation Cards */}
                      <section>
                        <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-4">推荐文献</h3>
                        <div className="space-y-3">
                          {recommendations.map((rec, i) => (
                            <div key={i} className="rounded-xl border border-gray-200 bg-white p-5 card-hover">
                              <div className="flex items-start justify-between gap-4">
                                <div className="flex-1 min-w-0">
                                  <h4 className="text-sm font-medium text-gray-900 mb-1">{rec.title}</h4>
                                  <p className="text-xs text-gray-500">{rec.authors} · {rec.year}</p>
                                  <p className="text-sm text-gray-600 mt-2">{rec.reason}</p>
                                </div>
                                <div className="shrink-0 text-right">
                                  <div className="inline-flex items-center gap-1 rounded-full bg-purple-50 px-2.5 py-1 text-xs font-medium text-purple-700">
                                    <Star className="h-3 w-3" />
                                    {Math.round(rec.relevance * 100)}%
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </section>
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
