import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import ts from 'typescript'

const source = fs.readFileSync(new URL('../src/utils/presentation.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText
const ui = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`)

test('missing or invalid scores are not displayed as zero', () => {
  for (const value of [undefined, null, NaN, Infinity, -.1, 1.1]) assert.equal(ui.percent(value), '-')
  assert.equal(ui.percent(0), '0%')
  assert.equal(ui.percent(.9345, 1), '93.5%')
})
test('margins retain sign and units', () => {
  assert.equal(ui.margin(.125), '+12.5 pp')
  assert.equal(ui.margin(-.12), '-12.0 pp')
  assert.equal(ui.margin(undefined), '-')
})
test('progress is finite, bounded, and honest for an empty task', () => {
  assert.equal(ui.progress(0, 0), 0)
  assert.equal(ui.progress(2, 3), 67)
  assert.equal(ui.progress(-1, 3), 0)
  assert.equal(ui.progress(10, 3), 100)
  assert.equal(ui.progress(NaN, 3), 0)
})
test('search is literal, trimmed and case insensitive', () => {
  assert.ok(ui.includesQuery(' SUM ', 'array_sum.py'))
  assert.ok(ui.includesQuery('', null))
  assert.ok(!ui.includesQuery('.*', 'array_sum.py'))
  assert.ok(ui.includesQuery('题目', '测试题目'))
})
test('risk and task labels preserve server-defined states', () => {
  assert.equal(ui.riskMeta('HIGH').label, '高风险')
  assert.equal(ui.riskMeta('UNSUPPORTED').label, '未知')
  assert.equal(ui.taskMeta('PARTIAL').label, '部分完成')
  assert.equal(ui.taskMeta('RUNNING').tone, 'primary')
  assert.equal(ui.taskMeta('MISSING').label, '未知')
})
test('timestamps use explicit Shanghai timezone and reject bad input', () => {
  assert.equal(ui.dateTime('bad'), '-')
  assert.equal(ui.dateTime(null), '-')
  assert.match(ui.dateTime('2026-10-16T01:23:00Z'), /09:23/)
})
