import { getApi, postApi, type ApiResponse } from './http'

export type TaskStatus = 'PENDING' | 'QUEUED' | 'RUNNING' | 'PARTIAL' | 'FAILED' | 'CANCELLED' | 'FINISHED'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'ELEVATED' | 'HIGH'
export type TaskMode = 'BASIC_TOKEN' | 'TOKEN_AST' | 'PICAS_INVARIANT' | 'PICAS_STANDARD' | 'PICAS_CROSSLANG' | 'PICAS_EXPERIMENTAL'

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface DetectionTask {
  id: number
  questionId: number
  taskName: string
  taskMode: TaskMode
  status: TaskStatus
  totalSubmissions: number
  totalPairs: number
  finishedPairs: number
  failedPairs: number
  progress: number
  submissionIds: number[]
  failureReason: string
  createdAt: string
  finishedAt: string | null
}

export interface TaskSummary {
  id: number
  taskName: string
  taskMode: TaskMode
  status: TaskStatus
  finishedPairs: number
  failedPairs: number
  totalPairs: number
  createdAt: string
}

export interface TaskPairFailure {
  submissionAId: number
  submissionBId: number
  message: string
  attempts: number
  resolved: boolean
  lastAttemptAt: string
}

export async function getTaskFailures(taskId: number): Promise<ApiResponse<TaskPairFailure[]>> {
  return getApi<TaskPairFailure[]>(`/tasks/${taskId}/failures`)
}

export interface CreateTaskBody {
  questionId: number
  taskName: string
  submissionIds: number[]
  taskMode?: TaskMode
}

export interface ProblemProfile {
  domain?: string
  featureVersion?: string
  descriptionLength?: number
  ioFieldCount?: number
  constraintCount?: number
  difficultyScore?: number
  solutionSpaceScore?: number
  templateRiskScore?: number
  naturalSimilarityRisk?: number
  recommendedBaseThreshold?: number
  confidence?: number
  explanation?: Record<string, unknown>
}

export interface ThresholdAdjustment {
  policy?: string
  baseThreshold?: number
  difficultyAdjustment?: number
  solutionSpaceAdjustment?: number
  templateRiskAdjustment?: number
  naturalSimilarityAdjustment?: number
  historicalDistributionAdjustment?: number
  finalThreshold?: number
  formulaVersion?: string
  explanation?: string
}

export interface ResultRow {
  id: number
  taskId: number
  submissionAId: number
  submissionBId: number
  submissionAFileName: string
  submissionBFileName: string
  tokenSimilarity: number
  astSimilarity: number
  canonicalTokenSimilarity: number
  identifierMappingSimilarity: number
  weightedSimilarityScore: number
  dynamicThreshold: number
  riskMargin: number
  calibratedRiskScore: number
  exceedThreshold: boolean
  marginScale: number
  formulaVersion: string
  algorithmVersion: string
  metricConfigHash: string
  riskLevel: RiskLevel
  problemProfile: ProblemProfile
  thresholdAdjustment: ThresholdAdjustment
  reasonSummary: string
  isMock: boolean
  createdAt: string
}

export interface TaskResultSummary {
  taskId: number
  totalResults: number
  lowCount: number
  mediumCount: number
  elevatedCount: number
  highCount: number
  containsMockData: boolean
}

export interface EvidenceItem {
  id: number
  resultId: number
  evidenceType: string
  similarityScore: number
  description: string
  metadata: Record<string, unknown>
}

export interface SimilarityMetric {
  name: string
  value: number
  weight: number
  explanation: string
}

export interface IdentifierMappingItem {
  mappingType: string
  kind: string
  canonicalName: string
  scopePath: string
  submissionAName: string
  submissionBName: string
  submissionALine: number
  submissionBLine: number
  occurrenceA: number
  occurrenceB: number
  confidence: number
}

export interface CodeSide {
  submissionId: number
  fileName: string
  language: string
  code: string
}

export interface CodePair {
  resultId: number
  taskId: number
  submissionA: CodeSide
  submissionB: CodeSide
}

export interface LineRange {
  startLine: number
  endLine: number
}

export interface DiffHighlight {
  evidenceId: number
  type: string
  aRange: LineRange
  bRange: LineRange
  confidence: number
}

export interface DiffView {
  resultId: number
  taskId: number
  codeA: CodeSide
  codeB: CodeSide
  highlights: DiffHighlight[]
}

export interface ReportResult {
  reportId: number
  taskId: number
  status: 'NOT_GENERATED' | 'GENERATING' | 'GENERATED' | 'FAILED'
  format: 'HTML'
  fileName: string
  downloadUrl: string
  createdAt: string
}

export interface CreateReportBody {
  format: 'HTML'
  includeLowRiskPairs: boolean
  includeCodeSnippets: boolean
  includeThresholdExplanation: boolean
}

export async function createTask(body: CreateTaskBody): Promise<ApiResponse<DetectionTask>> {
  return postApi<DetectionTask, CreateTaskBody>('/tasks', body)
}

export async function startTask(taskId: number): Promise<ApiResponse<DetectionTask>> {
  return postApi<DetectionTask, Record<string, never>>(`/tasks/${taskId}/start`, {})
}

export async function getTask(taskId: number): Promise<ApiResponse<DetectionTask>> {
  return getApi<DetectionTask>(`/tasks/${taskId}`)
}

export async function listRecentTasks(): Promise<ApiResponse<TaskSummary[]>> {
  return getApi<TaskSummary[]>('/tasks/recent')
}

export async function getTaskResults(taskId: number, page = 1): Promise<ApiResponse<PageResult<ResultRow>>> {
  return getApi<PageResult<ResultRow>>(`/tasks/${taskId}/results?page=${page}&pageSize=20`)
}

export async function getTaskResultSummary(taskId: number): Promise<ApiResponse<TaskResultSummary>> {
  return getApi<TaskResultSummary>(`/tasks/${taskId}/results/summary`)
}

export async function getResult(resultId: number): Promise<ApiResponse<ResultRow>> {
  return getApi<ResultRow>(`/results/${resultId}`)
}

export async function getResultEvidence(resultId: number): Promise<ApiResponse<EvidenceItem[]>> {
  return getApi<EvidenceItem[]>(`/results/${resultId}/evidence`)
}

export async function getResultMetrics(resultId: number): Promise<ApiResponse<SimilarityMetric[]>> {
  return getApi<SimilarityMetric[]>(`/results/${resultId}/metrics`)
}

export async function getThresholdAdjustment(resultId: number): Promise<ApiResponse<ThresholdAdjustment>> {
  return getApi<ThresholdAdjustment>(`/results/${resultId}/threshold-adjustment`)
}

export async function getIdentifierMappings(resultId: number): Promise<ApiResponse<IdentifierMappingItem[]>> {
  return getApi<IdentifierMappingItem[]>(`/results/${resultId}/identifier-mappings`)
}

export async function getResultCodePair(resultId: number): Promise<ApiResponse<CodePair>> {
  return getApi<CodePair>(`/results/${resultId}/code-pair`)
}

export async function getResultDiffView(resultId: number): Promise<ApiResponse<DiffView>> {
  return getApi<DiffView>(`/results/${resultId}/diff-view`)
}

export async function createTaskReport(taskId: number, body: CreateReportBody): Promise<ApiResponse<ReportResult>> {
  return postApi<ReportResult, CreateReportBody>(`/tasks/${taskId}/reports`, body)
}

export async function listTaskReports(taskId: number): Promise<ApiResponse<ReportResult[]>> {
  return getApi<ReportResult[]>(`/tasks/${taskId}/reports`)
}
