import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import ts from 'typescript'
const source = fs.readFileSync(new URL('../src/utils/analysisStatistics.ts', import.meta.url), 'utf8')
const output = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText
const stats = await import(`data:text/javascript;base64,${Buffer.from(output).toString('base64')}`)

test('R7 descriptive quartiles use linear interpolation without mutating inputs', () => {
  const input = [.9, .1, .5, .3]
  const result = stats.describeScores(input)
  assert.deepEqual(input, [.9, .1, .5, .3])
  assert.equal(result.n, 4)
  assert.ok(Math.abs(result.q1 - .25) < 1e-12)
  assert.equal(result.median, .4)
  assert.ok(Math.abs(result.q3 - .6) < 1e-12)
  assert.ok(Math.abs(result.mean - .45) < 1e-12)
})
test('zero is valid; missing, strings and invalid scores are not zero observations', () => {
  const result = stats.describeScores([0, 1, null, undefined, NaN, Infinity, -.1, 1.1, '0.5'])
  assert.equal(result.n, 2)
  assert.equal(result.missing, 7)
  assert.equal(result.min, 0)
  assert.equal(result.max, 1)
  assert.equal(result.median, .5)
})
test('empty and singleton statistics are explicit, with no invented spread', () => {
  const empty = stats.describeScores([null])
  assert.equal(empty.n, 0)
  for (const key of ['min','max','q1','q3','median','mean']) assert.equal(empty[key], null)
  const single = stats.describeScores([.8])
  assert.equal(single.n, 1)
  assert.equal(single.min, single.max)
  assert.equal(stats.quantile([], .5), null)
  assert.equal(stats.quantile([1], NaN), null)
})
test('histogram bins are left-closed/right-open, except the last includes 1', () => {
  const value = stats.scoreHistogram([0, .099, .1, .2, .999, 1, null], 10)
  assert.deepEqual(value.bins.map(bin => bin.count), [2,1,1,0,0,0,0,0,0,2])
  assert.equal(value.bins.reduce((sum, bin) => sum + bin.count, 0), value.n)
  assert.equal(value.n, 6)
  assert.equal(value.missing, 1)
  assert.equal(value.bins[9].upperInclusive, true)
})
test('proportion denominators are valid observations, not all rows', () => {
  const value = stats.scoreHistogram([.2, .8, null, NaN], 2)
  assert.deepEqual(value.bins.map(bin => bin.share), [.5,.5])
  assert.equal(stats.scoreHistogram([]).bins[0].share, null)
  for (const n of [0, 51, 1.5, NaN]) assert.throws(() => stats.scoreHistogram([], n))
})
test('paired scatter requires both metrics and does not infer relationship labels', () => {
  const result = stats.normalizationPairs([
    {id:1,tokenSimilarity:.2,canonicalTokenSimilarity:.8,riskLevel:'LOW'},
    {id:2,tokenSimilarity:.7,canonicalTokenSimilarity:.4},
    {id:3,tokenSimilarity:0,canonicalTokenSimilarity:0},
    {id:4,tokenSimilarity:.5,canonicalTokenSimilarity:null},
  ])
  assert.equal(result.n,3); assert.equal(result.missing,1)
  assert.equal(result.increased,1); assert.equal(result.decreased,1); assert.equal(result.unchanged,1)
  assert.equal(result.points[0].riskLevel,'LOW')
  assert.equal(result.points[1].riskLevel,'UNKNOWN')
})
test('heatmap omits unknown cells but preserves real zero', () => {
  const cells = stats.dimensionHeatmap([{id:7,tokenSimilarity:0,astSimilarity:null,canonicalTokenSimilarity:.9}])
  assert.equal(cells.length,2)
  assert.equal(cells[0].value,0)
  assert.equal(cells[1].columnIndex,2)
  assert.ok(cells.every(cell => cell.id === 7))
})
test('each dimension keeps its own denominator for boxplots', () => {
  const result = stats.dimensionSummaries([{id:1,tokenSimilarity:.2,astSimilarity:.5},{id:2,tokenSimilarity:.8,astSimilarity:null}])
  assert.equal(result[0].n,2); assert.equal(result[1].n,1); assert.equal(result[2].n,0)
  assert.equal(result[1].missing,1)
})
test('HTML structure values are not mislabeled as programming-language AST', () => {
  const html = [{id:1,formulaVersion:'HTML_STRUCTURE_FIXED_V1',astSimilarity:.8}]
  assert.equal(stats.dimensionSummaries(html)[1].label,'HTML 结构')
  assert.equal(stats.dimensionHeatmap(html)[0].label,'HTML 结构')
  assert.equal(stats.dimensionSummaries([{id:2,astSimilarity:.8}])[1].label,'AST')
})
test('CSV escapes spreadsheet formulas, separators and missing values without changing numeric signs', () => {
  assert.equal(stats.csvCell('=SUM(A1)'), '"\'=SUM(A1)"')
  assert.equal(stats.csvCell('  +cmd'), '"\'  +cmd"')
  assert.equal(stats.csvCell('a,"b"'), '"a,""b"""')
  assert.equal(stats.csvCell(-.4), '-0.4')
  const csv = stats.analysisCsv([{id:1,submissionAFileName:'@test.py',weightedSimilarityScore:null}], 'CURRENT_PAGE_FILTERED')
  assert.ok(csv.startsWith('\uFEFFscope,'))
  assert.ok(csv.includes('"\'@test.py"'))
  assert.ok(csv.includes('"CURRENT_PAGE_FILTERED"'))
})
