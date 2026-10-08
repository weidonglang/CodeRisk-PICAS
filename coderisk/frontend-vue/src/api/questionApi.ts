import { getApi, postApi, type ApiResponse } from './http'

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface Question {
  id: number
  title: string
  description: string
  inputFormat: string
  outputFormat: string
  constraintsText: string
  starterLanguage: string
  starterCode: string
  starterSource: string
  createdAt: string
  updatedAt: string
}

export interface CreateQuestionBody {
  title: string
  description: string
  inputFormat: string
  outputFormat: string
  constraintsText: string
  starterLanguage?: string
  starterCode?: string
  starterSource?: string
}

export interface QuestionFeature {
  questionId: number
  featureVersion: string
  descriptionLength: number
  ioFieldCount: number
  constraintCount: number
  difficultyScore: number
  solutionSpaceScore: number
  templateRiskScore: number
  naturalSimilarityRisk: number
  recommendedBaseThreshold: number
  confidence: number
  explanation: Record<string, unknown>
  thresholdAdjustment: Record<string, unknown>
}

export async function listQuestions(): Promise<ApiResponse<PageResult<Question>>> {
  return getApi<PageResult<Question>>('/questions')
}

export async function getQuestion(questionId: number): Promise<ApiResponse<Question>> {
  return getApi<Question>(`/questions/${questionId}`)
}

export async function createQuestion(body: CreateQuestionBody): Promise<ApiResponse<Question>> {
  return postApi<Question, CreateQuestionBody>('/questions', body)
}

export async function computeQuestionFeature(questionId: number): Promise<ApiResponse<QuestionFeature>> {
  return postApi<QuestionFeature, Record<string, never>>(`/questions/${questionId}/features/compute`, {})
}

export async function getLatestQuestionFeature(questionId: number): Promise<ApiResponse<QuestionFeature>> {
  return getApi<QuestionFeature>(`/questions/${questionId}/features/latest`)
}
