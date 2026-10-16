# 数据入口修复与融合开发诊断

工作日期：2026-10-10。范围为 Research V4 数据入口、JPlag 对齐和独立开发探针。算法服务、生产公式、权重、阈值及既有公开数据成绩未修改。

## 数据入口行为

- `placeholder` 永远不能进入核心指标。录入助手拒绝以核心资格追加；手工改 JSON 也会被校验器拒绝。
- `source_type=ai_assisted` 或 `case_type=AI_REWRITE` 均要求非空模型、提示词、带时区 ISO-8601 生成时间、`VERIFIED` 人工检查及 `PASSED` 功能检查，才能通过流程核心资格检查。另一种 case_type 不能绕过 AI 来源要求。
- 非合成数据要求非空来源及授权说明；题目信息、身份字段不接受纯空白。
- `--append` 在写入前读取整个当前数据集，检查版本、重复 pair、题目/来源家族/代码哈希跨集合泄漏以及资格。失败时不修改 shard。
- 模板默认资格关闭、人工检查待完成、功能检查未运行。模板值须根据真实记录填写，不把模板默认值当作审核证据。
- Java/Python 同语言且资格通过的 AI-assisted 样例可进入 JPlag；placeholder、跨语言、未核实 AI、预先声明的解析/不支持语法探针仍有明确排除原因。
- 新 JPlag 对齐行保存两侧源码哈希。PICAS 对齐拒绝重复 ID、冲突题目/划分/标签/哈希。旧文件没有源码哈希时 `sourceHashesVerified=false`；不能将仅 ID 对齐称为源码身份已核验。

这里的核心资格是 **seed/开发流程资格**。正式研究仍须 `research_protocol.py` 的真人双人复核、独立性确认、来源家族、预注册划分等门槛；字段声明不是机器认证。旧 Research V4 runner 是开发入口，正式评测参见 [公平评测流程](FAIR_EVALUATION.md)。

Research V4 的 `code_*_sha256` 兼容既有规则：读取 UTF-8 文本、将文件换行归一为 LF，然后对 UTF-8 文本计算 SHA-256。它不是下载包/原始文件字节哈希；原始来源字节哈希应在采集清单另行保留。

## 开发探针及结果

新增 16 对 Java/Python 自有 synthetic 探针，全部 `eligible_for_core_metrics=false`，独立于 Research V4 91 对 seed 和 ConPlag/IR-Plag。写于观察 ConPlag 之后，不是盲测或正式 benchmark；不计入人工标注数。不执行这些代码，只调用生产分析函数处理源码文本。

入口：[diagnose_development_probes.py](../../coderisk/experiment/diagnose_development_probes.py)。最终结果：[开发诊断表](../../coderisk/experiment/evidence/development-fusion-20261010-r2/report.md)，以及同目录 `component_table.csv`、`pair_diagnostics.json`、`manifest.json`。早期 `development-fusion-20261010` 保留为初次运行，不混入最终表。

| 探针 | Raw | Canonical | Mapping | Full | 无规范化同对分数 | Full 差值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Python 纯改名 | 0.030303 | 1.000000 | 1.000000 | 0.806061 | 0.515151 | +0.290910 |
| Java 纯改名 | 0.172414 | 1.000000 | 1.000000 | 0.834483 | 0.586207 | +0.248276 |
| Python 前插无关局部声明 | 0.681818 | 0.275862 | 0.800000 | 0.562320 | 0.795454 | -0.233134 |
| Python 前插无关函数 | 0.708333 | 0.051282 | 0.200000 | 0.361410 | 0.770833 | -0.409423 |
| Java 前插无关函数 | 0.772727 | 0.218750 | 0.333333 | 0.452983 | 0.761364 | -0.308381 |
| Java 相同循环、不同操作 | 0.837838 | 0.837838 | 1.000000 | 0.894595 | 0.918919 | -0.024324 |

7 项预先写在探针中的开发契约全部通过：原样、纯改名、格式变化的 canonical 一致性，以及解析/规范化不支持时 raw 回退。其余 9 项只有观察结果，不能按“契约通过”统计。没有根据这些探针选择参数或生成 Precision/Recall/F1。

### 能说明什么

纯改名得到相同 canonical token，支持目前受限范围内的改名契约。加入无关局部变量会令 `result` 从 `VAR_1` 变成 `VAR_2`；加入前置函数会令 Python 原函数路径从 `MODULE/FUNC_1_1` 变成 `MODULE/FUNC_2_2`，Java 则从 `ROOT/SCOPE_1/SCOPE_1` 变成 `ROOT/SCOPE_1/SCOPE_2`。记录的 token 和绑定证明声明次序/作用域编号会影响表示；不是“变量绑定找错”或“纯改名失败”的证据。

映射分是覆盖/一致性启发式。相同循环中由求和变成计数仍可得到 mapping=1，不能解释为操作或完整语义一致。Java 基础结构摘要同样可能无法区分该探针中的算术操作。这揭示公共结构敏感性，但没有已复核负标签，不能统计为正式误报率。

固定融合分量的差值可逐对重构：`Full - B = .45*(Canonical-B) + .15*(Mapping-B)`，`B=.5*(Raw+AST)`；回退时两侧都用 Raw。低 canonical/mapping 会降低整体分数，高公共结构信号也可能抬高分数。探针没有识别 ConPlag 每个漏检的原因，没有证明提高某项权重会改善效果。

### 下一步技术路线

先扩大自有开发契约到声明插入、遮蔽、独立作用域及函数顺序，明确要承诺哪一种不变性，再设计实验分支比较表示策略。任何算法修复都要保存新版本、回退覆盖及失败样例；已观察 ConPlag 测试不能继续充当未见测试集。真实效果评测须先完成新数据标签与冻结协议。

## 复现

从 `E:\ms` 运行。下列解释器是本机最近回归所用的 Python 3.12 环境；跨机器请换为安装项目依赖的有效解释器。

```powershell
$PY = '.\.tmp\language-venv\Scripts\python.exe'
& $PY coderisk\experiment\diagnose_development_probes.py --help
& $PY coderisk\experiment\diagnose_development_probes.py --output output\fusion-dev-new-run
& $PY coderisk\experiment\validate_research_v4_dataset.py --output-dir output\intake-check-new-run
```

诊断输出必须是不存在的新目录。运行记录含客户端工作日期、真实 UTC 时间、Git 基点、脏工作区标记、算法文件与探针哈希；没有随机过程，`random_seed=null`。

本轮没有 MySQL 实库、JPlag 新原生评分或浏览器主链路复测。MySQL 有效凭据、真实双人复核及正式效果评测仍待完成。
