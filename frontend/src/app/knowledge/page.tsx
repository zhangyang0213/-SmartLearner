'use client'

import { useState, useEffect, useRef } from 'react'
import Sidebar from '@/components/Sidebar'
import { Database, Plus, Search, Upload, File, Trash2, X, Loader2, FileText, Hash, ChevronDown, MessageSquare } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'
import { createKB, listKBs, getKB, deleteKB, searchKB, nlQuery, uploadFiles } from '@/lib/api'

interface KBItem {
  kb_id: string
  name: string
  description: string
  doc_count: number
  chunk_count: number
  created_at: string
}

interface KBDetail {
  kb_id: string
  name: string
  description: string
  doc_count: number
  chunk_count: number
  docs: Array<{ doc_id: string; filename: string; chunk_count: number; uploaded_at: string }>
  created_at: string
}

interface SearchResult {
  content: string
  metadata: Record<string, unknown>
  score: number
  source: string
}

type SearchType = 'semantic' | 'keyword' | 'hybrid'

export default function KnowledgePage() {
  const [kbs, setKbs] = useState<KBItem[]>([])
  const [selectedKbId, setSelectedKbId] = useState<string>('')
  const [kbDetail, setKbDetail] = useState<KBDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchType, setSearchType] = useState<SearchType>('semantic')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [useNLQuery, setUseNLQuery] = useState(false)
  const [interpretedQuery, setInterpretedQuery] = useState('')

  // Create KB modal
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newKbName, setNewKbName] = useState('')
  const [newKbDesc, setNewKbDesc] = useState('')
  const [creating, setCreating] = useState(false)

  // Upload
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Error
  const [error, setError] = useState('')

  useEffect(() => {
    loadKBs()
  }, [])

  useEffect(() => {
    if (selectedKbId) loadKBDetail()
  }, [selectedKbId])

  async function loadKBs() {
    try {
      setLoading(true)
      const data = await listKBs()
      setKbs(data.knowledge_bases || [])
      if (data.knowledge_bases?.length > 0 && !selectedKbId) {
        setSelectedKbId(data.knowledge_bases[0].kb_id)
      }
    } catch {
      setKbs([])
    } finally {
      setLoading(false)
    }
  }

  async function loadKBDetail() {
    if (!selectedKbId) return
    try {
      setDetailLoading(true)
      const data = await getKB(selectedKbId)
      setKbDetail(data)
    } catch {
      setKbDetail(null)
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleCreateKB() {
    if (!newKbName.trim()) return
    setCreating(true)
    setError('')
    try {
      const data = await createKB(newKbName, newKbDesc)
      setKbs((prev) => [...prev, { kb_id: data.kb_id, name: data.name, description: data.description, doc_count: 0, chunk_count: 0, created_at: new Date().toISOString() }])
      setSelectedKbId(data.kb_id)
      setShowCreateModal(false)
      setNewKbName('')
      setNewKbDesc('')
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建知识库失败')
    } finally {
      setCreating(false)
    }
  }

  async function handleDeleteKB(kbId: string) {
    if (!confirm('确定要删除此知识库吗？此操作不可撤销。')) return
    try {
      await deleteKB(kbId)
      setKbs((prev) => prev.filter((kb) => kb.kb_id !== kbId))
      if (selectedKbId === kbId) {
        setSelectedKbId(kbs.find((kb) => kb.kb_id !== kbId)?.kb_id || '')
        setKbDetail(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim() || !selectedKbId) return
    setSearchLoading(true)
    setError('')
    setSearchResults([])
    setInterpretedQuery('')

    try {
      if (useNLQuery) {
        const data = await nlQuery(selectedKbId, searchQuery)
        setSearchResults(data.results)
        setInterpretedQuery(data.interpreted_query)
      } else {
        const data = await searchKB(selectedKbId, searchQuery, searchType)
        setSearchResults(data.results)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败')
    } finally {
      setSearchLoading(false)
    }
  }

  async function handleUploadDocs() {
    const files = fileInputRef.current?.files
    if (!files?.length || !selectedKbId) return
    setUploading(true)
    setError('')
    try {
      await uploadFiles(selectedKbId, Array.from(files))
      if (fileInputRef.current) fileInputRef.current.value = ''
      await loadKBDetail()
      await loadKBs()
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
    }
  }

  const selectedKb = kbs.find((kb) => kb.kb_id === selectedKbId)

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="lg:pl-60">
        {/* Header */}
        <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="flex h-16 items-center gap-4 px-4 sm:px-6 lg:px-8 pl-16 lg:pl-8">
            <Database className="h-5 w-5 text-emerald-600" />
            <h1 className="text-lg font-semibold text-gray-900">知识库管家</h1>
          </div>
        </header>

        <div className="flex flex-col lg:flex-row h-[calc(100vh-4rem)]">
          {/* Left Sidebar - KB List */}
          <div className="w-full lg:w-72 shrink-0 border-b lg:border-b-0 lg:border-r border-gray-200 bg-white flex flex-col">
            <div className="p-4 border-b border-gray-100">
              <button
                onClick={() => setShowCreateModal(true)}
                className="w-full btn-primary gap-2"
              >
                <Plus className="h-4 w-4" />
                新建知识库
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                </div>
              ) : kbs.length === 0 ? (
                <div className="p-4 text-center text-sm text-gray-400 py-8">
                  暂无知识库，点击上方按钮创建
                </div>
              ) : (
                <div className="p-2 space-y-1">
                  {kbs.map((kb) => (
                    <button
                      key={kb.kb_id}
                      onClick={() => setSelectedKbId(kb.kb_id)}
                      className={clsx(
                        'w-full text-left rounded-lg px-3 py-2.5 transition-colors group',
                        selectedKbId === kb.kb_id
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'text-gray-700 hover:bg-gray-50'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium truncate">{kb.name}</span>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteKB(kb.kb_id) }}
                          className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-500 transition-all"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-gray-400">{kb.doc_count} 文档</span>
                        <span className="text-xs text-gray-400">{kb.chunk_count} 片段</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Main Area */}
          <div className="flex-1 overflow-y-auto">
            {/* Error */}
            {error && (
              <div className="m-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                <span className="flex-1">{error}</span>
                <button onClick={() => setError('')}><X className="h-4 w-4" /></button>
              </div>
            )}

            {selectedKbId ? (
              <div className="p-4 sm:p-6 lg:p-8 space-y-6">
                {/* KB Info */}
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">{selectedKb?.name}</h2>
                    <p className="text-sm text-gray-500 mt-0.5">{selectedKb?.description}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-center">
                      <p className="text-lg font-bold text-emerald-600">{kbDetail?.doc_count || selectedKb?.doc_count || 0}</p>
                      <p className="text-xs text-gray-400">文档</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold text-emerald-600">{kbDetail?.chunk_count || selectedKb?.chunk_count || 0}</p>
                      <p className="text-xs text-gray-400">片段</p>
                    </div>
                  </div>
                </div>

                {/* Upload */}
                <div className="flex items-center gap-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.txt,.doc,.docx,.md"
                    className="hidden"
                    onChange={handleUploadDocs}
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="btn-secondary gap-2"
                  >
                    {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                    {uploading ? '上传中...' : '上传文档'}
                  </button>
                </div>

                {/* Search Bar */}
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="搜索知识库..."
                        className="input-field pl-9"
                      />
                    </div>
                    <div className="relative">
                      <select
                        value={searchType}
                        onChange={(e) => setSearchType(e.target.value as SearchType)}
                        className="input-field appearance-none pr-8 text-sm"
                        disabled={useNLQuery}
                      >
                        <option value="semantic">语义搜索</option>
                        <option value="keyword">关键词搜索</option>
                        <option value="hybrid">混合搜索</option>
                      </select>
                      <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                    </div>
                    <button
                      onClick={handleSearch}
                      disabled={searchLoading || !searchQuery.trim()}
                      className="btn-primary gap-1.5"
                    >
                      {searchLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                      搜索
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setUseNLQuery(!useNLQuery)}
                      className={clsx(
                        'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors',
                        useNLQuery
                          ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
                          : 'text-gray-500 hover:text-gray-700'
                      )}
                    >
                      <MessageSquare className="h-3.5 w-3.5" />
                      自然语言查询
                    </button>
                  </div>
                  {interpretedQuery && (
                    <p className="text-xs text-gray-500">
                      解析后的查询：<span className="font-medium text-emerald-600">{interpretedQuery}</span>
                    </p>
                  )}
                </div>

                {/* Search Results */}
                {searchResults.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-gray-700">搜索结果</h3>
                    {searchResults.map((result, i) => (
                      <div key={i} className="rounded-xl border border-gray-200 bg-white p-4">
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <FileText className="h-3.5 w-3.5" />
                            <span>{result.source}</span>
                          </div>
                          <div className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                            <Hash className="h-3 w-3" />
                            {Math.round(result.score * 100)}%
                          </div>
                        </div>
                        <p className="text-sm text-gray-700 leading-relaxed">{result.content}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* KB Documents */}
                {kbDetail && kbDetail.docs.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-gray-700">文档列表</h3>
                    <div className="space-y-2">
                      {kbDetail.docs.map((doc) => (
                        <div key={doc.doc_id} className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3">
                          <File className="h-4 w-4 text-gray-400 shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                            <p className="text-xs text-gray-400">{doc.chunk_count} 片段</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {detailLoading && (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center py-16">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50 mb-4">
                  <Database className="h-8 w-8 text-emerald-500" />
                </div>
                <h3 className="text-base font-medium text-gray-900 mb-1">选择或创建知识库</h3>
                <p className="text-sm text-gray-500 max-w-sm">
                  从左侧选择一个知识库，或创建新的知识库开始管理你的知识
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create KB Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">新建知识库</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
                <input
                  type="text"
                  value={newKbName}
                  onChange={(e) => setNewKbName(e.target.value)}
                  placeholder="输入知识库名称"
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={newKbDesc}
                  onChange={(e) => setNewKbDesc(e.target.value)}
                  placeholder="简要描述知识库用途"
                  rows={3}
                  className="input-field resize-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button onClick={() => setShowCreateModal(false)} className="btn-secondary">取消</button>
                <button onClick={handleCreateKB} disabled={creating || !newKbName.trim()} className="btn-primary gap-2">
                  {creating && <Loader2 className="h-4 w-4 animate-spin" />}
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
