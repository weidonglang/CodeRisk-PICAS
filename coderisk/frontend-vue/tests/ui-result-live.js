// Read the most recent self-authored UI smoke task; export only that isolated task.
async (page) => {
  const origin=await page.evaluate(()=>location.origin);
  if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin))throw new Error('Local test application required');
  const tasks=(await (await page.request.get(origin+'/api/tasks/recent')).json()).data;
  const task=tasks.find(item=>item.taskName.startsWith('UI_SELF_AUTHORED')&&item.status==='FINISHED');
  if(!task)throw new Error('Run ui-smoke.js against an isolated test database first');
  const rows=(await (await page.request.get(origin+'/api/tasks/'+task.id+'/results')).json()).data.items;
  const result=rows.find(row=>row.submissionAFileName==='UI_SELF_A.py'&&row.submissionBFileName==='UI_SELF_B.py');
  if(!result)throw new Error('Self-authored source pair required');
  const checks=[],errors=[];
  const listener=error=>errors.push(error.message);
  page.on('pageerror',listener);
  const check=(ok,label)=>{if(!ok)throw new Error(label);checks.push(label)};
  await page.setViewportSize({width:1440,height:1000});
  try {
    await page.goto(origin+'/tasks/'+task.id+'/results');
    await page.getByText('图表',{exact:true}).click();
    await page.locator('.pair-chart-name').first().click();
    await page.waitForURL(origin+'/results/'+result.id);
    await page.getByRole('heading',{name:'源码对照',exact:true}).waitFor();
    check((await page.title()).startsWith('结果证据'),'GRAPH_LINK_AND_ROUTE_TITLE');
    const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'任务报告',exact:true}).click()]);
    check(download.suggestedFilename().endsWith('.html'),'DETAIL_TASK_REPORT_REAL_DOWNLOAD');
    await download.saveAs('output/playwright/result-review-20261016/detail-task-report.html');
    await page.locator('.evidence-toolbar .el-select__wrapper').click();
    await page.getByRole('option',{name:'Token 片段',exact:true}).click();
    check(await page.locator('.evidence-table .el-table__row').count()===1,'REAL_EVIDENCE_TYPE_FILTER');
    await page.locator('.evidence-toolbar .el-select__wrapper').click();
    await page.getByRole('option',{name:'全部证据类型',exact:true}).click();
    check(await page.locator('.evidence-table .el-table__row').count()>1,'REAL_EVIDENCE_FILTER_RESET');
    check(errors.length===0,'NO_RUNTIME_ERRORS');
  } finally {page.off('pageerror',listener)}
  return {kind:'SELF_AUTHORED_REAL_API_UI_ONLY_NOT_BENCHMARK',taskId:task.id,resultId:result.id,checks,errors,sourceExecution:false};
}
