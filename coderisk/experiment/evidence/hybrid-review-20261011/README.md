# 阶段 5：候选召回门禁证据

2026-10-11，隔离离线研究流程，无生产评分改动、远程调用或新增费用。

```powershell
$Python = (Resolve-Path ./.tmp/language-venv/Scripts/python.exe).Path
& $Python coderisk/experiment/hybrid_review.py --output output/research-hybrid-mock-20261011 --allow-development
& $Python coderisk/experiment/hybrid_review.py --output output/research-hybrid-import-gate-20261011 --allow-development --mode import
```

- `mock/` 是实际 seed 流程：91 synthetic 输入/75 分析/16 排除；无完整 query pool，BLOCKED_INCOMPLETE_QUERY_POOLS，Recall@K N/A，K=null、选中/真实响应/调用/费用为 0。
- `import-gate/` 是同数据 import 的阻断记录，development 不能使当前样本获得真实混合资格。
- `hybrid-stage5-gates-red.xml` 1 个红测复现未知 selected pair 未检查问题；`hybrid-stage5-focused-final.xml` 修复后 27 项通过。
- `hybrid-stage5-full.xml` 当前工作树 431 项 Python 通过、既有 warning 1，含其他未提交任务，不等于 clean HEAD 的数量。
- `hybrid-stage5-isolated.xml`：临时源码树 `5e4139687d61cfb9eeb3290f04b2dee8d6227ddf` 独立运行阶段 4–5 新测试 54 项通过，不依赖其他 pending 实现。
- 本轮 `mvn test` H2 19 项通过、`npm run build` 类型检查/构建成功；真实 XML 与 `verification.json` 记录 sandbox 拒绝后的成功重试。浏览器未重跑，MySQL 仍待凭据。
- 测试专用完整候选池 mock 6 对/18 请求及 MOCK_TEST_ONLY 批准只在契约测试中，不是新增人工数据或模型结果。

版本、源码/配置/数据 hash、费用、正式阻断原因在 manifest；HEAD 不代表整个 dirty 工作树。真实混合收益未验证，数据池及真实授权 Direct LLM 基线仍待补。详见 [研究说明](../../../../coderisk_docs/research/HYBRID_DETECTION.md)。
