# 阶段 4：离线 LLM 协议与 JPlag 对齐证据

2026-10-10，全部 seed 数据为 synthetic，正式资格 0。没有真实 LLM 推理、网络请求或新增费用，没有真人标签补造。

## 实际执行

```powershell
$Python = (Resolve-Path ./.tmp/language-venv/Scripts/python.exe).Path
& $Python coderisk/experiment/research_v4_jplag.py --output-dir output/research-llm-jplag-20261010 --execute
& $Python coderisk/experiment/llm_baseline.py --output output/research-llm-mock-final-20261010 --allow-development --jplag-dir output/research-llm-jplag-20261010
& $Python coderisk/experiment/llm_baseline.py --output output/research-llm-dry-final-20261010 --mode dry-run --allow-development
```

- `mock/`：实际 91 输入/75 分析、225 请求，mock 不评分；三方共同表 N=0，两方共同 test N=38。未知或无效 LLM 输出不当零分。
- `dry-run/`：实际无调用的计划执行记录。
- `jplag/`：Java/Python 退出码 0，版本 6.2.0、72 对对齐，jar hash 在 manifest；原始源码及原生枚举 CSV 保留本机 output，不全复制进 Git。
- `llm-stage4-gates-red.xml`：2 项失败，复现错误输出未计声明费用/重复缓存创建；`llm-stage4-final-contract.xml`：修复与最终输出补充后 27 项通过。
- `llm-stage4-full.xml`：完整工作树 404 项通过、既有 warning 1；含其他未提交任务，不等于本阶段 clean HEAD 的测试数。
- `llm-stage4-isolated.xml`：从 HEAD+本阶段补丁导出源码树 `0c8d4e44d79b46e555e77a4599203b6da5dd7bd9`，独立 27 项通过；未依赖其他未提交实现。

源码/配置/数据/prompt/Schema hash、Git HEAD 与 dirty 状态在 run_manifest 中。HEAD 是当时基础版本，不能代替工作树 hash。Schema 可校验的定位不证明语义推理或关系成立；离线导入无法外部证明模型真的被调用。

完整边界和命令见 [LLM_BASELINE](../../../../coderisk_docs/research/LLM_BASELINE.md)。生产权重不改，MySQL 无新增实库验证。
