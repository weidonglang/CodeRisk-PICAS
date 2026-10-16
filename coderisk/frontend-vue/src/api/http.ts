import axios from 'axios'
import { requestErrorMessage } from './errorMessage'

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

httpClient.interceptors.response.use(response => {
  if (response.data?.success === false) throw new Error(typeof response.data.message === 'string' ? response.data.message : '请求未成功')
  return response
}, error => {
  if (!axios.isAxiosError(error)) return Promise.reject(error)
  return Promise.reject(new Error(requestErrorMessage(error)))
})

export async function getApi<T>(url: string): Promise<ApiResponse<T>> {
  const response = await httpClient.get<ApiResponse<T>>(url)
  return response.data
}

export async function postApi<T, B>(url: string, body: B): Promise<ApiResponse<T>> {
  const response = await httpClient.post<ApiResponse<T>>(url, body)
  return response.data
}
