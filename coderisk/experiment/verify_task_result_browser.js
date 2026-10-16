// Playwright CLI run-code fixture. This is a controlled UI race check, not real data.
// Run with a dedicated session already opened on the local Vue application.
async (page) => {
  const trace = [];
  let committed = false;
  const envelope = data => ({ success: true, code: 'OK', data, message: '', traceId: 'UI_TEST_ONLY' });
  await page.route('**/api/tasks/999**', async route => {
    const url = new URL(route.request().url());
    trace.push({ path: url.pathname, resultsCommitted: committed });
    let data;
    if (url.pathname === '/api/tasks/999') {
      // Reproduce the final transition while a task request is in flight.
      await new Promise(resolve => setTimeout(resolve, 500));
      committed = true;
      data = { id: 999, questionId: 999, taskName: 'UI_TEST_ONLY', taskMode: 'PICAS_STANDARD',
        status: 'FINISHED', totalSubmissions: 2, totalPairs: 1, finishedPairs: 1,
        failedPairs: 0, progress: 1, submissionIds: [1, 2], failureReason: '' };
    } else if (url.pathname.endsWith('/summary')) {
      data = { taskId: 999, totalResults: committed ? 1 : 0, lowCount: 1,
        mediumCount: 0, elevatedCount: 0, highCount: 0, containsMockData: true };
    } else if (url.pathname.endsWith('/failures')) {
      data = [];
    } else {
      const row = { id: 999, taskId: 999, submissionAId: 1, submissionBId: 2,
        submissionAFileName: 'UI_TEST_ONLY-a.py', submissionBFileName: 'UI_TEST_ONLY-b.py',
        tokenSimilarity: .1, astSimilarity: .1, canonicalTokenSimilarity: .1,
        identifierMappingSimilarity: .1, weightedSimilarityScore: .1, dynamicThreshold: .7,
        riskMargin: -.6, calibratedRiskScore: 0, exceedThreshold: false, marginScale: .4,
        riskLevel: 'LOW', isMock: true, problemProfile: {}, thresholdAdjustment: {},
        reasonSummary: 'Self-authored UI fixture' };
      data = { items: committed ? [row] : [], total: committed ? 1 : 0,
        page: 1, pageSize: 20, totalPages: committed ? 1 : 0 };
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(envelope(data)) });
  });
  await page.goto('http://127.0.0.1:15173/tasks/999/results');
  await page.getByRole('heading', { name: '任务状态：FINISHED' }).waitFor();
  await page.getByText('UI_TEST_ONLY-a.py', { exact: true }).waitFor();
  const dependent = trace.filter(t => t.path !== '/api/tasks/999');
  if (dependent.length !== 3 || dependent.some(t => !t.resultsCommitted)) {
    throw new Error('Results were fetched before the terminal task transition committed');
  }
  await page.unroute('**/api/tasks/999**');
  return { check: 'TERMINAL_STATUS_RESULT_ORDER', data_kind: 'UI_TEST_ONLY',
    passed: true, final_result_visible: true, trace };
}
