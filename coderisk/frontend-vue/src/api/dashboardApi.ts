import { getApi, type ApiResponse } from './http'

export interface DashboardSummary {
  questionCount: number
  submissionCount: number
  taskCount: number
  highRiskResultCount: number
  versionStage: string
  dataNotice: string
}

export async function getDashboardSummary(): Promise<ApiResponse<DashboardSummary>> {
  return getApi<DashboardSummary>('/dashboard/summary')
}
