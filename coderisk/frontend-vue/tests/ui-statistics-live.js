// Six explicitly synthetic, self-authored snippets. Not a functional dataset or benchmark.
async (page) => {
  const origin=await page.evaluate(()=>location.origin);
  if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin))throw new Error('Local isolated test application required');
  const out='output/playwright/statistical-views-20261016';
  const checks=[],errors=[];
  const onError=error=>errors.push(error.message);page.on('pageerror',onError);
  const check=(ok,name)=>{if(!ok)throw new Error(name);checks.push(name)};
  const chart=key=>page.locator(`figure[data-chart="${key}"][data-ready="true"]`);
  try {
    await page.setViewportSize({width:1440,height:1100});
    await page.goto(origin+'/questions/create');
    await page.getByRole('textbox',{name:/题目标题/}).fill('UI_STATS_SELF_AUTHORED · 描述性统计展示 · '+Date.now());
    await page.getByRole('textbox',{name:'题目描述',exact:true}).fill('六份自编合成静态代码用于图表联调。不同聚合操作不视为功能等价，不标注来源关系，不进入研究benchmark，也不执行源码。');
    const [response]=await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/questions')&&r.request().method()==='POST'),page.getByRole('button',{name:'保存题目',exact:true}).click()]);
    const question=(await response.json()).data;
    await page.waitForURL('**/questions');
    await page.goto(origin+'/questions/'+question.id+'/submissions');
    const names=['StatsSum','StatsRename','StatsSorted','StatsMaximum','StatsCount','StatsPrefix'];
    for(const [index,name] of names.entries()){
      await page.getByRole('textbox',{name:'学生标识',exact:true}).fill('UI_STATS_SELF_'+index);
      await page.locator('input[type="file"]').setInputFiles('coderisk/frontend-vue/tests/fixtures/statistics/'+name+'.py');
      await page.getByRole('button',{name:'保存提交',exact:true}).click();
      await page.getByRole('cell',{name:name+'.py',exact:true}).waitFor();
    }
    checks.push('SIX_SELF_AUTHORED_SYNTHETIC_UPLOADS');
    await page.getByRole('button',{name:'开始检测',exact:true}).click();
    await page.waitForURL(/\/tasks\/\d+\/results/);
    const taskUrl=page.url();
    await page.getByRole('heading',{name:'任务状态：FINISHED',exact:true}).waitFor({timeout:90000});
    const taskId=Number(taskUrl.match(/\/tasks\/(\d+)/)[1]);
    const rows=(await (await page.request.get(origin+'/api/tasks/'+taskId+'/results')).json()).data.items;
    check(rows.length===15,'FIFTEEN_REAL_STATIC_ANALYSIS_RESULTS');
    await page.getByText('分析',{exact:true}).click();
    await chart('score-histogram').locator('.chart-surface svg').waitFor();
    check(await chart('score-histogram').locator('.chart-surface svg text').count()>3,'REAL_HISTOGRAM_NONBLANK');
    await page.waitForLoadState('networkidle');
    await page.screenshot({path:out+'/live-histogram.png',fullPage:true,animations:'disabled'});
    await page.getByText('规范化对照',{exact:true}).click();
    await chart('normalization-scatter').locator('.chart-surface svg').waitFor();
    check(await chart('normalization-scatter').locator('.chart-surface svg path').count()>3,'REAL_SCATTER_NONBLANK');
    await page.screenshot({path:out+'/live-normalization.png',fullPage:true,animations:'disabled'});
    await page.getByText('多维结构',{exact:true}).click();
    await chart('dimension-heatmap').locator('.chart-surface svg').waitFor();
    await chart('dimension-boxplot').locator('.chart-surface svg').waitFor();
    check(await chart('dimension-heatmap').locator('.chart-surface svg text').count()>15,'REAL_HEATMAP_NONBLANK');
    check(await chart('dimension-boxplot').locator('.chart-surface svg path').count()>3,'REAL_BOXPLOT_NONBLANK');
    await page.screenshot({path:out+'/live-dimensions.png',fullPage:true,animations:'disabled'});
    await page.setViewportSize({width:390,height:844});
    await page.getByText('规范化对照',{exact:true}).click();
    await chart('normalization-scatter').locator('.chart-surface svg').waitFor();
    await page.waitForLoadState('networkidle');
    check(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),'LIVE_MOBILE_NO_PAGE_OVERFLOW');
    await page.screenshot({path:out+'/live-mobile.png',fullPage:true,animations:'disabled'});
    check((await page.locator('.project-credit').innerText()).includes('魏语石'),'LIVE_OWNER_CREDIT');
    check(errors.length===0,'NO_BROWSER_RUNTIME_ERRORS');
    await page.setViewportSize({width:1440,height:1100});
    return {kind:'SELF_AUTHORED_SYNTHETIC_UI_ONLY_NOT_BENCHMARK',questionId:question.id,taskId,taskUrl,pairs:rows.length,checks,errors,sourceExecution:false};
  } finally {page.off('pageerror',onError)}
}
