'use client'

import { useState } from 'react'
import Sidebar from '@/components/Sidebar'
import { Route, Plus, Loader2, X, Clock, CheckCircle, Circle, Play, ChevronDown, ChevronUp, Target, Flame, BookOpen, Star, Timer } from 'lucide-react'
import clsx from 'clsx'
import { createPlan, getProgress, updateProgress, recordSession, getRecommendations } from '@/lib/api'

interface Task {
  id: string
  title: string
  description: string
  estimated_hours: number
  status: string
}

interface Milestone {
  id: string
  title: string
  description: string
  order: number
  status: string
  tasks: Task[]
}

interface PlanProgress {
  plan_id: string
  goal: string
  completion_percentage: number
  streak: number
  total_study_hours: number
  milestones: Milestone[]
}

interface Recommendation {
  type: string
  title: string
  description: string
  priority: string
  action: string
}

export default function LearningPage() {
  const [planId, setPlanId] = useState<string>('')
  const [plan, setPlan] = useState<PlanProgress | null>(null)
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [expandedMilestone, setExpandedMilestone] = useState<string | null>(null)
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)

  // Create form
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [goal, setGoal] = useState('')
  const [currentLevel, setCurrentLevel] = useState('')
  const [timeframe, setTimeframe] = useState('')
  const [creating, setCreating] = useState(false)

  // Session recording
  const [showSessionModal, setShowSessionModal] = useState(false)
  const [sessionTask, setSessionTask] = useState<{ milestoneId: string; taskId: string } | null>(null)
  const [sessionDuration, setSessionDuration] = useState('')
  const [sessionNotes, setSessionNotes] = useState('')
  const [recordingSession, setRecordingSession] = useState(false)

  async function handleCreatePlan() {
    if (!goal.trim() || !currentLevel.trim() || !timeframe.trim()) return
    setCreating(true)
    setError('')
    try {
      const data = await createPlan(goal, currentLevel, timeframe)
      setPlanId(data.plan_id)
      setShowCreateForm(false)
      await loadProgress(data.plan_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建计划失败')
    } finally {
      setCreating(false)
    }
  }

  async function loadProgress(pid: string) {
    setLoading(true)
    setError('')
    try {
      const data = await getProgress(pid)
      setPlan({
        plan_id: data.plan_id,
        goal: data.goal,
        completion_percentage: data.completion_percentage,
        streak: data.streak,
        total_study_hours: data.total_study_hours,
        milestones: data.milestones,
      })
      // Load recommendations
      try {
        const recs = await getRecommendations(pid)
        setRecommendations(recs.recommendations)
      } catch {
        setRecommendations([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载计划失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpdateTaskStatus(milestoneId: string, taskId: string, currentStatus: string) {
    if (!planId) return
    const newStatus = currentStatus === 'completed' ? 'not_started' : currentStatus === 'in_progress' ? 'completed' : 'in_progress'
    try {
      await updateProgress(planId, milestoneId, taskId, newStatus)
      setPlan((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          milestones: prev.milestones.map((m) =>
            m.id === milestoneId
              ? {
                  ...m,
                  tasks: m.tasks.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t)),
                  status: newStatus === 'completed' && m.tasks.every((t) => t.id === taskId || t.status === 'completed')
                    ? 'completed'
                    : m.tasks.some((t) => t.id === taskId ? newStatus === 'in_progress' || newStatus === 'completed' : t.status === 'in_progress' || t.status === 'completed')
                    ? 'in_progress'
                    : 'not_started',
                }
              : m
          ),
          completion_percentage: Math.round(
            (prev.milestones.reduce((acc, m) => {
              const completedTasks = m.tasks.filter((t) =>
                t.id === taskId && m.id === milestoneId
                  ? newStatus === 'completed'
                  : t.status === 'completed'
              ).length
              return acc + completedTasks
            }, 0) /
              Math.max(1, prev.milestones.reduce((acc, m) => acc + m.tasks.length, 0))) *
              100
          ),
        }
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新状态失败')
    }
  }

  async function handleRecordSession() {
    if (!planId || !sessionTask || !sessionDuration) return
    setRecordingSession(true)
    setError('')
    try {
      await recordSession(planId, sessionTask.milestoneId, sessionTask.taskId, parseFloat(sessionDuration), sessionNotes || undefined)
      setShowSessionModal(false)
      setSessionTask(null)
      setSessionDuration('')
      setSessionNotes('')
      await loadProgress(planId)
    } catch (err) {
      setError(err instanceof Error ? err.message : '记录学习时间失败')
    } finally {
      setRecordingSession(false)
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-emerald-500" />
      case 'in_progress':
        return <Play className="h-5 w-5 text-orange-500" />
      default:
        return <Circle className="h-5 w-5 text-gray-300" />
    }
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case 'completed':
        return '已完成'
      case 'in_progress':
        return '进行中'
      default:
        return '未开始'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="lg:pl-60">
        {/* Header */}
        <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="flex h-16 items-center gap-4 px-4 sm:px-6 lg:px-8 pl-16 lg:pl-8">
            <Route className="h-5 w-5 text-orange-600" />
            <h1 className="text-lg font-semibold text-gray-900">学习路径规划</h1>
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Error */}
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              <span className="flex-1">{error}</span>
              <button onClick={() => setError('')}><X className="h-4 w-4" /></button>
            </div>
          )}

          {/* Create Plan Form */}
          {!plan && !loading && (
            <div className="max-w-2xl">
              {!showCreateForm ? (
                <div className="flex flex-col items-center justify-center text-center py-16">
                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-50 mb-4">
                    <Route className="h-8 w-8 text-orange-500" />
                  </div>
                  <h3 className="text-base font-medium text-gray-900 mb-1">创建你的学习计划</h3>
                  <p className="text-sm text-gray-500 max-w-sm mb-6">
                    设定学习目标，AI将为你生成个性化的学习路径和里程碑
                  </p>
                  <button onClick={() => setShowCreateForm(true)} className="btn-primary gap-2">
                    <Plus className="h-4 w-4" />
                    创建新计划
                  </button>
                </div>
              ) : (
                <div className="rounded-xl border border-gray-200 bg-white p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">创建学习计划</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">学习目标</label>
                      <input
                        type="text"
                        value={goal}
                        onChange={(e) => setGoal(e.target.value)}
                        placeholder="例如：掌握机器学习基础"
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">当前水平</label>
                      <input
                        type="text"
                        value={currentLevel}
                        onChange={(e) => setCurrentLevel(e.target.value)}
                        placeholder="例如：有Python基础，无机器学习经验"
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">时间范围</label>
                      <input
                        type="text"
                        value={timeframe}
                        onChange={(e) => setTimeframe(e.target.value)}
                        placeholder="例如：3个月"
                        className="input-field"
                      />
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                      <button onClick={() => setShowCreateForm(false)} className="btn-secondary">取消</button>
                      <button onClick={handleCreatePlan} disabled={creating || !goal.trim() || !currentLevel.trim() || !timeframe.trim()} className="btn-primary gap-2">
                        {creating && <Loader2 className="h-4 w-4 animate-spin" />}
                        生成计划
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center gap-2 py-16">
              <Loader2 className="h-5 w-5 animate-spin text-orange-500" />
              <span className="text-sm text-gray-600">正在加载学习计划...</span>
            </div>
          )}

          {/* Plan Content */}
          {plan && !loading && (
            <div className="flex flex-col lg:flex-row gap-6">
              {/* Main Content */}
              <div className="flex-1 min-w-0">
                {/* Goal */}
                <div className="mb-6">
                  <h2 className="text-lg font-semibold text-gray-900">{plan.goal}</h2>
                  <div className="mt-2 flex items-center gap-3">
                    <div className="flex-1 h-2 rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full bg-orange-500 transition-all"
                        style={{ width: `${plan.completion_percentage}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-600">{plan.completion_percentage}%</span>
                  </div>
                </div>

                {/* Timeline */}
                <div className="space-y-0">
                  {plan.milestones.map((milestone, idx) => {
                    const isExpanded = expandedMilestone === milestone.id
                    const isLast = idx === plan.milestones.length - 1
                    return (
                      <div key={milestone.id} className="relative flex gap-4">
                        {/* Timeline line */}
                        <div className="flex flex-col items-center">
                          <button
                            onClick={() => handleUpdateTaskStatus(milestone.id, milestone.tasks[0]?.id, milestone.status)}
                            className="relative z-10 mt-1"
                          >
                            {getStatusIcon(milestone.status)}
                          </button>
                          {!isLast && (
                            <div className={clsx(
                              'w-0.5 flex-1 min-h-[40px]',
                              milestone.status === 'completed' ? 'bg-emerald-300' : 'bg-gray-200'
                            )} />
                          )}
                        </div>

                        {/* Content */}
                        <div className={clsx('flex-1 pb-6', !isLast && 'pb-8')}>
                          <button
                            onClick={() => setExpandedMilestone(isExpanded ? null : milestone.id)}
                            className="w-full text-left"
                          >
                            <div className="flex items-center justify-between rounded-lg hover:bg-gray-50 -mx-2 px-2 py-1.5 transition-colors">
                              <div>
                                <h3 className="text-sm font-semibold text-gray-900">{milestone.title}</h3>
                                <p className="text-xs text-gray-500 mt-0.5">{milestone.description}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className={clsx(
                                  'inline-flex rounded-full px-2 py-0.5 text-xs font-medium',
                                  milestone.status === 'completed' ? 'bg-emerald-50 text-emerald-700' :
                                  milestone.status === 'in_progress' ? 'bg-orange-50 text-orange-700' : 'bg-gray-100 text-gray-500'
                                )}>
                                  {getStatusLabel(milestone.status)}
                                </span>
                                {isExpanded ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
                              </div>
                            </div>
                          </button>

                          {/* Expanded Tasks */}
                          {isExpanded && (
                            <div className="mt-3 space-y-2 ml-2">
                              {milestone.tasks.map((task) => (
                                <div
                                  key={task.id}
                                  className={clsx(
                                    'flex items-start gap-3 rounded-lg border p-3 transition-colors',
                                    task.status === 'completed'
                                      ? 'border-emerald-200 bg-emerald-50/50'
                                      : 'border-gray-200 bg-white'
                                  )}
                                >
                                  <button
                                    onClick={() => handleUpdateTaskStatus(milestone.id, task.id, task.status)}
                                    className="mt-0.5 shrink-0"
                                  >
                                    {task.status === 'completed' ? (
                                      <CheckCircle className="h-4 w-4 text-emerald-500" />
                                    ) : task.status === 'in_progress' ? (
                                      <Play className="h-4 w-4 text-orange-500" />
                                    ) : (
                                      <Circle className="h-4 w-4 text-gray-300 hover:text-gray-400" />
                                    )}
                                  </button>
                                  <div className="flex-1 min-w-0">
                                    <p className={clsx(
                                      'text-sm font-medium',
                                      task.status === 'completed' ? 'text-gray-500 line-through' : 'text-gray-900'
                                    )}>
                                      {task.title}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-0.5">{task.description}</p>
                                    <div className="flex items-center gap-3 mt-2">
                                      <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                                        <Clock className="h-3 w-3" />
                                        {task.estimated_hours}小时
                                      </span>
                                      {task.status !== 'completed' && (
                                        <button
                                          onClick={() => {
                                            setSessionTask({ milestoneId: milestone.id, taskId: task.id })
                                            setShowSessionModal(true)
                                          }}
                                          className="inline-flex items-center gap-1 text-xs text-orange-600 hover:text-orange-700"
                                        >
                                          <Timer className="h-3 w-3" />
                                          记录学习
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Recommendations */}
                {recommendations.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">学习建议</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {recommendations.map((rec, i) => (
                        <div key={i} className="rounded-xl border border-gray-200 bg-white p-4 card-hover">
                          <div className="flex items-start gap-2 mb-2">
                            <Star className={clsx(
                              'h-4 w-4 shrink-0 mt-0.5',
                              rec.priority === 'high' ? 'text-red-500' :
                              rec.priority === 'medium' ? 'text-yellow-500' : 'text-gray-400'
                            )} />
                            <h4 className="text-sm font-medium text-gray-900">{rec.title}</h4>
                          </div>
                          <p className="text-xs text-gray-500 ml-6">{rec.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Sidebar - Progress */}
              <div className="w-full lg:w-72 shrink-0 space-y-4">
                <div className="rounded-xl border border-gray-200 bg-white p-5">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">学习进度</h3>
                  <div className="space-y-4">
                    <div className="text-center">
                      <p className="text-3xl font-bold text-orange-600">{plan.completion_percentage}%</p>
                      <p className="text-xs text-gray-400 mt-1">完成进度</p>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="text-center rounded-lg bg-orange-50 p-3">
                        <Flame className="h-5 w-5 text-orange-500 mx-auto mb-1" />
                        <p className="text-lg font-bold text-orange-700">{plan.streak}</p>
                        <p className="text-xs text-orange-600">连续天数</p>
                      </div>
                      <div className="text-center rounded-lg bg-primary-50 p-3">
                        <BookOpen className="h-5 w-5 text-primary-500 mx-auto mb-1" />
                        <p className="text-lg font-bold text-primary-700">{plan.total_study_hours}</p>
                        <p className="text-xs text-primary-600">学习小时</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400 mb-2">里程碑完成</p>
                      <div className="flex items-center gap-1">
                        {plan.milestones.map((m) => (
                          <div
                            key={m.id}
                            className={clsx(
                              'h-2 flex-1 rounded-full',
                              m.status === 'completed' ? 'bg-emerald-400' :
                              m.status === 'in_progress' ? 'bg-orange-400' : 'bg-gray-200'
                            )}
                          />
                        ))}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {plan.milestones.filter((m) => m.status === 'completed').length} / {plan.milestones.length} 已完成
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Session Recording Modal */}
      {showSessionModal && sessionTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">记录学习时间</h2>
              <button onClick={() => { setShowSessionModal(false); setSessionTask(null) }} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">学习时长（小时）</label>
                <input
                  type="number"
                  value={sessionDuration}
                  onChange={(e) => setSessionDuration(e.target.value)}
                  placeholder="例如：1.5"
                  step="0.5"
                  min="0.5"
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">学习笔记（可选）</label>
                <textarea
                  value={sessionNotes}
                  onChange={(e) => setSessionNotes(e.target.value)}
                  placeholder="记录今天的学习收获..."
                  rows={3}
                  className="input-field resize-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button onClick={() => { setShowSessionModal(false); setSessionTask(null) }} className="btn-secondary">取消</button>
                <button onClick={handleRecordSession} disabled={recordingSession || !sessionDuration} className="btn-primary gap-2">
                  {recordingSession && <Loader2 className="h-4 w-4 animate-spin" />}
                  保存记录
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
