// Playwright CLI run-code --filename. Only self-authored UI fixtures; not a benchmark.
async (page) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const origin = await page.evaluate(() => location.origin);
  if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin)) throw new Error('Local application required');
  const checks = [];
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const check = (ok, name) => { if (!ok) throw new Error(name); checks.push(name); };
  const title = 'UI_SELF_AUTHORED · 数组求和 · ' + Date.now();
  const output = 'output/playwright/result-review-20261016/flow';
  await page.goto(origin + '/questions/create');
  await page.getByRole('button', { name: '保存题目', exact: true }).click();
  await page.getByText('题目标题不能为空', { exact: true }).waitFor();
  checks.push('EMPTY_TITLE_VALIDATION');
  await page.getByRole('textbox', { name: /题目标题/ }).fill(title);
  await page.getByRole('textbox', { name: '题目描述', exact: true }).fill('自有合成界面联调，不用于正式实验。读取 n 和 n 个整数，输出所有整数的和。');
  await page.getByRole('textbox', { name: '输入格式', exact: true }).fill('第一行 n，第二行 n 个整数。');
  await page.getByRole('textbox', { name: '输出格式', exact: true }).fill('输出一个整数。');
  await page.getByRole('textbox', { name: '约束条件', exact: true }).fill('1 <= n <= 1000');
  await page.getByRole('button', { name: '共同模板 · 可选登记' }).click();
  await page.getByRole('textbox', { name: '共同模板源码' }).fill('def placeholder():\n    pass\n');
  await page.getByRole('button', { name: '保存题目', exact: true }).click();
  await page.getByText('登记共同模板时请填写来源依据', { exact: true }).waitFor();
  checks.push('TEMPLATE_SOURCE_VALIDATION');
  await page.getByRole('textbox', { name: '共同模板源码' }).fill('');
  await page.getByRole('button', { name: '共同模板 · 可选登记' }).click();
  const [createdResponse] = await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/api/questions') && response.request().method() === 'POST'),
    page.getByRole('button', { name: '保存题目', exact: true }).click(),
  ]);
  const question = (await createdResponse.json()).data;
  check(createdResponse.ok() && question.id > 0, 'QUESTION_CREATE_REAL_API');
  await page.waitForURL('**/questions');
  await page.getByRole('textbox', { name: '本页搜索题目', exact: true }).fill('NO_MATCH_SELF_AUTHORED');
  await page.getByText('本页没有匹配的题目', { exact: true }).waitFor();
  await page.getByRole('textbox', { name: '本页搜索题目', exact: true }).fill('');
  await page.getByRole('link', { name: title, exact: true }).click();
  await page.getByRole('heading', { name: title, exact: true }).waitFor();
  const sources = [
    { name: 'UI_SELF_A.py', student: 'UI_SELF_A' },
    { name: 'UI_SELF_B.py', student: 'UI_SELF_B' },
  ];
  for (const source of sources) {
    await page.getByRole('textbox', { name: '学生标识', exact: true }).fill(source.student);
    await page.locator('input[type="file"]').setInputFiles('coderisk/frontend-vue/tests/fixtures/' + source.name);
    await page.getByRole('button', { name: '保存提交', exact: true }).click();
    await page.getByRole('cell', { name: source.name, exact: true }).waitFor();
    check(await page.locator('input[type="file"]').inputValue() === '', 'FILE_INPUT_CLEARED_' + source.student);
  }
  await page.screenshot({ path: output + '/upload-desktop.png', fullPage: true, animations: 'disabled' });
  await page.getByRole('button', { name: '开始检测', exact: true }).click();
  await page.waitForURL(/\/tasks\/\d+\/results/);
  const taskUrl = page.url();
  await page.getByRole('heading', { name: '任务状态：FINISHED', exact: true }).waitFor({ timeout: 90000 });
  await page.getByRole('cell', { name: sources[0].name, exact: true }).waitFor();
  checks.push('TASK_FINISHED_AND_RESULT_VISIBLE_REAL_ANALYSIS');
  await page.getByRole('textbox', { name: '本页搜索文件名', exact: true }).fill('NO_MATCH_SELF_AUTHORED');
  await page.locator('.results-desktop').getByText('本页没有符合条件的代码对', { exact: true }).waitFor();
  await page.getByRole('textbox', { name: '本页搜索文件名', exact: true }).fill('');
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: '导出报告', exact: true }).click()]);
  check(download.suggestedFilename().endsWith('.html'), 'HTML_REPORT_DOWNLOAD');
  await download.saveAs(output + '/self-authored-report.html');
  await page.screenshot({ path: output + '/task-results-desktop.png', fullPage: true, animations: 'disabled' });
  await page.getByRole('button', { name: '查看', exact: true }).click();
  await page.waitForURL(/\/results\/\d+$/);
  await page.getByRole('heading', { name: '结果证据', exact: true }).waitFor();
  const resultUrl = page.url();
  await page.getByRole('heading', { name: '源码对照', exact: true }).waitFor();
  await page.getByText('Token 片段', { exact: true }).first().click();
  check(await page.locator('.selected-evidence').isVisible(), 'EVIDENCE_ROW_SELECTION');
  check(await page.locator('.code-line.highlighted').count() > 0, 'SOURCE_LINE_HIGHLIGHTS');
  await page.getByRole('button', { name: '全部高亮', exact: true }).click();
  await page.getByRole('tab', { name: '题目与阈值', exact: true }).click();
  await page.getByRole('heading', { name: '动态阈值分解', exact: true }).waitFor();
  checks.push('PROFILE_AND_THRESHOLD_TAB');
  await page.getByRole('tab', { name: '标识符映射', exact: true }).click();
  check(await page.getByRole('tabpanel', { name: '标识符映射', exact: true }).locator('.el-table__row').count() > 0, 'IDENTIFIER_MAPPING_TAB');
  await page.getByRole('tab', { name: '背景复核', exact: true }).click();
  await page.getByRole('heading', { name: '版本与自然相似背景' }).waitFor();
  await page.getByRole('tab', { name: '证据与源码', exact: true }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: output + '/evidence-desktop.png', fullPage: true, animations: 'disabled' });
  check(await page.locator('aside[aria-label="主导航"] a[aria-current="page"]').getAttribute('href') === '/tasks', 'RESULT_BELONGS_TO_TASK_NAVIGATION');
  const viewports = [1440, 768, 390, 320];
  const routes = ['/dashboard', '/questions', '/questions/create', '/questions/' + question.id + '/submissions', '/tasks', resultUrl.slice(origin.length), '/settings'];
  for (const width of viewports) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of routes) {
      await page.goto(origin + route);
      await page.locator('main h1').waitFor();
      await page.waitForLoadState('networkidle');
      if (route.includes('/results/')) await page.getByRole('heading', { name: '源码对照', exact: true }).waitFor();
      const overflow = await page.evaluate(() => ({ width: innerWidth, body: document.documentElement.scrollWidth }));
      check(overflow.body <= overflow.width + 1, 'NO_PAGE_OVERFLOW_' + width + '_' + route);
    }
    await page.goto(resultUrl);
    await page.getByRole('heading', { name: '源码对照', exact: true }).waitFor();
    await page.screenshot({ path: output + '/evidence-' + width + '.png', fullPage: true, animations: 'disabled' });
    if (width === 390) {
      await page.goto(origin + '/dashboard');
      await page.getByRole('heading', { name: '最近检测任务', exact: false }).waitFor();
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: output + '/dashboard-mobile.png', fullPage: true, animations: 'disabled' });
    }
  }
  check(errors.length === 0, 'NO_BROWSER_RUNTIME_ERRORS');
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(origin + '/dashboard');
  await page.locator('.question-row').filter({ hasText: title }).waitFor();
  await page.screenshot({ path: output + '/dashboard-desktop.png', fullPage: true, animations: 'disabled' });
  return { dataKind: 'SELF_AUTHORED_UI_SMOKE_ONLY_NOT_BENCHMARK', questionId: question.id, taskUrl, resultUrl, checks, errors, sourceExecution: false };
}
