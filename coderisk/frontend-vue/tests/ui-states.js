// UI-only intercepted states. Never writes mock records into the application database.
async (page) => {
  const origin = await page.evaluate(() => location.origin);
  if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin)) throw new Error('Local test application required');
  const checks = [];
  const check = (condition, name) => { if (!condition) throw new Error(name); checks.push(name); };
  const envelope = data => ({ success: true, code: 'OK', message: '', data, traceId: 'UI_FIXTURE_ONLY' });
  const fulfill = (route, data) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(envelope(data)) });
  await page.setViewportSize({ width: 1440, height: 1000 });
  const pages = [];
  await page.route('**/api/questions?*', async route => {
    const second = /[?&]page=2(?:&|$)/.test(route.request().url());
    pages.push(second ? 2 : 1);
    const items = Array.from({ length: second ? 1 : 20 }, (_, index) => ({ id: 10001 + index + (second ? 20 : 0), title: 'UI_PAGE_' + (index + (second ? 21 : 1)), inputFormat: 'UI_ONLY', outputFormat: 'UI_ONLY', createdAt: '2026-10-16T00:00:00Z', starterCode: '' }));
    await fulfill(route, { items, total: 21, page: second ? 2 : 1, pageSize: 20, totalPages: 2 });
  });
  try {
    await page.goto(origin + '/questions');
    await page.getByRole('link', { name: 'UI_PAGE_1', exact: true }).waitFor();
    await page.locator('.el-pagination .btn-next').click();
    await page.getByRole('link', { name: 'UI_PAGE_21', exact: true }).waitFor();
    check(pages.includes(1) && pages.includes(2), 'QUESTION_SERVER_PAGINATION');
  } finally { await page.unroute('**/api/questions?*'); }
  await page.route(origin + '/api/**', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ success: false, message: 'PRIVATE_SERVER_DIAGNOSTIC_UI_FIXTURE' }) }));
  try {
    await page.goto(origin + '/dashboard');
    await page.getByText('后端未连接', { exact: true }).waitFor();
    await page.getByText('概览、最近任务、题目、语言加载失败', { exact: true }).waitFor();
    check((await page.locator('.metric-tile > strong').allTextContents()).every(text => text === '-'), 'UNAVAILABLE_COUNTS_ARE_NOT_FAKE_ZERO');
    check(!(await page.locator('body').innerText()).includes('PRIVATE_SERVER_DIAGNOSTIC'), 'SERVER_INTERNAL_MESSAGE_NOT_EXPOSED');
    await page.screenshot({ path: 'output/playwright/statistical-views-20261016/offline-fixture.png', animations: 'disabled' });
  } finally { await page.unroute(origin + '/api/**'); }
  const result = { id: 9991, taskId: 999, submissionAFileName: 'UI_FIXTURE_A.py', submissionBFileName: 'UI_FIXTURE_B.py', tokenSimilarity: .2, astSimilarity: null, canonicalTokenSimilarity: null, identifierMappingSimilarity: null, weightedSimilarityScore: .2, dynamicThreshold: .7, riskMargin: -.5, calibratedRiskScore: .1, exceedThreshold: false, riskLevel: 'LOW', isMock: true, problemProfile: {}, thresholdAdjustment: {}, formulaVersion: 'UI_FIXTURE_ONLY', reasonSummary: 'UI fixture: parser fallback, not an algorithm result.' };
  let experimental = false;
  await page.route('**/api/results/9991**', async route => {
    const url = route.request().url().split('?')[0];
    if (url.endsWith('/evidence')) await fulfill(route, experimental ? [{ id: 1, evidenceType: 'CROSSLANG_IR_MATCH', similarityScore: .4, description: 'UI fixture only', metadata: { irSequenceA: ['UI_INPUT', 'UI_RETURN'], irSequenceB: ['UI_INPUT', 'UI_RETURN'], coverageA: .8, coverageB: .8 } }] : [{ id: 1, evidenceType: 'PARSER_WARNING', similarityScore: 0, description: 'UI_SELF_UNSUPPORTED_SYNTAX: raw-only fallback', metadata: {} }]);
    else if (url.endsWith('/metrics')) await fulfill(route, experimental ? [{ name: 'CROSSLANG_IR_SIMILARITY', value: .4, weight: 0, explanation: 'UI_FIXTURE_ONLY' }] : []);
    else if (url.endsWith('/diff-view')) await fulfill(route, { codeA: { fileName: 'UI_FIXTURE_A.py', code: 'x = 1\n' }, codeB: { fileName: 'UI_FIXTURE_B.py', code: 'y = 1\n' }, highlights: [] });
    else await fulfill(route, result);
  });
  try {
    await page.goto(origin + '/results/9991');
    await page.getByText('UI_SELF_UNSUPPORTED_SYNTAX: raw-only fallback', { exact: true }).first().waitFor();
    const dimensions = await page.locator('.dimension-item strong').allTextContents();
    check(dimensions.join('|') === '20%|-|-|-', 'UNAVAILABLE_AST_CANONICAL_MAPPING_DISPLAY_AS_MISSING');
    check(await page.getByRole('tab', { name: '实验性指标', exact: true }).count() === 0, 'PARSER_FALLBACK_DOES_NOT_INVENT_IR');
    experimental = true;
    await page.reload();
    await page.getByRole('tab', { name: '实验性指标', exact: true }).click();
    await page.getByText('实验性能力 · 生产权重 0', { exact: true }).waitFor();
    checks.push('EXPERIMENTAL_METRICS_CLEAR_ZERO_WEIGHT_BOUNDARY');
  } finally { await page.unroute('**/api/results/9991**'); }
  const trace = [];
  let committed = false;
  await page.route('**/api/tasks/999**', async route => {
    const path = route.request().url().split('?')[0].slice(origin.length);
    trace.push({ path, committed });
    if (path === '/api/tasks/999') {
      await page.waitForTimeout(150); // Intentional race fixture, not production waiting.
      committed = true;
      await fulfill(route, { id: 999, taskName: 'UI_RACE_FIXTURE', taskMode: 'PICAS_STANDARD', status: 'FINISHED', totalSubmissions: 2, totalPairs: 1, finishedPairs: 1, failedPairs: 0, progress: 1, failureReason: '' });
    } else if (path.endsWith('/summary')) await fulfill(route, { totalResults: committed ? 1 : 0, lowCount: 1, mediumCount: 0, elevatedCount: 0, highCount: 0, containsMockData: true });
    else if (path.endsWith('/failures')) await fulfill(route, []);
    else await fulfill(route, { items: committed ? [{ ...result, id: 999, taskId: 999 }] : [], total: committed ? 1 : 0, page: 1, pageSize: 20 });
  });
  try {
    await page.goto(origin + '/tasks/999/results');
    await page.getByRole('heading', { name: '任务状态：FINISHED', exact: true }).waitFor();
    await page.getByRole('cell', { name: 'UI_FIXTURE_A.py', exact: true }).waitFor();
    const dependent = trace.filter(item => item.path !== '/api/tasks/999');
    check(dependent.length === 3 && dependent.every(item => item.committed), 'TERMINAL_STATUS_READ_BEFORE_RESULT_REQUESTS');
  } finally { await page.unroute('**/api/tasks/999**'); }
  await page.goto(origin + '/dashboard');
  await page.getByText('后端已连接', { exact: true }).waitFor();
  return { kind: 'INTERCEPTED_UI_FIXTURES_ONLY_NOT_BENCHMARK', checks, mockRoutesRemoved: true, databaseWrites: 0 };
}
