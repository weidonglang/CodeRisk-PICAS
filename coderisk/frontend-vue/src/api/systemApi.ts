import { getApi, type ApiResponse } from './http'

export type SupportLevel = 'STABLE' | 'EXPERIMENTAL' | 'DISABLED'

export interface SystemHealth {
  status: string
  appVersion: string
  service: string
  checkedAt: string
  analysisBaseUrl: string
}

export interface LanguageDescriptor {
  language: string
  displayName: string
  supportLevel: SupportLevel
  defaultEnabled: boolean
}

export interface TaskModeDescriptor {
  code: string
  name: string
  version: string
  stable: boolean
}

export async function getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
  return getApi<SystemHealth>('/system/health')
}

export async function getLanguages(): Promise<ApiResponse<LanguageDescriptor[]>> {
  return getApi<LanguageDescriptor[]>('/system/languages')
}

export async function getTaskModes(): Promise<ApiResponse<TaskModeDescriptor[]>> {
  return getApi<TaskModeDescriptor[]>('/system/task-modes')
}
