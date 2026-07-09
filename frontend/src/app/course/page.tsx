'use client'

import { useState, useRef, useEffect } from 'react'
import Sidebar from '@/components/Sidebar'
import { BookOpen, Upload, Send, ChevronDown, ClipboardCheck, Loader2, X, File, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'
import { uploadFiles, askQuestion, generateQuiz, evaluateQuiz, listKBs } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{ content: string; score: number }>
}

interface KBItem {
  kb_id: string
  name: string
  description: string
  doc_count: number
  chunk_count: number
}

interface QuizQuestion {
  id: string
  type: string
  question_text: string
  options: string[]
  correct_answer: string
  explanation: string
  bloom_level: number
  difficulty: string
}

export default function CoursePage() {
  const [kbs, setKbs] = useState<KBItem[]>([])
  const [selectedKb, setSelectedKb] = useState<string>('')
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [mode, setMode] = useState<'chat' | 'quiz'>('chat')
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([])
  const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({})
  const [quizSubmitted, setQuizSubmitted] = useState(false)
  const [quizEvaluations, setQuizEvaluations] = useState<Record<string, { score: number; feedback: string; correct_answer: string }>>({})
  const [quizTopic, setQuizTopic] = useState('')
  const [quizDifficulty, setQuizDifficulty] = useState('medium')
  const [quizNumQuestions, setQuizNumQuestions] = useState(5)
  const [generatingQuiz, setGeneratingQuiz] = useState(false)
  const [error, setError] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [kbsLoading, setKbsLoading] = useState(true)

  useEffect(() => { loadKBs() }, [])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function loadKBs() {
    try {
      setKbsLoading(true)
      const data = await listKBs()
      setKbs(data.knowledge_bases || [])
      if (data.knowledge_bases?.length > 0 && !selectedKb) {
        setSelectedKb(data.knowledge_bases[0].kb_id)
      }
    } catch {
      setKbs([])
    } finally {
      setKbsLoading(false)
    }
  }

  async function handleUpload() {
    const files = fileInputRef.current?.files
    if (!files?.length || !selectedKb) return
    setUploading(true)
    setError('')
    try {
      await uploadFiles(selectedKb, Array.from(files))
      const fileNames = Array.from(files).map((f) => f.name)
      setUploadedFiles((prev) => [...prev, ...fileNames])
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
    }
  }

  async function handleSend() {
    if (!input.trim() || !selectedKb || loading) return
    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)
    setError('')
    try {
      const data = await askQuestion(selectedKb, userMessage)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.answer, sources: data.sources }])
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerateQuiz() {
    if (!selectedKb) return
    setGeneratingQuiz(true)
    setError('')
    setQuizSubmitted(false)
    setQuizEvaluations({})
    setQuizAnswers({})
    try {
      const data = await generateQuiz(selectedKb, quizTopic || '课程内容', quizNumQuestions, quizDifficulty)
      setQuizQuestions(data.questions || [])
      setMode('quiz')
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成测验失败')
    } finally {
      setGeneratingQuiz(false)
    }
  }

  async function handleSubmitQuiz() {
    if (quizQuestions.length === 0) return
    setLoading(true)
    setError('')
    try {
      // 逐题评估
      const evals: Record<string, { score: number; feedback: string; correct_answer: string }> = {}
      for (const q of quizQuestions) {
        const userAnswer = quizAnswers[q.id] || ''
        try {
          const result = await evaluateQuiz(q as any, userAnswer)
          evals[q.id] = result
        } catch {
          evals[q.id] = { score: 0, feedback: '评估失败', correct_answer: q.correct_answer }
        }
      }
      setQuizEvaluations(evals)
      setQuizSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交测验失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="flex h-16 items-center gap-4 px-4 sm:px-6 lg:px-8 pl-16 lg:pl-8">
            <BookOpen className="h-5 w-5 text-blue-600" />
            <h1 className="text-lg font-semibold text-gray-900">课程问答助手</h1>
          </div>
        </header>

        <div className="flex flex-col lg:flex-row h-[calc(100vh-4rem)]">
          {/* Left Panel */}
          <div className="w-full lg:w-72 shrink-0 border-b lg:border-b-0 lg:border-r border-gray-200 bg-white p-4 overflow-y-auto">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">知识库</h2>
            <div className="relative mb-4">
              <select
                value={selectedKb}
                onChange={(e) => setSelectedKb(e.target.value)}
                className="input-field appearance-none pr-8"
              >
                <option value="">选择知识库</option>
                {kbs.map((kb) => (
                  <option key={kb.kb_id} value={kb.kb_id}>{kb.name}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            </div>

            <div className="mb-4">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.doc,.docx,.pptx,.ppt,.md,.csv"
                className="hidden"
                onChange={handleUpload}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={!selectedKb || uploading}
                className="w-full btn-secondary gap-2"
              >
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {uploading ? '上传中...' : '上传课件'}
              </button>
              <p className="text-xs text-gray-400 mt-1">支持 PDF、PPTX、DOCX、TXT、MD</p>
            </div>

            {uploadedFiles.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">已上传文件</h3>
                <ul className="space-y-1.5">
                  {uploadedFiles.map((name, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-gray-600 truncate">
                      <File className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                      <span className="truncate">{name}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {kbsLoading && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
              </div>
            )}
          </div>

          {/* Right Panel */}
          <div className="flex-1 flex flex-col bg-white">
            {/* Mode Toggle + Quiz Generator Button */}
            <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-2">
              <button
                onClick={() => setMode('chat')}
                className={clsx(
                  'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  mode === 'chat' ? 'bg-blue-50 text-blue-700' : 'text-gray-500 hover:text-gray-700'
                )}
              >
                问答模式
              </button>
              <button
                onClick={() => setMode('quiz')}
                className={clsx(
                  'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  mode === 'quiz' ? 'bg-purple-50 text-purple-700' : 'text-gray-500 hover:text-gray-700'
                )}
              >
                测验模式
              </button>
            </div>

            {error && (
              <div className="mx-4 mt-3 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                <span className="flex-1">{error}</span>
                <button onClick={() => setError('')}><X className="h-4 w-4" /></button>
              </div>
            )}

            {/* Chat Mode */}
            {mode === 'chat' && (
              <>
                <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
                  {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center py-16">
                      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 mb-4">
                        <BookOpen className="h-8 w-8 text-blue-500" />
                      </div>
                      <h3 className="text-base font-medium text-gray-900 mb-1">课程问答助手</h3>
                      <p className="text-sm text-gray-500 max-w-sm">
                        选择知识库并上传课件文件，然后向我提问，我会基于知识库内容为你解答
                      </p>
                    </div>
                  )}
                  {messages.map((msg, i) => (
                    <div key={i} className={clsx('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                      <div className={clsx(
                        'max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                        msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'
                      )}>
                        {msg.role === 'assistant' ? (
                          <div className="prose prose-sm max-w-none">
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                          </div>
                        ) : msg.content}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-gray-200/50">
                            <p className="text-xs text-gray-400 mb-1">参考来源:</p>
                            {msg.sources.slice(0, 2).map((s, j) => (
                              <p key={j} className="text-xs text-gray-500 truncate">{s.content?.slice(0, 80)}...</p>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-2xl px-4 py-3">
                        <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
                <div className="border-t border-gray-200 p-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                      placeholder="输入你的问题..."
                      className="input-field flex-1"
                      disabled={loading || !selectedKb}
                    />
                    <button onClick={handleSend} disabled={loading || !input.trim() || !selectedKb} className="btn-primary gap-1.5 shrink-0">
                      <Send className="h-4 w-4" />
                      发送
                    </button>
                  </div>
                </div>
              </>
            )}

            {/* Quiz Mode */}
            {mode === 'quiz' && (
              <div className="flex-1 overflow-y-auto p-4">
                {quizQuestions.length === 0 ? (
                  <div className="max-w-lg mx-auto space-y-6 py-8">
                    <div className="flex flex-col items-center text-center mb-6">
                      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-50 mb-4">
                        <ClipboardCheck className="h-8 w-8 text-purple-500" />
                      </div>
                      <h3 className="text-base font-medium text-gray-900 mb-1">生成测验</h3>
                      <p className="text-sm text-gray-500">配置参数后点击生成，基于知识库内容自动出题</p>
                    </div>

                    <div className="rounded-xl border border-gray-200 bg-white p-5 space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">测验主题</label>
                        <input
                          type="text"
                          value={quizTopic}
                          onChange={(e) => setQuizTopic(e.target.value)}
                          placeholder="例如：数据类型、函数基础（留空则覆盖全部内容）"
                          className="input-field"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">题目数量</label>
                        <select
                          value={quizNumQuestions}
                          onChange={(e) => setQuizNumQuestions(parseInt(e.target.value))}
                          className="input-field"
                        >
                          <option value={3}>3题</option>
                          <option value={5}>5题</option>
                          <option value={8}>8题</option>
                          <option value={10}>10题</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">难度等级</label>
                        <div className="flex gap-2">
                          {[
                            { value: 'easy', label: '简单', desc: '记忆与理解' },
                            { value: 'medium', label: '中等', desc: '应用与分析' },
                            { value: 'hard', label: '困难', desc: '评价与创造' },
                          ].map((d) => (
                            <button
                              key={d.value}
                              onClick={() => setQuizDifficulty(d.value)}
                              className={clsx(
                                'flex-1 rounded-lg border px-3 py-2 text-center transition-colors',
                                quizDifficulty === d.value
                                  ? 'border-purple-300 bg-purple-50 text-purple-700'
                                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
                              )}
                            >
                              <p className="text-sm font-medium">{d.label}</p>
                              <p className="text-xs opacity-70">{d.desc}</p>
                            </button>
                          ))}
                        </div>
                      </div>
                      <button
                        onClick={handleGenerateQuiz}
                        disabled={generatingQuiz || !selectedKb}
                        className="btn-primary w-full gap-2"
                      >
                        {generatingQuiz ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                        {generatingQuiz ? '正在生成...' : '生成测验'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-5 max-w-2xl mx-auto">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-gray-700">测验题目</h3>
                      <button
                        onClick={() => { setQuizQuestions([]); setQuizSubmitted(false); setQuizEvaluations({}); setQuizAnswers({}) }}
                        className="text-xs text-gray-500 hover:text-gray-700"
                      >
                        重新生成
                      </button>
                    </div>
                    {quizQuestions.map((q, i) => {
                      const evalResult = quizSubmitted ? quizEvaluations[q.id] : null
                      return (
                        <div key={q.id} className="rounded-xl border border-gray-200 bg-white p-5">
                          <div className="flex items-start gap-2 mb-3">
                            <span className="text-sm font-bold text-gray-400">{i + 1}.</span>
                            <div className="flex-1">
                              <h4 className="text-sm font-medium text-gray-900">{q.question_text}</h4>
                              <div className="flex gap-2 mt-1">
                                <span className="text-xs text-gray-400">难度: {q.difficulty}</span>
                                <span className="text-xs text-gray-400">Bloom Level {q.bloom_level}</span>
                              </div>
                            </div>
                          </div>
                          {(q.type === 'multiple_choice' || q.type === 'true_false') && q.options && q.options.length > 0 ? (
                            <div className="space-y-2">
                              {q.options.map((opt, j) => {
                                const isSelected = quizAnswers[q.id] === opt
                                const isCorrect = quizSubmitted && evalResult?.correct_answer === opt
                                const isWrong = quizSubmitted && isSelected && evalResult?.correct_answer !== opt
                                return (
                                  <button
                                    key={j}
                                    onClick={() => !quizSubmitted && setQuizAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                                    disabled={quizSubmitted}
                                    className={clsx(
                                      'w-full text-left rounded-lg border px-4 py-2.5 text-sm transition-colors',
                                      isCorrect && 'border-green-300 bg-green-50 text-green-800',
                                      isWrong && 'border-red-300 bg-red-50 text-red-800',
                                      !isCorrect && !isWrong && isSelected && 'border-blue-300 bg-blue-50 text-blue-700',
                                      !isCorrect && !isWrong && !isSelected && 'border-gray-200 hover:border-gray-300 text-gray-700'
                                    )}
                                  >
                                    <span className="font-medium mr-2">{String.fromCharCode(65 + j)}.</span>
                                    {opt}
                                  </button>
                                )
                              })}
                            </div>
                          ) : (
                            <textarea
                              value={quizAnswers[q.id] || ''}
                              onChange={(e) => setQuizAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                              placeholder="输入你的答案..."
                              rows={3}
                              disabled={quizSubmitted}
                              className="input-field resize-none"
                            />
                          )}
                          {quizSubmitted && evalResult && (
                            <div className="mt-3 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
                              <p className="font-medium mb-1">评分: {evalResult.score}分</p>
                              <p>{evalResult.feedback}</p>
                              {evalResult.correct_answer && (
                                <p className="mt-1 text-xs text-blue-600">正确答案: {evalResult.correct_answer}</p>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                    {!quizSubmitted ? (
                      <button
                        onClick={handleSubmitQuiz}
                        disabled={loading}
                        className="btn-primary w-full"
                      >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : '提交答案'}
                      </button>
                    ) : (
                      <div className="rounded-xl border border-gray-200 bg-white p-5 text-center">
                        <p className="text-2xl font-bold text-purple-600">
                          {Object.values(quizEvaluations).filter((e) => e.score >= 60).length} / {quizQuestions.length}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">及格题数（60分以上）</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
