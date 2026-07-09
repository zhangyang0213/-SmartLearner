'use client'

import { useState, useRef, useEffect } from 'react'
import Sidebar from '@/components/Sidebar'
import { FileText, Upload, Loader2, X, Lightbulb, BookOpen, Network, Star, CheckCircle, ArrowRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'
import { uploadFiles, listKBs, summarize, generateSocratic, evaluateSocratic, recommendLiterature } from '@/lib/api'

type Tab = 'summary' | 'socratic' | 'recommend'

interface KBItem {
  kb_id: string
  name: string
}

interface SummaryData {
  title_guess: string
  abstract_summary: string
  key_contributions: string[]
  methodology_summary: string
  findings_summary: string
  limitations: string[]
  future_work: string
  overall_assessment: string
}

interface SocraticQuestion {
  question: string
  purpose: string
  hint: string
  depth_level: number
}

interface SocraticEval {
  understanding_level: string
  feedback: string
  follow_up_question: string
}

interface LiteratureRec {
  title: string
  authors_guess: string
  relevance_reason: string
  topics_shared: string[]
}

export default function PaperPage() {
  const [paperKbId, setPaperKbId] = useState('')
  const [paperTitle, setPaperTitle] = useState('')
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('summary')
  const [error, setError] = useState('')

  const [kbs, setKbs] = useState<KBItem[]>([])
  const [selectedKb, setSelectedKb] = useState('')

  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  const [socraticQuestions, setSocraticQuestions] = useState<SocraticQuestion[]>([])
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0)
  const [socraticResponse, setSocraticResponse] = useState('')
  const [socraticLoading, setSocraticLoading] = useState(false)
  const [evalLoading, setEvalLoading] = useState(false)
  const [evaluations, setEvaluations] = useState<Record<number, SocraticEval>>({})

  const [recommendations, setRecommendations] = useState<LiteratureRec[]>([])
  const [litLoading, setLitLoading] = useState(false)

  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { loadKBs() }, [])

  async function loadKBs() {
    try {
      const data = await listKBs()
      setKbs((data.knowledge_bases || []).map((kb: any) => ({ kb_id: kb.kb_id, name: kb.name })))
    } catch { setKbs([]) }
  }

  async function handleUploadFile(file: File) {
    if (!selectedKb) {
      setError('请先选择一个知识库')
      return
    }
    setUploading(true)
    setError('')
    try {
      await uploadFiles(selectedKb, [file])
      const title = file.name.replace(/\.(docx|doc|pdf|txt|md)$/i, '').replace(/_/g, ' ')
      setPaperKbId(selectedKb)
      setPaperTitle(title)
      // 上传成功后自动加载摘要
      loadSummary(selectedKb)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg || '上传失败')
    } finally {
      setUploading(false)
    }
  }

  function handleTabChange(tab: Tab) {
    setActiveTab(tab)
    // 使用 paperKbId 的最新值
    const kbId = paperKbId
    if (!kbId) return
    if (tab === 'summary' && !summary) loadSummary(kbId)
    if (tab === 'socratic' && socraticQuestions.length === 0) loadSocratic(kbId)
    if (tab === 'recommend' && recommendations.length === 0) loadRecommendations(kbId)
  }

  async function loadSummary(kbId: string) {
    if (!kbId) return
    setSummaryLoading(true)
    setError('')
    try {
      const data = await summarize(kbId)
      // 后端 limitations 可能是字符串或数组，统一转为数组
      let limitations: string[] = []
      if (Array.isArray(data.limitations)) {
        limitations = data.limitations
      } else if (typeof data.limitations === 'string' && data.limitations.trim()) {
        limitations = [data.limitations]
      }
      let keyContributions: string[] = []
      if (Array.isArray(data.key_contributions)) {
        keyContributions = data.key_contributions
      } else if (typeof data.key_contributions === 'string') {
        keyContributions = [data.key_contributions]
      }
      setSummary({
        title_guess: data.title_guess || '',
        abstract_summary: data.abstract_summary || '',
        key_contributions: keyContributions,
        methodology_summary: data.methodology_summary || '',
        findings_summary: data.findings_summary || '',
        limitations,
        future_work: data.future_work || '',
        overall_assessment: data.overall_assessment || '',
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取摘要失败')
    } finally {
      setSummaryLoading(false)
    }
  }

  async function loadSocratic(kbId: string) {
    if (!kbId) return
    setSocraticLoading(true)
    setError('')
    try {
      const data = await generateSocratic(kbId)
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
    const q = socraticQuestions[currentQuestionIdx]
    if (!paperKbId || !q || !socraticResponse.trim()) return
    setEvalLoading(true)
    setError('')
    try {
      const data = await evaluateSocratic(paperKbId, q.question, socraticResponse)
      setEvaluations(prev => ({
        ...prev,
        [currentQuestionIdx]: {
          understanding_level: data.understanding_level || 'surface',
          feedback: data.feedback || '',
          follow_up_question: data.follow_up_question || '',
        },
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : '评估失败')
    } finally {
      setEvalLoading(false)
    }
  }

  async function loadRecommendations(kbId: string) {
    if (!kbId) return
    setLitLoading(true)
    setError('')
    try {
      const data = await recommendLiterature(kbId, 5)
      setRecommendations(data.recommendations || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取推荐失败')
    } finally {
      setLitLoading(false)
    }
  }

  const currentQ = socraticQuestions[currentQuestionIdx]
  const currentEval = evaluations[currentQuestionIdx]

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="flex h-16 items-center gap-4 px-4 sm:px-6 lg:px-8 pl-16 lg:pl-8">
            <FileText className="h-5 w-5 text-purple-600" />
            <h1 className="text-lg font-semibold text-gray-900">论文精读教练</h1>
            {paperTitle && <span className="hidden sm:inline text-sm text-gray-500 truncate ml-2">— {paperTitle}</span>}
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8">
          {!paperKbId ? (
            <div className="max-w-lg mx-auto space-y-4 py-8">
              <div className="flex flex-col items-center text-center mb-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-50 mb-4">
                  <FileText className="h-8 w-8 text-purple-500" />
                </div>
                <h3 className="text-base font-medium text-gray-900 mb-1">上传论文</h3>
                <p className="text-sm text-gray-500">选择知识库后上传论文，AI 将为你精读分析</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">选择知识库</label>
                <select
                  value={selectedKb}
                  onChange={(e) => setSelectedKb(e.target.value)}
                  className="input-field"
                >
                  <option value="">选择已有知识库</option>
                  {kbs.map((kb) => (
                    <option key={kb.kb_id} value={kb.kb_id}>{kb.name}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  没有知识库？去"知识库管家"页面先创建一个
                </p>
              </div>

              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setDragOver(false)
                  const file = e.dataTransfer.files[0]
                  if (file) handleUploadFile(file)
                }}
                className={clsx(
                  'relative rounded-2xl border-2 border-dashed p-10 text-center transition-colors',
                  dragOver ? 'border-purple-400 bg-purple-50' : 'border-gray-300 hover:border-gray-400',
                  !selectedKb && 'opacity-50'
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".doc,.docx,.pdf,.txt,.md"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUploadFile(f) }}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={!selectedKb}
                />
                <Upload className="h-8 w-8 text-purple-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">拖拽或点击选择论文文件</p>
                <p className="text-xs text-gray-400 mt-1">支持 .docx .doc .pdf .txt .md</p>
              </div>

              {uploading && (
                <div className="flex items-center justify-center gap-2 py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                  <span className="text-sm text-gray-600">正在上传并解析...</span>
                </div>
              )}
            </div>
          ) : (
            <>
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm text-gray-600">当前论文：<strong>{paperTitle}</strong></p>
                <button onClick={() => { setPaperKbId(''); setPaperTitle(''); setSummary(null); setSocraticQuestions([]); setRecommendations([]) }}
                  className="text-xs text-gray-500 hover:text-red-600">换一篇论文</button>
              </div>

              {/* 上传后自动加载摘要 */}
              {error && (
                <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                  <span className="flex-1">{error}</span>
                  <button onClick={() => setError('')}><X className="h-4 w-4" /></button>
                </div>
              )}

              <div className="flex items-center gap-1 border-b border-gray-200 mb-6">
                {([
                  { id: 'summary' as Tab, label: '摘要', icon: BookOpen },
                  { id: 'socratic' as Tab, label: '深度精读', icon: Lightbulb },
                  { id: 'recommend' as Tab, label: '文献推荐', icon: Network },
                ]).map((tab) => {
                  const Icon = tab.icon
                  return (
                    <button key={tab.id} onClick={() => handleTabChange(tab.id)}
                      className={clsx(
                        'flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors -mb-px',
                        activeTab === tab.id ? 'border-purple-600 text-purple-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                      )}>
                      <Icon className="h-4 w-4" />{tab.label}
                    </button>
                  )
                })}
              </div>

              {activeTab === 'summary' && (
                <div>
                  {!summary && !summaryLoading && (
                    <div className="text-center py-8">
                      <button onClick={() => loadSummary(paperKbId)} className="btn-primary gap-2">
                        <BookOpen className="h-4 w-4" />生成论文摘要
                      </button>
                    </div>
                  )}
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
                                <Star className="h-4 w-4 text-purple-400 shrink-0 mt-0.5" /><span>{c}</span>
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
                                  <X className="h-4 w-4 text-red-400 shrink-0 mt-0.5" /><span>{l}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                          {summary.future_work && <p className="text-sm text-gray-700">{summary.future_work}</p>}
                        </section>
                      )}
                      {summary.overall_assessment && (
                        <section className="rounded-xl border border-purple-200 bg-purple-50/50 p-6">
                          <h3 className="text-sm font-semibold text-purple-700 uppercase tracking-wider mb-3">总体评价</h3>
                          <p className="text-sm text-gray-700 leading-relaxed">{summary.overall_assessment}</p>
                        </section>
                      )}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'socratic' && (
                <div>
                  {socraticQuestions.length === 0 && !socraticLoading && (
                    <div className="text-center py-8">
                      <button onClick={() => loadSocratic(paperKbId)} className="btn-primary gap-2">
                        <Lightbulb className="h-4 w-4" />开始深度精读
                      </button>
                    </div>
                  )}
                  {socraticLoading && (
                    <div className="flex items-center justify-center gap-2 py-16">
                      <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                      <span className="text-sm text-gray-600">正在生成问题...</span>
                    </div>
                  )}
                  {socraticQuestions.length > 0 && currentQ && (
                    <div className="max-w-3xl space-y-6">
                      <div className="flex items-center gap-2">
                        {socraticQuestions.map((_, i) => (
                          <div key={i} className={clsx(
                            'h-1.5 flex-1 rounded-full transition-colors',
                            i < currentQuestionIdx ? 'bg-purple-500' : i === currentQuestionIdx ? 'bg-purple-400' : 'bg-gray-200'
                          )} />
                        ))}
                        <span className="text-xs text-gray-500 ml-2 shrink-0">{currentQuestionIdx + 1}/{socraticQuestions.length}</span>
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
                          <textarea value={socraticResponse} onChange={(e) => setSocraticResponse(e.target.value)}
                            placeholder="写下你的理解和思考..." rows={4} className="input-field resize-none" />
                          <button onClick={handleEvaluateResponse}
                            disabled={evalLoading || !socraticResponse.trim()} className="btn-primary gap-2">
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
                            <p className="text-sm font-semibold mb-1">
                              理解程度：
                              {currentEval.understanding_level === 'insightful' ? '深刻' :
                               currentEval.understanding_level === 'deep' ? '较深' : '表面'}
                            </p>
                            <p className="text-sm text-gray-700 mb-2">{currentEval.feedback}</p>
                            {currentEval.follow_up_question && (
                              <p className="text-sm text-purple-600 italic">追问：{currentEval.follow_up_question}</p>
                            )}
                          </div>
                          {currentQuestionIdx < socraticQuestions.length - 1 ? (
                            <button onClick={() => { setCurrentQuestionIdx(prev => prev + 1); setSocraticResponse('') }}
                              className="btn-primary gap-2"><ArrowRight className="h-4 w-4" />下一题</button>
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

              {activeTab === 'recommend' && (
                <div>
                  {recommendations.length === 0 && !litLoading && (
                    <div className="text-center py-8">
                      <button onClick={() => loadRecommendations(paperKbId)} className="btn-primary gap-2">
                        <Network className="h-4 w-4" />推荐相关文献
                      </button>
                    </div>
                  )}
                  {litLoading && (
                    <div className="flex items-center justify-center gap-2 py-16">
                      <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                      <span className="text-sm text-gray-600">正在分析...</span>
                    </div>
                  )}
                  {recommendations.length > 0 && (
                    <div className="space-y-3 max-w-3xl">
                      {recommendations.map((rec, i) => (
                        <div key={i} className="rounded-xl border border-gray-200 bg-white p-5">
                          <h4 className="text-sm font-medium text-gray-900 mb-1">{rec.title}</h4>
                          <p className="text-xs text-gray-500">{rec.authors_guess || ''}</p>
                          <p className="text-sm text-gray-600 mt-2">{rec.relevance_reason}</p>
                          {rec.topics_shared?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {rec.topics_shared.map((t, j) => (
                                <span key={j} className="inline-flex rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-700">{t}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
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
