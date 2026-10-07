import axios from 'axios'

export interface ApiResponse<T> {
  success: boolean
  code: string
  message: string
  data: T
  traceId: string
  timestamp: string
}

export const httpClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export async function getApi<T>(url: string): Promise<ApiResponse<T>> {
  const response = await httpClient.get<ApiResponse<T>>(url)
  return response.data
}

export async function postApi<T, B>(url: string, body: B): Promise<ApiResponse<T>> {
  const response = await httpClient.post<ApiResponse<T>>(url, body)
  return response.data
}
