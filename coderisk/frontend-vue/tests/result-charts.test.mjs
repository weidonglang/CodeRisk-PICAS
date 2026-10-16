import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import ts from 'typescript'
const source = fs.readFileSync(new URL('../src/utils/resultCharts.ts', import.meta.url), 'utf8')
const output = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText
const charts = await import(`data:text/javascript;base64,${Buffer.from(output).toString('base64')}`)

test('chart scores reject unavailable and out-of-range values rather than clamp to a fake score', () => {
  for (const value of [null, undefined, NaN, Infinity, -.01, 1.01, '0.5']) assert.equal(charts.scorePosition(value), null)
  assert.equal(charts.scorePosition(0), 0)
  assert.equal(charts.scorePosition(1), 100)
  assert.equal(charts.scorePosition(.73), 73)
})
test('canonical difference is a signed display delta, not a risk recalculation', () => {
  assert.equal(charts.scoreDifference(.25, .9), .65)
  assert.equal(charts.scoreDifference(.9, .25), -.65)
  assert.equal(charts.scoreDifference(.5, null), null)
  assert.equal(charts.scoreDifference(0, 0), 0)
})
test('full-task risk distribution includes medium and is not inferred from one page', () => {
  const value = charts.riskDistribution({ totalResults: 100, lowCount: 40, mediumCount: 30, elevatedCount: 20, highCount: 10 })
  assert.equal(value.available, true)
  assert.deepEqual(value.segments.map(row => row.share), [40, 30, 20, 10])
  assert.deepEqual(value.segments.map(row => row.count), [40, 30, 20, 10])
})
test('missing, inconsistent, or unsafe counts never silently become a valid distribution', () => {
  for (const summary of [null, {}, {totalResults: 1, lowCount: 0, mediumCount: 0, elevatedCount: 0, highCount: 0}, {totalResults: 0, lowCount: -1, mediumCount: 0, elevatedCount: 0, highCount: 1}, {totalResults: 1, lowCount: .5, mediumCount: .5, elevatedCount: 0, highCount: 0}]) {
    const value = charts.riskDistribution(summary)
    assert.equal(value.available, false)
    assert.ok(value.segments.every(row => row.count === null))
  }
})
test('empty distribution stays empty without divide-by-zero', () => {
  const value = charts.riskDistribution({totalResults: 0, lowCount: 0, mediumCount: 0, elevatedCount: 0, highCount: 0})
  assert.equal(value.available, true)
  assert.equal(value.total, 0)
  assert.ok(value.segments.every(row => row.share === 0))
})
test('signed threshold adjustment bars use a shared zero-centered scale', () => {
  assert.deepEqual(charts.adjustmentBar(.1, .2), {left: 50, width: 25})
  assert.deepEqual(charts.adjustmentBar(-.2, .2), {left: 0, width: 50})
  assert.deepEqual(charts.adjustmentBar(0, .2), {left: 50, width: 0})
  assert.equal(charts.adjustmentBar(undefined, .2), null)
  assert.equal(charts.adjustmentBar(.2, 0), null)
})
