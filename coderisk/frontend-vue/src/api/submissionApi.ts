import { getApi, httpClient, type ApiResponse } from './http'

export type ParserStatus = 'NOT_PARSED' | 'PARSED' | 'PARTIAL' | 'FAILED' | 'FALLBACK_TOKEN_ONLY'
export type SupportLevel = 'STABLE' | 'EXPERIMENTAL' | 'DISABLED'

export interface Submission {
  id: number
  questionId: number
  studentId: string
  language: string
  languageVersion: string
  supportLevel: SupportLevel
  fileName: string
  fileSizeBytes: number
  rawCodePath: string
  parserStatus: ParserStatus
  createdAt: string
}

export async function listSubmissions(questionId: number): Promise<ApiResponse<Submission[]>> {
  return getApi<Submission[]>(`/questions/${questionId}/submissions`)
}

export async function uploadSubmission(
  questionId: number,
  studentId: string,
  file: File,
  languageVersion = '',
): Promise<ApiResponse<Submission>> {
  const form = new FormData()
  form.append('studentId', studentId)
  form.append('languageVersion', languageVersion)
  form.append('file', file)
  const response = await httpClient.post<ApiResponse<Submission>>(
    `/questions/${questionId}/submissions/upload`,
    form,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    },
  )
  return response.data
}
