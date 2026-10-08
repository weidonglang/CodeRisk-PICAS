# 版本、模板与短代码开发验证

这里保存八个自行编写的合成开发案例及实际分析器结果，覆盖 Java/Python/C/HTML。不是新增真实作业、可信独立解答或正式检测成绩。全部关系标签 UNKNOWN/UNCERTAIN，正式指标资格为零。

`run_manifest.json` 保存实际 UTC 时间、Python 版本和实现指纹，`case_summary.jsonl` 保存摘要，各案例 JSON 包含请求、完整结果以及无版本/模板声明的基线分数和阈值。八例新增复核背景后，生产分数与阈值均保持不变。

短 Python 计算器同代码相似分为 1.0，但提示可区分依据不足；Python 旧式 print 与新式 print 的低分仍附解析/版本限制，不认定独立；Python 2/3 除法声明差异、Java/C 版本声明、HTML/输入共同模板均有复核上下文。模板只在原始 Token 精确匹配时计算覆盖，任一侧没有非模板内容时诊断相似度保持 null。

```powershell
python coderisk/experiment/run_context_checks.py --output coderisk/experiment/evidence/review-context-replay
```

新输出目录必须不存在。实现和规则边界见 [说明](../../../../coderisk_docs/proposal/VERSION_AND_NATURAL_SIMILARITY.md)。

另有 `live_e2e_summary.json`，来自真实 Spring Boot/Python 服务及隔离的临时 H2 内存数据库。合成 Java 计算器提交声明版本 8/17，登记多行共同模板后，两侧各剩余 7 个 Token，原分数仍为 1.0，并保存“可区分依据不足”提示；HTML 报告包含相同上下文。该联调同样没有真实标签、没有执行提交源码，正式指标资格为零。实际结果页经 Playwright 截图和视觉检查。该摘要不属于八案例运行指纹清单，不据此推断检测准确率。
