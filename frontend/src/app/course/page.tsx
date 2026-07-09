'use client'

import { useState, useRef, useEffect } from 'react'
import Sidebar from '@/components/Sidebar'
import { BookOpen, Upload, Send, FileUp, ChevronDown, ClipboardCheck, Loader2, X, File } from 'lucide-react'
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
  question: string
  options: string[]
  answer: number
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
  const [quizAnswers, setQuizAnswers] = useState<Record<string, number>>({})
  const [quizId, setQuizId] = useState<string>('')
  const [quizSubmitted, setQuizSubmitted] = useState(false)
  const [quizResults, setQuizResults] = useState<Array<{ question_id: string; correct: boolean; correct_answer: number; explanation: string }> | null>(null)
  const [error, setError] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [kbsLoading, setKbsLoading] = useState(true)

  useEffect(() => {
    loadKBs()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
      const data = await askQuestion(selectedKb, userMessage, messages.slice(-6))
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.answer, sources: data.sources },
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerateQuiz() {
    if (!selectedKb) return
    setLoading(true)
    setError('')
    setQuizSubmitted(false)
    setQuizResults(null)
    setQuizAnswers({})

    try {
      const data = await generateQuiz(selectedKb)
      setQuizId(data.quiz_id)
      setQuizQuestions(data.questions)
      setMode('quiz')
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成测验失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmitQuiz() {
    if (!quizId) return
    setLoading(true)
    setError('')

    try {
      const data = await evaluateQuiz(quizId, quizAnswers)
      setQuizResults(data.results)
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
        {/* Header */}
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
                  <option key={kb.kb_id} value={kb.kb_id}>
                    {kb.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            </div>

            {/* Upload */}
            <div className="mb-4">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.doc,.docx,.md"
                className="hidden"
                onChange={handleUpload}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={!selectedKb || uploading}
                className="w-full btn-secondary gap-2"
              >
                {uploading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="h-4 w-4" />
                )}
                {uploading ? '上传中...' : '上传文件'}
              </button>
            </div>

            {/* Uploaded files */}
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

          {/* Right Panel - Chat / Quiz */}
          <div className="flex-1 flex flex-col bg-white">
            {/* Mode Toggle */}
            <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-2">
              <button
                onClick={() => setMode('chat')}
                className={clsx(
                  'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  mode === 'chat'
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                )}
              >
                问答模式
              </button>
              <button
                onClick={() => setMode('quiz')}
                className={clsx(
                  'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  mode === 'quiz'
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                )}
              >
                测验模式
              </button>
              {mode === 'chat' && (
                <button
                  onClick={handleGenerateQuiz}
                  disabled={loading || !selectedKb}
                  className="ml-auto btn-secondary gap-1.5 text-xs"
                >
                  <ClipboardCheck className="h-3.5 w-3.5" />
                  生成测验
                </button>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="mx-4 mt-3 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                <span className="flex-1">{error}</span>
                <button onClick={() => setError('')}>
                  <X className="h-4 w-4" />
                </button>
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
                        选择知识库并上传课程文件，然后向我提问，我会基于知识库内容为你解答
                      </p>
                    </div>
                  )}
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      className={clsx(
                        'flex',
                        msg.role === 'user' ? 'justify-end' : 'justify-start'
                      )}
                    >
                      <div
                        className={clsx(
                          'max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                          msg.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        )}
                      >
                        {msg.role === 'assistant' ? (
                          <div className="prose prose-sm max-w-none">
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                          </div>
                        ) : (
                          msg.content
                        )}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-gray-200/50">
                            <p className="text-xs text-gray-400 mb-1">参考来源:</p>
                            {msg.sources.slice(0, 2).map((s, j) => (
                              <p key={j} className="text-xs text-gray-500 truncate">
                                {s.content.slice(0, 80)}...
                              </p>
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

                {/* Input */}
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
                    <button
                      onClick={handleSend}
                      disabled={loading || !input.trim() || !selectedKb}
                      className="btn-primary gap-1.5 shrink-0"
                    >
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
                  <div className="flex flex-col items-center justify-center h-full text-center py-16">
                    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-50 mb-4">
                      <ClipboardCheck className="h-8 w-8 text-purple-500" />
                    </div>
                    <h3 className="text-base font-medium text-gray-900 mb-1">测验模式</h3>
                    <p className="text-sm text-gray-500 max-w-sm">
                      点击&quot;生成测验&quot;按钮，基于知识库内容自动生成测验题目
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6 max-w-2xl mx-auto">
                    {quizQuestions.map((q, i) => (
                      <div key={q.id} className="rounded-xl border border-gray-200 bg-white p-5">
                        <h4 className="text-sm font-medium text-gray-900 mb-3">
                          {i + 1}. {q.question}
                        </h4>
                        <div className="space-y-2">
                          {q.options.map((opt, j) => {
                            const isSelected = quizAnswers[q.id] === j
                            const isCorrect = quizSubmitted && quizResults?.find((r) => r.question_id === q.id)?.correct_answer === j
                            const isWrong = quizSubmitted && isSelected && !quizResults?.find((r) => r.question_id === q.id)?.correct
                            return (
                              <button
                                key={j}
                                onClick={() => !quizSubmitted && setQuizAnswers((prev) => ({ ...prev, [q.id]: j }))}
                                disabled={quizSubmitted}
                                className={clsx(
                                  'w-full text-left rounded-lg border px-4 py-2.5 text-sm transition-colors',
                                  isCorrect && 'border-green-300 bg-green-50 text-green-800',
                                  isWrong && 'border-red-300 bg-red-50 text-red-800',
                                  !isCorrect && !isWrong && isSelected && 'border-primary-300 bg-primary-50 text-primary-700',
                                  !isCorrect && !isWrong && !isSelected && 'border-gray-200 hover:border-gray-300 text-gray-700'
                                )}
                              >
                                <span className="font-medium mr-2">{String.fromCharCode(65 + j)}.</span>
                                {opt}
                              </button>
                            )
                          })}
                        </div>
                        {quizSubmitted && quizResults?.find((r) => r.question_id === q.id) && (
                          <div className="mt-3 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
                            {quizResults.find((r) => r.question_id === q.id)?.explanation}
                          </div>
                        )}
                      </div>
                    ))}
                    {!quizSubmitted && (
                      <button
                        onClick={handleSubmitQuiz}
                        disabled={loading || Object.keys(quizAnswers).length < quizQuestions.length}
                        className="btn-primary w-full"
                      >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : '提交答案'}
                      </button>
                    )}
                    {quizSubmitted && quizResults && (
                      <div className="rounded-xl border border-gray-200 bg-white p-5 text-center">
                        <p className="text-2xl font-bold text-primary-600">
                          {quizResults.filter((r) => r.correct).length} / {quizQuestions.length}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">正确率</p>
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
