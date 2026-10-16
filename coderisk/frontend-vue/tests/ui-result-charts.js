// Intercepted display fixtures only. No API writes, scoring changes or benchmark claims.
async (page) => {
  const origin = await page.evaluate(() => location.origin);
  const output = 'output/playwright/result-review-20261016';
  if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin)) throw new Error('Local test application required');
  const checks = [], errors = [];
  const errorListener = error => errors.push(error.message);
  page.on('pageerror', errorListener);
  const check = (ok, label) => { if (!ok) throw new Error(label); checks.push(label); };
  const fulfill = (route, data) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({success: true, code: 'OK', data}) });
  const base = {id: 99001, taskId: 9900, submissionAFileName: 'UI_ONLY_sum_values.py', submissionBFileName: 'UI_ONLY_accumulate.py', tokenSimilarity: .28, astSimilarity: .92, canonicalTokenSimilarity: .98, identifierMappingSimilarity: .95, weightedSimilarityScore: .852, dynamicThreshold: .81, riskMargin: .042, calibratedRiskScore: .71, exceedThreshold: true, riskLevel: 'ELEVATED', isMock: true, formulaVersion: 'UI_DISPLAY_FIXTURE', algorithmVersion: 'NOT_AN_ALGORITHM_RESULT', reasonSummary: '浏览器临时模拟数据，仅验证展示，不写入数据库。', problemProfile: {difficultyScore:.4,solutionSpaceScore:.6,templateRiskScore:.3,naturalSimilarityRisk:.5}, thresholdAdjustment: {baseThreshold:.72,difficultyAdjustment:.02,solutionSpaceAdjustment:-.01,templateRiskAdjustment:.03,naturalSimilarityAdjustment:.05,historicalDistributionAdjustment:0,finalThreshold:.81,explanation:'UI fixture only'}};
  let missing = false;
  const row = () => missing ? {...base, astSimilarity:null, canonicalTokenSimilarity:null, identifierMappingSimilarity:null, weightedSimilarityScore:null, dynamicThreshold:null, riskMargin:null} : base;
  const rows = [base, {...base,id:99002,submissionAFileName:'UI_ONLY_format.java',riskLevel:'LOW',weightedSimilarityScore:.3,riskMargin:-.51,exceedThreshold:false}];
  const evidence = [{id:1,evidenceType:'TOKEN_MATCH',similarityScore:.28,description:'UI_ONLY token evidence',metadata:{fragments:[{submissionAStartLine:70,submissionAEndLine:71,submissionBStartLine:70,submissionBEndLine:71}]}},{id:2,evidenceType:'IDENTIFIER_MAPPING',similarityScore:.95,description:'UI_ONLY identifier mapping',metadata:{mappings:[{canonicalName:'v0',scopePath:'module/function0',submissionAName:'values',submissionBName:'items',kind:'VARIABLE'}]}}];
  const code = Array.from({length:120},(_,i)=>'# UI_ONLY self-authored display line '+(i+1)).join('\n');
  await page.route(origin + '/api/tasks/9900**', async route => {
    const url = route.request().url().split('?')[0];
    if(url.endsWith('/summary')) await fulfill(route,{taskId:9900,totalResults:100,lowCount:40,mediumCount:30,elevatedCount:20,highCount:10,containsMockData:true});
    else if(url.endsWith('/failures')) await fulfill(route,[]);
    else if(url.endsWith('/results')) await fulfill(route,{items:rows,total:100,page:1,pageSize:20,totalPages:5});
    else await fulfill(route,{id:9900,taskName:'UI_ONLY_DISPLAY_FIXTURE',taskMode:'PICAS_STANDARD',status:'FINISHED',totalPairs:100,finishedPairs:100,failedPairs:0,progress:1,createdAt:'2026-10-16T00:00:00Z'});
  });
  await page.route(origin + '/api/results/99001**', async route => {
    const url = route.request().url();
    if(url.endsWith('/evidence')) await fulfill(route,evidence);
    else if(url.endsWith('/metrics')) await fulfill(route,[]);
    else if(url.endsWith('/diff-view')) await fulfill(route,{codeA:{fileName:base.submissionAFileName,language:'PYTHON',code},codeB:{fileName:base.submissionBFileName,language:'PYTHON',code},highlights:[{evidenceId:1,aRange:{startLine:70,endLine:71},bRange:{startLine:70,endLine:71}}]});
    else await fulfill(route,row());
  });
  try {
    await page.setViewportSize({width:1440,height:1000});
    await page.goto(origin+'/tasks/9900/results');
    await page.getByRole('heading',{name:'任务状态：FINISHED',exact:true}).waitFor();
    check((await page.locator('.distribution-legend strong').allTextContents()).join('|')==='40|30|20|10','GLOBAL_DISTRIBUTION_USES_SUMMARY_NOT_TWO_PAGE_ROWS');
    await page.getByRole('textbox',{name:'本页搜索文件名',exact:true}).fill('format');
    check((await page.locator('.distribution-legend strong').allTextContents()).join('|')==='40|30|20|10','FILTER_DOES_NOT_REWRITE_FULL_TASK_DISTRIBUTION');
    await page.getByRole('textbox',{name:'本页搜索文件名',exact:true}).fill('');
    await page.getByText('图表',{exact:true}).click();
    check(await page.locator('.pair-chart-row').count()===2,'CHART_ALTERNATIVE_SHOWS_CURRENT_PAGE_PAIRS');
    check((await page.locator('.pair-chart-values').allTextContents()).join('|').includes('85.2%'),'CHART_RETAINS_DECIMAL_SCORE');
    for (const width of [1440,768,390,320]) {
      await page.setViewportSize({width,height:900});
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      check(!overflow,'PAIR_CHART_NO_OVERFLOW_'+width);
    }
    await page.getByText('列表',{exact:true}).click();
    check(await page.locator('.results-mobile').isVisible(),'MOBILE_PAIR_LIST_REPLACES_WIDE_TABLE');
    check(await page.locator('.mobile-pair').count()===2,'MOBILE_PAIR_LIST_RETAINS_BOTH_ROWS');
    await page.goto(origin+'/results/99001');
    await page.getByRole('heading',{name:'分数与阈值',exact:true}).waitFor();
    check((await page.locator('.score-analysis-primary .score-track').getAttribute('aria-label')).includes('85.2%'),'DETAIL_CHART_ACCESSIBLE_NUMERIC_ALTERNATIVE');
    check((await page.locator('.normalization-delta').innerText()).includes('+70.0 pp'),'CANONICAL_RAW_DELTA_IS_DISPLAY_ONLY');
    await page.getByRole('tab',{name:'题目与阈值',exact:true}).click();
    check((await page.locator('.adjustment-row').allTextContents()).join('|').includes('-1.0 pp'),'NEGATIVE_THRESHOLD_ADJUSTMENT_RETAINS_SIGN');
    check(await page.locator('.adjustment-track .negative').count()===1,'NEGATIVE_ADJUSTMENT_BAR_LEFT_OF_ZERO');
    check(await page.locator('.adjustment-row').count()===5,'HISTORICAL_COMPONENT_NOT_SILENTLY_OMITTED');
    await page.getByRole('tab',{name:'标识符映射',exact:true}).click();
    await page.getByRole('textbox',{name:'搜索标识符映射',exact:true}).fill('does_not_exist');
    await page.getByText('暂无匹配的标识符映射',{exact:true}).waitFor();
    checks.push('IDENTIFIER_SEARCH_EMPTY_STATE');
    await page.getByRole('textbox',{name:'搜索标识符映射',exact:true}).fill('items');
    check(await page.getByRole('tabpanel',{name:'标识符映射',exact:true}).locator('.el-table__row').count()===1,'IDENTIFIER_SEARCH_MATCHES_B_SIDE');
    await page.getByRole('tab',{name:'证据与源码',exact:true}).click();
    await page.locator('.mobile-evidence-item').filter({hasText:'UI_ONLY token evidence'}).click();
    check((await page.locator('.code-block').evaluateAll(nodes=>nodes.map(n=>n.scrollTop))).every(value=>value>0),'EVIDENCE_SCROLLS_LONG_CODE_TO_MATCHED_LINES');
    await page.getByText('自动换行',{exact:true}).click();
    check(await page.getByRole('checkbox',{name:'自动换行',exact:true}).isChecked(),'SOURCE_WRAP_CHECKBOX_STATE');
    check(await page.locator('.code-compare.wrapped').count()===1,'SOURCE_WRAP_TOGGLE');
    await page.getByText('上下',{exact:true}).click();
    check(await page.locator('.code-compare.stacked').count()===1,'SOURCE_STACK_LAYOUT_TOGGLE');
    for(const width of [1440,768,390,320]) {
      await page.setViewportSize({width,height:900});
      check(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),'DETAIL_NO_OVERFLOW_'+width);
    }
    missing=true;
    await page.reload();
    await page.getByRole('heading',{name:'分数与阈值',exact:true}).waitFor();
    check(await page.locator('.score-analysis-primary .track-point').count()===0,'MISSING_SCORE_HAS_NO_FAKE_ZERO_POINT');
    check(await page.locator('.score-analysis-primary .track-threshold').count()===0,'MISSING_THRESHOLD_HAS_NO_FAKE_ZERO_MARKER');
    check(await page.locator('.dimension-track.unavailable').count()===3,'MISSING_DIMENSIONS_ARE_EXPLICIT');
    check((await page.locator('.normalization-delta strong').innerText())==='-','MISSING_CANONICAL_HAS_NO_INVENTED_DELTA');
    check(errors.length===0,'NO_BROWSER_RUNTIME_ERRORS');
  } finally {
    await page.unroute(origin+'/api/tasks/9900**');
    await page.unroute(origin+'/api/results/99001**');
    page.off('pageerror',errorListener);
    await page.setViewportSize({width:1440,height:1000});
    await page.goto(origin+'/dashboard');
  }
  return {kind:'INTERCEPTED_UI_ONLY_NOT_BENCHMARK',checks,errors,databaseWrites:0,mockRoutesRemoved:true};
}
