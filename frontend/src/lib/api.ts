const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || error.message || '请求失败')
  }
  return res.json()
}

// ==================== Course QA ====================

export async function uploadFiles(kbId: string, files: File[]) {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  const res = await fetch(`${BASE_URL}/upload/${kbId}`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || '上传失败')
  }
  return res.json()
}

export async function askQuestion(kbId: string, question: string) {
  return request<{ answer: string; sources: Array<{ content: string; source: string; score: number }>; confidence: number }>(
    `/course/ask`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, question }),
    }
  )
}

export async function chat(kbId: string, question: string, history: Array<{ role: string; content: string }> = []) {
  return request<{ answer: string; sources: Array<{ content: string; source: string }> }>(
    `/course/chat`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, question, history }),
    }
  )
}

export async function generateQuiz(kbId: string, topic: string, numQuestions: number = 5, difficulty: string = 'medium') {
  return request<{ title: string; questions: Array<{ id: string; type: string; question_text: string; options: string[]; correct_answer: string; explanation: string; bloom_level: number; difficulty: string }> }>(
    `/course/quiz/generate`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, topic, num_questions: numQuestions, difficulty }),
    }
  )
}

export async function evaluateQuiz(question: Record<string, unknown>, userAnswer: string) {
  return request<{ score: number; feedback: string; correct_answer: string }>(
    `/course/quiz/evaluate`,
    {
      method: 'POST',
      body: JSON.stringify({ question, user_answer: userAnswer }),
    }
  )
}

// ==================== Paper Reader ====================

export async function summarize(kbId: string) {
  return request<Record<string, any>>(
    `/paper/summarize`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId }),
    }
  )
}

export async function quickSummary(kbId: string) {
  return request<{ summary: string }>(
    `/paper/quick-summary`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId }),
    }
  )
}

export async function extractConcepts(kbId: string) {
  return request<{ concepts: Array<Record<string, any>> }>(
    `/paper/concepts`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId }),
    }
  )
}

export async function generateSocratic(kbId: string, focusArea?: string) {
  return request<{ questions: Array<Record<string, any>> }>(
    `/paper/socratic/questions`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, focus_area: focusArea }),
    }
  )
}

export async function evaluateSocratic(kbId: string, question: string, userResponse: string) {
  return request<Record<string, any>>(
    `/paper/socratic/evaluate`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, question, user_response: userResponse }),
    }
  )
}

export async function recommendLiterature(kbId: string, numResults: number = 5) {
  return request<{ recommendations: Array<Record<string, any>> }>(
    `/paper/recommend`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, num_results: numResults }),
    }
  )
}

export async function generateLiteratureMap(kbId: string) {
  return request<Record<string, any>>(
    `/paper/literature-map`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId }),
    }
  )
}

export async function findContradictingViews(kbId: string) {
  return request<{ views: Array<Record<string, any>> }>(
    `/paper/contradicting-views`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId }),
    }
  )
}

export async function generateReadingGuide(kbId: string) {
  return request<Record<string, any>>(
    `/paper/reading-guide`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId }),
    }
  )
}

// ==================== Knowledge Base ====================

export async function createKB(name: string, description: string, category: string = 'general') {
  return request<{ kb_id: string; name: string; description: string; category: string; created_at: string }>(
    `/kb/create`,
    {
      method: 'POST',
      body: JSON.stringify({ name, description, category }),
    }
  )
}

export async function listKBs() {
  return request<{
    knowledge_bases: Array<{
      kb_id: string
      name: string
      description: string
      doc_count: number
      chunk_count: number
      created_at: string
    }>
  }>(`/kb/list`)
}

export async function getKB(kbId: string) {
  return request<{
    kb_id: string
    name: string
    description: string
    doc_count: number
    chunk_count: number
    created_at: string
  }>(`/kb/${kbId}`)
}

export async function deleteKB(kbId: string) {
  return request<{ success: boolean }>(`/kb/${kbId}`, {
    method: 'DELETE',
  })
}

export async function searchKB(kbId: string, query: string, searchType: string = 'semantic', k: number = 5) {
  return request<{
    results: Array<{ content: string; metadata: Record<string, unknown>; score: number; source: string }>
  }>(`/kb/${kbId}/search`, {
    method: 'POST',
    body: JSON.stringify({ query, search_type: searchType, k }),
  })
}

export async function multiKBSearch(kbIds: string[], query: string, k: number = 5) {
  return request<{
    results: Array<{ content: string; metadata: Record<string, unknown>; score: number; source: string; kb_id: string }>
  }>(`/kb/search/multi`, {
    method: 'POST',
    body: JSON.stringify({ kb_ids: kbIds, query, k }),
  })
}

export async function nlQuery(kbId: string, query: string) {
  return request<{
    refined_query: string
    results: Array<{ content: string; metadata: Record<string, unknown>; score: number; source: string }>
    summary: string
  }>(`/kb/${kbId}/nl-query`, {
    method: 'POST',
    body: JSON.stringify({ query }),
  })
}

// ==================== Learning Path ====================

export async function createPlan(goal: string, currentLevel: string, timeframe: string, preferences?: Record<string, unknown>) {
  return request<Record<string, any>>(
    `/learning/plan`,
    {
      method: 'POST',
      body: JSON.stringify({ goal, current_level: currentLevel, timeframe, preferences }),
    }
  )
}

export async function refinePlan(plan: Record<string, any>, feedback: string) {
  return request<Record<string, any>>(
    `/learning/plan/refine`,
    {
      method: 'POST',
      body: JSON.stringify({ plan, feedback }),
    }
  )
}

export async function updateProgress(planId: string, milestoneId: string, taskId: string, status: string, notes: string = '') {
  return request<{ message: string; completion_percentage: number }>(
    `/learning/progress/update`,
    {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId, milestone_id: milestoneId, task_id: taskId, status, notes }),
    }
  )
}

export async function getProgress(planId: string) {
  return request<Record<string, any>>(
    `/learning/progress/${planId}`
  )
}

export async function recordSession(planId: string, durationMinutes: number, topic: string = '', notes: string = '') {
  return request<{ message: string; total_hours: number }>(
    `/learning/study-session`,
    {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId, duration_minutes: durationMinutes, topic, notes }),
    }
  )
}

export async function getStudyStats(planId: string, period: string = 'week') {
  return request<Record<string, any>>(
    `/learning/stats/${planId}?period=${period}`
  )
}

export async function getRecommendations(planId: string) {
  return request<Record<string, any>>(
    `/learning/recommendations/${planId}`
  )
}
