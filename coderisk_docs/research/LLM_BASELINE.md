# 独立 LLM 对照实验

2026-10-10 研究阶段 4。此文与实现逐步同步；不是生产功能或模型优越性结论。

## 实施边界

- 只新增隔离实验入口、版本化提示词和严格 JSON Schema。默认 mock/dry-run 无网络、无付费、无源码执行。
- 真实模型响应由操作者在获得许可后自行运行并按协议离线导入；本工具不提供在线 SDK，不读取密钥，也不自动调用外部服务。离线导入不能验证外部调用是否真的发生，须核验提供方记录。
- Direct LLM 只收到相同题目、模板、语言与编号源码，不收到关系标签、split、case_type 或 PICAS 分数。不能把模型输出风险线索当作抄袭概率或最终关系判断。
- mock 只输出 ABSTAIN/null，不计算模型准确率；import 才能形成真实响应的可用分数，仍受授权、预算、验证集选参和正式数据门禁约束。
- JPlag 与 PICAS 必须按当前源码 hash、题目、split 对齐。缺失不是零，覆盖不足不能包装成公平全量比较。JPlag 不使用题目文本；共享模板处理不同的 case 不进入三方同背景主表。

## 已实现与未验证

已新增 `experiment/llm_baseline.py`、配置、版本化提示词、Schema 与测试；生产 API、数据库及评分不改。授权、请求身份、费用/Token 上限、缓存完整性、重复运行、原文引文核对、validation-only 选阈值已实现。真实模型效果、延迟、费用、稳定性未测，测试伪响应不算真实模型数据。

源码内指令可能干扰模型。把源码作为不可信数据、禁止执行、要求结构和证据只能降低流程风险，不是 prompt injection 的完备防御。结论性措辞的词法拒绝不能穷尽所有表达，仍须人工审阅。

## 运行协议

仓库根目录 PowerShell，先 `--help`；其他机器替换 `$Python`：

```powershell
$Python = (Resolve-Path ./.tmp/language-venv/Scripts/python.exe).Path
& $Python coderisk/experiment/llm_baseline.py --help
& $Python coderisk/experiment/llm_baseline.py --output output/llm-mock-new --allow-development
& $Python coderisk/experiment/llm_baseline.py --output output/llm-dry-new --mode dry-run --allow-development --export-prompts
& $Python coderisk/experiment/research_v4_jplag.py --output-dir output/jplag-new --execute
& $Python coderisk/experiment/llm_baseline.py --output output/llm-aligned-new --allow-development --jplag-dir output/jplag-new
```

默认正式模式拒绝当前 seed，必须显式 `--allow-development`。结果目录不可覆盖。`--export-prompts` 才写出含源码的 `prompts.jsonl`，默认仅请求 hash。真实数据需要 `llm_authorization={authorized:true, scope:"LOCAL_EXPORT_AND_IMPORT", reference:..., reviewer_id:...}`；公开许可证不等于上传许可，此声明也不代替远程使用授权。

获得许可后自行运行模型，将配置复制到新文件，填写精确版本/参数；响应按 `responses_template.jsonl` 填写 latencyMs、costUsd、usage、output，不能捏造。请求 hash 绑定背景、源码、提示词、Schema、模型、参数和 repetition，任何改变均需重建请求。导入命令不发网络请求：

```powershell
& $Python coderisk/experiment/llm_baseline.py --config path/to/frozen-real-config.json --output output/llm-import-new --mode import --responses path/to/authorized-responses.jsonl --cache-dir output/llm-cache --allow-development
```

默认 `maxCostUsd=0`。导入已支付响应时需在新配置明确设置历史费用上限；预检包含无效输出的已声明费用/Token，超额拒绝且不写缓存。相同请求只计一次，新增网络调用/费用始终 0。未知请求、重复 JSONL 身份、篡改缓存均拒绝。费用真实性要由提供方凭证核验；非法包装元数据可能无法计量，不得称为可靠费用测量。

正式评测还需注册配置、提示词、运行时 Schema、载入后数据 hash，满足既有标签/来源/分集门禁。同题不同提交不自动是独立负例；调提示词或模型后不能反复窥探冻结 test。

## 比较与输出

- `scores.jsonl` / `requests.jsonl` / `model_outputs.jsonl`：逐对分量、降级、请求和逐次输出；`selection.json`：仅 validation 选工作点。
- `metrics.csv` / `coverage.csv`：指标与覆盖；`stability.csv` / `repetitions.csv`：重复次数、均值、极差、标准差及声明延迟/费用。
- `failures.csv`：不可评分和 FP/FN；`borderline.csv`：冻结工作点 ±0.05（展示约定）；`REPORT.md`：汇总；`run_manifest.json`：版本、配置/数据/源码 hash、Git 状态、种子、时刻和费用。
- 至少两次有效非弃答响应才求均值；缺失/无效/弃答不是负例。引文一致只验证定位，不验证语义推理或派生关系。
- `COMMON_THREE` 是三者同源码共同集合；`COMMON_PICAS_JPLAG` 是两方共同集合；`AVAILABLE_DIAGNOSTIC` 覆盖不同，不能横比优劣。当前 JPlag 原始适配不能统一去模板，登记共同模板样本不进入三方主表。JPlag 不利用题目文本，这一方法差异须报告。

## 实际验证

2026-10-10：新测试 27 项通过，工作树全量 Python 404 项通过（含其他未提交任务），1 条既有依赖 warning。费用漏计/重复缓存写入两个红测先失败后修复，伪响应只用于测试契约。

mock 与 dry-run 实跑：91 输入、75 分析（35 validation/40 test）、16 排除；225 计划请求，真实模型响应/LLM 可评分/正式资格/新增网络调用/费用均 0。LLM 指标 N/A，不支持真实模型或混合收益结论。

JPlag 6.2.0 Java/Python 实际 exit 0，72 对匹配；底层枚举比较不全部计入指标。共同 test 38 对：PICAS_FIXED F1=0.7692/FPR=0.6250，PICAS_RULE_DYNAMIC F1=0.6667/FPR=0.2500，JPlag F1=0.7826/FPR=0.3750。规则动态阈值有召回损失，完整融合不是最好；全部是 synthetic 流程观察，非可信 benchmark。

受控归档见 [阶段 4 证据](../../coderisk/experiment/evidence/llm-baseline-20261010/README.md)。真实模型稳定性未测，MySQL 仍待凭据；后续需授权数据、人工关系复核、冻结评测与模型提供方记录。
