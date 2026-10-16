async (page) => {
  const origin=await page.evaluate(()=>location.origin);
  const checks=[],errors=[];const onError=error=>errors.push(error.message);page.on('pageerror',onError);
  const check=(ok,label)=>{if(!ok)throw new Error(label);checks.push(label)};
  const fulfill=(route,data)=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({success:true,code:'OK',data})});
  const latest=(await (await page.request.get(origin+'/api/tasks/recent')).json()).data;
  const task=latest.find(row=>row.taskName.startsWith('UI_STATS_SELF_AUTHORED')&&row.status==='FINISHED');
  const single=latest.find(row=>row.taskName.startsWith('UI_SELF_AUTHORED')&&row.totalPairs===1&&row.status==='FINISHED');
  if(!task||!single)throw new Error('Self-authored isolated task fixtures required');
  const chart=key=>page.locator(`figure[data-chart="${key}"][data-ready="true"] .chart-surface`);
  const metrics=[{method:'UI_FIXED',sampleCount:12,f1:.5,recall:.8,precision:.4,falsePositiveRate:.4,naturalSimilarityFpr:.4},{method:'UI_DYNAMIC',sampleCount:12,f1:null,recall:.6,precision:.7,falsePositiveRate:.1,naturalSimilarityFpr:null}];
  await page.setViewportSize({width:1440,height:1000});
  try {
    await page.goto(origin+'/tasks/'+task.id+'/results?view=analysis&plot=dimensions');
    await chart('dimension-heatmap').locator('svg').waitFor();
    check((await page.locator('.statistical-analysis').innerText()).includes('逐对多维指标热力图'),'DIRECT_ANALYSIS_URL');
    await page.reload();await chart('dimension-heatmap').locator('svg').waitFor();checks.push('ANALYSIS_VIEW_SURVIVES_RELOAD');
    const cell=chart('dimension-heatmap').locator('svg path[stroke="#ffffff"][stroke-width="3"]').first();
    await cell.click({position:{x:8,y:8}});await page.waitForURL(/\/results\/\d+$/);
    await page.getByRole('heading',{name:'结果证据',exact:true}).waitFor();checks.push('HEATMAP_CELL_DRILLS_INTO_REAL_EVIDENCE');
    await page.goto(origin+'/tasks/'+single.id+'/results?view=analysis&plot=dimensions');
    await page.getByText('各分量有效值不足4个，暂不绘制箱线图',{exact:true}).waitFor();
    check(await page.locator('[data-chart="dimension-boxplot"]').count()===0,'SINGLETON_BOX_NOT_FABRICATED');
    await page.route(origin+'/api/experiments/latest',route=>fulfill(route,{runId:'UI_ONLY_EXPERIMENT_FIXTURE',summary:{run:{runId:'UI_ONLY_EXPERIMENT_FIXTURE',datasetVersion:'SYNTHETIC_UI_ONLY',caseCount:12,validationCaseCount:6,testCaseCount:6},validationCalibration:{selectedFixedThreshold:null},E1_fixedVsDynamic:metrics,E2_rawVsCanonical:{meanRawTokenSimilarity:.3,meanCanonicalTokenSimilarity:.8},E3_fusion:metrics,E4_ablation:metrics,E5_failureAnalysis:{failureCount:0,borderlineCount:1}}}));
    await page.goto(origin+'/experiments');
    await chart('experiment-method-comparison').locator('svg').waitFor();
    check((await chart('experiment-method-comparison').getAttribute('aria-label')).includes('1/2方法有有效值'),'EXPERIMENT_NULL_METRIC_NOT_ZERO');
    check((await chart('experiment-method-comparison').locator('svg').textContent()).includes('n=12'),'METHOD_CHART_DENOMINATORS_VISIBLE');
    await page.getByText('消融',{exact:true}).click();
    await page.locator('.comparison-controls .el-select__wrapper').click();await page.getByRole('option',{name:'NaturalSimilar FPR',exact:true}).click();
    await page.getByRole('option',{name:'NaturalSimilar FPR',exact:true}).waitFor({state:'hidden'});
    check((await chart('experiment-method-comparison').getAttribute('aria-label')).includes('NaturalSimilar FPR'),'ABLATION_AND_METRIC_CONTROLS');
    for(const width of [1440,768,390,320]){
      await page.setViewportSize({width,height:900});
      await page.waitForFunction(()=>[...document.querySelectorAll('.chart-surface')].filter(el=>el.clientWidth>0).every(el=>{const svg=el.querySelector('svg');return !svg||Math.abs(Number(svg.getAttribute('width'))-el.clientWidth)<2}));
      const layout=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,pageWidth:document.documentElement.scrollWidth,viewport:innerWidth,elements:[...document.querySelectorAll('main *')].filter(el=>el.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(el=>({tag:el.tagName,classes:String(el.className).slice(0,100),width:Math.round(el.getBoundingClientRect().width)})),tables:[...document.querySelectorAll('.el-table')].map(el=>({width:el.clientWidth,scroll:el.scrollWidth,overflow:getComputedStyle(el).overflowX,parentWidth:el.parentElement?.clientWidth,parentOverflow:el.parentElement&&getComputedStyle(el.parentElement).overflowX}))}));
      check(!layout.overflow,'EXPERIMENT_NO_PAGE_OVERFLOW_'+width+(layout.overflow?JSON.stringify(layout):''));
    }
    await page.unroute(origin+'/api/experiments/latest');
    await page.route(origin+'/api/experiments/latest',route=>route.fulfill({status:404,contentType:'application/json',body:JSON.stringify({success:false,message:'UI_ONLY_NO_EXPERIMENT'})}));
    await page.goto(origin+'/experiments');
    await page.getByText('暂无可用的离线实验产物',{exact:true}).waitFor();
    check(await page.locator('.stat-chart').count()===0,'NO_EXPERIMENT_NO_FAKE_METHOD_CHART');
    check(errors.length===0,'NO_BROWSER_RUNTIME_ERRORS');
  } finally {await page.unroute(origin+'/api/experiments/latest');page.off('pageerror',onError);await page.setViewportSize({width:1440,height:1000});await page.goto(origin+'/tasks/'+task.id+'/results?view=analysis&plot=dimensions')}
  return {kind:'REAL_SELF_AUTHORED_DRILL_AND_INTERCEPTED_EXPERIMENT_UI',checks,errors,existingSelfAuthoredTaskId:task.id,databaseWrites:0};
}
