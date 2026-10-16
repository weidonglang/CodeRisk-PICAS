// A failed local chart-module request must not remove data or fabricate a graph.
async (page) => {
  const origin=await page.evaluate(()=>location.origin),checks=[];
  const tasks=(await (await page.request.get(origin+'/api/tasks/recent')).json()).data;
  const task=tasks.find(row=>row.taskName.startsWith('UI_STATS_SELF_AUTHORED')&&row.status==='FINISHED');
  if(!task)throw new Error('Run ui-statistics-live.js in isolated data first');
  let blocked=0;
  const pattern='**/src/charts/echartsRuntime.ts*';
  await page.route(pattern,route=>{blocked++;return route.abort('failed')});
  try {
    await page.goto(origin+'/tasks/'+task.id+'/results?view=analysis');
    await page.getByText('图表暂不可用，数值明细仍可查看',{exact:true}).waitFor();
    if(!blocked)throw new Error('Module interception did not exercise fallback');checks.push('MODULE_FAILURE_HAS_EXPLICIT_FALLBACK');
    await page.getByText('数值明细 · 分量统计与原始代码对',{exact:true}).click();
    if(await page.locator('.analysis-numbers tbody tr').count()!==19)throw new Error('Numeric data lost');checks.push('NUMERIC_DATA_REMAINS_AVAILABLE');
    await page.unroute(pattern);
    await page.getByRole('button',{name:'刷新页面重试图表',exact:true}).click();
    await page.locator('[data-chart="score-histogram"][data-ready="true"] .chart-surface svg').waitFor();
    checks.push('EXPLICIT_RELOAD_RECOVERS_CHART');
    if(!page.url().includes('view=analysis'))throw new Error('Analysis link lost');checks.push('RECOVERY_RETAINS_ANALYSIS_VIEW');
  } finally {await page.unroute(pattern)}
  return {kind:'LOCAL_CHART_MODULE_FAILURE_TEST',checks,databaseWrites:0};
}
