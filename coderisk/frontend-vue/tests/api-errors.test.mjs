import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import ts from 'typescript'

const source = fs.readFileSync(new URL('../src/api/errorMessage.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText
const { requestErrorMessage } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`)

test('network errors name the unavailable backend', () => assert.equal(requestErrorMessage({}), '后端连接失败，请检查服务状态'))
test('timeouts have their own actionable status', () => assert.equal(requestErrorMessage({ code: 'ECONNABORTED' }), '请求超时，请稍后重试'))
test('server errors do not expose internal response messages', () => assert.equal(requestErrorMessage({ response: { status: 500, data: { message: 'PRIVATE_SQL_PATH' } } }), '后端服务暂不可用，请稍后重试'))
test('validation errors preserve the API message', () => assert.equal(requestErrorMessage({ response: { status: 400, data: { message: '文件类型不支持' } } }), '文件类型不支持'))
test('non-string messages are not coerced into user-facing content', () => assert.equal(requestErrorMessage({ response: { status: 400, data: { message: { path: 'PRIVATE' } } } }), '请求失败'))
test('blank validation messages have a fallback', () => assert.equal(requestErrorMessage({ response: { status: 422, data: { message: ' ' } } }), '请求失败'))
