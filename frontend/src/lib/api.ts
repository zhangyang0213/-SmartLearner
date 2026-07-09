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

export async function askQuestion(kbId: string, question: string, history: Array<{ role: string; content: string }> = []) {
  return request<{ answer: string; sources: Array<{ content: string; metadata: Record<string, unknown>; score: number }> }>(
    `/course/ask`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, question, history }),
    }
  )
}

export async function chat(kbId: string, message: string, sessionId?: string) {
  return request<{ response: string; session_id: string }>(
    `/course/chat`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, message, session_id: sessionId }),
    }
  )
}

export async function generateQuiz(kbId: string, topic?: string, numQuestions: number = 5) {
  return request<{ quiz_id: string; questions: Array<{ id: string; question: string; options: string[]; answer: number }> }>(
    `/course/quiz/generate`,
    {
      method: 'POST',
      body: JSON.stringify({ kb_id: kbId, topic, num_questions: numQuestions }),
    }
  )
}

export async function evaluateQuiz(quizId: string, answers: Record<string, number>) {
  return request<{
    score: number
    results: Array<{ question_id: string; correct: boolean; correct_answer: number; explanation: string }>
  }>(
    `/course/quiz/evaluate`,
    {
      method: 'POST',
      body: JSON.stringify({ quiz_id: quizId, answers }),
    }
  )
}

// ==================== Paper Reader ====================

export async function summarize(paperId: string) {
  return request<{
    paper_id: string
    title: string
    key_contributions: string[]
    methodology: string
    findings: string[]
    limitations: string[]
  }>(`/paper/summarize`, {
    method: 'POST',
    body: JSON.stringify({ paper_id: paperId }),
  })
}

export async function quickSummary(paperId: string) {
  return request<{ paper_id: string; summary: string }>(`/paper/quick-summary`, {
    method: 'POST',
    body: JSON.stringify({ paper_id: paperId }),
  })
}

export async function extractConcepts(paperId: string) {
  return request<{
    paper_id: string
    concepts: Array<{ name: string; definition: string; importance: string }>
  }>(`/paper/extract-concepts`, {
    method: 'POST',
    body: JSON.stringify({ paper_id: paperId }),
  })
}

export async function generateSocratic(paperId: string, section?: string, level: string = 'intermediate') {
  return request<{
    questions: Array<{ id: string; question: string; hint: string; key_points: string[] }>
  }>(`/paper/socratic/generate`, {
    method: 'POST',
    body: JSON.stringify({ paper_id: paperId, section, level }),
  })
}

export async function evaluateSocratic(paperId: string, questionId: string, response: string) {
  return request<{
    question_id: string
    score: number
    feedback: string
    key_points_covered: string[]
    suggestions: string[]
  }>(`/paper/socratic/evaluate`, {
    method: 'POST',
    body: JSON.stringify({ paper_id: paperId, question_id: questionId, response }),
  })
}

export async function recommendLiterature(paperId: string, numRecommendations: number = 5) {
  return request<{
    recommendations: Array<{
      title: string
      authors: string
      year: number
      relevance: number
      reason: string
    }>
    literature_map: { nodes: Array<{ id: string; label: string; group: string }>; edges: Array<{ source: string; target: string; weight: number }> }
  }>(`/paper/recommend`, {
    method: 'POST',
    body: JSON.stringify({ paper_id: paperId, num_recommendations: numRecommendations }),
  })
}

export async function uploadPaper(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${BASE_URL}/paper/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || '上传论文失败')
  }
  return res.json() as Promise<{ paper_id: string; title: string }>
}

// ==================== Knowledge Base ====================

export async function createKB(name: string, description: string) {
  return request<{ kb_id: string; name: string; description: string }>(`/kb/create`, {
    method: 'POST',
    body: JSON.stringify({ name, description }),
  })
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
    docs: Array<{ doc_id: string; filename: string; chunk_count: number; uploaded_at: string }>
    created_at: string
  }>(`/kb/${kbId}`)
}

export async function deleteKB(kbId: string) {
  return request<{ message: string }>(`/kb/${kbId}`, {
    method: 'DELETE',
  })
}

export async function searchKB(kbId: string, query: string, searchType: string = 'semantic', topK: number = 5) {
  return request<{
    results: Array<{ content: string; metadata: Record<string, unknown>; score: number; source: string }>
  }>(`/kb/${kbId}/search`, {
    method: 'POST',
    body: JSON.stringify({ query, search_type: searchType, top_k: topK }),
  })
}

export async function multiKBSearch(kbIds: string[], query: string, topK: number = 5) {
  return request<{
    results: Array<{ content: string; metadata: Record<string, unknown>; score: number; source: string; kb_id: string }>
  }>(`/kb/search/multi`, {
    method: 'POST',
    body: JSON.stringify({ kb_ids: kbIds, query, top_k: topK }),
  })
}

export async function nlQuery(kbId: string, query: string) {
  return request<{
    results: Array<{ content: string; metadata: Record<string, unknown>; score: number; source: string }>
    interpreted_query: string
  }>(`/kb/${kbId}/nl-query`, {
    method: 'POST',
    body: JSON.stringify({ query }),
  })
}

// ==================== Learning Path ====================

export async function createPlan(goal: string, currentLevel: string, timeframe: string, preferences?: Record<string, unknown>) {
  return request<{
    plan_id: string
    goal: string
    milestones: Array<{
      id: string
      title: string
      description: string
      order: number
      tasks: Array<{ id: string; title: string; description: string; estimated_hours: number }>
    }>
  }>(`/learning/plan/create`, {
    method: 'POST',
    body: JSON.stringify({ goal, current_level: currentLevel, timeframe, preferences }),
  })
}

export async function refinePlan(planId: string, feedback: string) {
  return request<{
    plan_id: string
    milestones: Array<{
      id: string
      title: string
      description: string
      order: number
      tasks: Array<{ id: string; title: string; description: string; estimated_hours: number }>
    }>
  }>(`/learning/plan/${planId}/refine`, {
    method: 'POST',
    body: JSON.stringify({ feedback }),
  })
}

export async function updateProgress(planId: string, milestoneId: string, taskId: string, status: string) {
  return request<{ message: string; completion_percentage: number }>(
    `/learning/plan/${planId}/progress`,
    {
      method: 'POST',
      body: JSON.stringify({ milestone_id: milestoneId, task_id: taskId, status }),
    }
  )
}

export async function getProgress(planId: string) {
  return request<{
    plan_id: string
    goal: string
    completion_percentage: number
    streak: number
    total_study_hours: number
    milestones: Array<{
      id: string
      title: string
      description: string
      order: number
      status: string
      tasks: Array<{ id: string; title: string; description: string; estimated_hours: number; status: string }>
    }>
  }>(`/learning/plan/${planId}/progress`)
}

export async function recordSession(planId: string, milestoneId: string, taskId: string, duration: number, notes?: string) {
  return request<{ message: string; total_hours: number }>(
    `/learning/plan/${planId}/session`,
    {
      method: 'POST',
      body: JSON.stringify({ milestone_id: milestoneId, task_id: taskId, duration, notes }),
    }
  )
}

export async function getRecommendations(planId: string) {
  return request<{
    recommendations: Array<{
      type: string
      title: string
      description: string
      priority: string
      action: string
    }>
  }>(`/learning/plan/${planId}/recommendations`)
}
