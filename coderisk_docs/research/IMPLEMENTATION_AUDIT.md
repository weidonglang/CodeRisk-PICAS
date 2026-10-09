# 实现精准核查：开题第一批

日期：2026-10-10；核查工作树基线 HEAD `9d4e90ff362db590bdb8ea395a0782076ad36f4a`。工作树已经包含未提交的 Python lambda/类绑定边界和 API warning 衔接，不能把 HEAD 旧版本误作当前实现。本轮只核对指定实现/规格差异，不重读或重建架构。

## 功能与真实状态

| 状态 | 功能、源码与函数 | 已有证据 / 具体缺口 |
| --- | --- | --- |
| 已实现且验证（限定用例） | `coderisk/analysis-service-python/app/analyzers/canonicalization.py`：`_PythonIndexer`、`_Scope.resolve`、`_apply_overrides` | `tests/test_formula_and_scope.py` 的嵌套遮蔽；`test_python_scope_boundaries.py` 的 lambda 默认值、变长参数、方法跳过类命名空间。验证了部分绑定，尚无全部支持语法的不变性证明 |
| 已实现且验证（限定用例） | 同文件 `_canonicalize_python`、`_python_scope_limitation` | `test_python_scope_boundaries.py`、`test_python_fallback_api.py`：推导式、global/nonlocal、注解、模式/异常捕获、类动态绑定等整文件 raw-token 回退，空 identifiers，reason 输出至 API |
| 已实现未充分验证 | 同文件 `_canonicalize_java`、`_java_scope_paths`、`_java_parameter_names` | ASCII/花括号启发式，不是 Java 编译器符号表。简单变量/参数/方法重命名通过；字段与局部声明点、无花括号循环、重载、泛型、继承、静态限定成员、反射未形成完整保证 |
| 已实现未充分验证 | 同文件 `build_identifier_mapping` | 规范角色/作用域集合的 coverage × consistency；不是类型、读写或语义匹配。公共结构中可得 mapping=1；不能解释为语义等价 |
| 已实现且验证（工程公式） | `token_similarity.py`：`_fingerprints`、`_sequence_similarity`、`_weighted_similarity` | 自适应 n-gram **集合 Jaccard**，不是 LCS。全项可用时 .20 raw + .20 AST + .45 canonical + .15 mapping；规范化不可用时生产分回退 raw。`test_formula_and_scope.py`、API 回退测试、融合贡献诊断提供证据 |
| 已实现且验证（规则而非效果） | `problem_profile.py`：`build_problem_profile`、`calculate_dynamic_threshold`、`calibrated_risk_score` | 默认 T=clamp(.68-.06D-.04Space+.08Template+.12Natural,.50,.95)，历史分布项=0；展示分 clamp(.5+margin/.40,0,1)。无独立自然相似分布，不支持“误报已下降”效果结论 |
| 已实现且验证（有限实验） | `normalized_ir.py`、`lightweight_summaries.py`；`analyze_token_pair` 的 `PICAS_CROSSLANG` 分支 | V4 受限 Java/Python IR/控制/数据摘要；不是完整 CFG/DFG，生产权重 0，不能当作跨语言语义判定 |
| 已实现未充分验证 | `experiment/run_fair_evaluation.py`、`research_v4_jplag.py`、ConPlag 归档 | 共同集合、验证集选阈值和 JPlag 真实小样例可运行；可信独立双人标签不足。完整融合并非探索 F1 最优；没有新正式重评 |
| 仅设计 | `CANONICALIZATION_SPEC.md` 的表达式交换、局部重排、CanonicalAST/子树指纹/拆分合并；`ALGORITHM_SPEC.md` 的高级指标 | 主规范化实现只做有限绑定 token 替换，不得将规格中的目标/伪代码写成已经实现。加入无关声明可改变编号和 scope path，不是合法改名群作用 |
| 仅设计 / 不支持 | 可信独立分布的 q_p(s)、Direct LLM、PICAS→LLM 混合检测 | 本轮不实现；不能将 q 当作抄袭概率，也不能将 mock 当真实模型结果；候选 Recall@K、成本/许可和测试集冻结均是前置条件 |
| 不支持 | 完整语义等价证明、确认抄袭/AI 来源识别、完整 CFG/DFG/PDG | 架构及接口不提供这些结论；必须保留人工判断 |

路径以上述项目根相对路径表示；测试位于 `coderisk/analysis-service-python/tests/`。稳定的 API/数据库/证据定位/报告主链路本轮不重构。

## 第一批红灯证据

新增 `tests/test_identifier_invariance.py`，在修改算法前实际运行：**18 项中 14 失败、4 通过**，JUnit `output/research-invariance-red.xml`。这些是自有正确性 fixture，不是公开评测数据或算法准确率。

1. Python `def combine(first, *, second=1)` 与 `combine(first=2, second=3)` 一起合法改名：声明/Name 会替换，但 ast.keyword.arg 原文残留，canonical 序列不同。
2. 模块级前向函数引用中的关键字实参同样缺少参数标签解析；不能简单把所有 keyword 文本当作当前局部变量。
3. 函数中 `globals()['value']`、`locals()`、`eval()`、`vars()`、`getattr()`，以及保存 `globals` 别名，仍报告 scope-aware-python。字符串名称不随词法改名，必须回退；不能声称这种程序在合法词法改名下保持语义。
4. Java `int first=value; int value=2;` 的前一个 value 应指字段，当前预声明把它捕获成未来局部变量；分开重命名字段/局部会改变 canonical。
5. Java 不完整花括号返回 lexical-fallback，但 `_lexical_fallback` 仍生成内部 identifiers；生产 API 虽不展示，直接模块调用仍可能误用。应保留 raw tokens + 空 identifiers + located reason。

通过的基本例包括 Java 简单参数/变量/方法改名保留 System.out.println、标准库成员不抹平、插入语句不等同改名、canonical 相同而生产 raw 分量及总分不同。

## 规格与评分的一致性

`FORMULA_SPEC.md` 与当前公式函数一致；原始 SHA-256 为 `562fdb7d68757b811147f9e8d6587e52f8aad01647d002b858329e9ddedf7c20`。本轮不改文件、系数、权重、动态阈值或 IR 权重。修复绑定/收紧回退可能改变个别样本的可用指标及分数，这是正确性变化，不是隐蔽调参；旧运行必须保留原算法源码哈希，不能将其成绩归给新版。

规范化规格里的 Level 2–5 和 AST/表达式/重排示例是设计，不是当前普通生产 canonical 的能力。README 需要明确当前实现、实验性和计划中，并限定 C(g·P)=C(P) 只作用于规范化表示，不能扩大到 PICAS 加权总分。

## 数据与负结果

- ConPlag 固定探索 test 每视图 627 对：原始 full F1 .5543、无 canonical .5985；去模板 .6974/.7352。JPlag 去模板共同集是 625 对，不能拼接成相同评测范围。见 [冻结分解与负结果](../proposal/NEXT_THREE_PROGRESS.md)。这些是历史快照，不作本轮新分数。
- 91 对 Research V4 seed 全 synthetic，不能支撑正式效果；IR-Plag 的发布关系和争议排除、52 对复核材料不等于已完成双审。
- PoolC 30,000 对许可不清隔离；XLCoST 30,893 对仅标题候选/预分词，不是真实改写标签或 raw 源码。见 [多语言接收边界](../proposal/NONJAVA_PUBLIC_INTAKE.md)。
- MySQL 缺有效凭据；只能引用历史 H2 验证，不称实库已验证。

## 精确分阶段提交计划

1. `docs(research): audit implementation and opening-stage claims`：本审计和 README 研究问题/方法、AI 权衡与设计状态；不改生产代码。保留原截图、启动、架构、数据与负结果。
2. `fix(canonical): validate bounded identifier-renaming invariance`：最小绑定修复、明确回退、合法置换生成器/fixture 测试、真实输出、数学范围与规格/开题导航同步。已存在的未提交规范化边界基线及 warning 衔接是本阶段依赖，仅该关联范围进入提交；无关暂存后端/前端/数据采集保持原状态。
3. 后续 P0（本轮不实现）：冻结各分量/两两组合的实验配置；补可信独立标签后比较规则与统计阈值。缺标签的 PR-AUC/FPR/Recall@K 必须标不可计算，禁止从同题不同提交伪造负例。
4. P1/P2：LLM dry-run 对照及可选混合，仅在前置基线/许可/预算成立后另轮执行。

## 验收

- 先红后绿：合法函数/参数/变量改名 C 一致，默认值与遮蔽绑定正确，实参标签回到原始行列。
- 自动置换为固定域上的双射，固定外部/库/API 名称，防止捕获/名称冲突；非法映射及动态语法显式拒绝或 raw 回退。
- 全量 Python、API warning/权重/evidence 回归；必要时后端及前端构建检查。自动样本是开发测试，不增加 formal benchmark 标签。
- 形式化只给有限子集的条件命题/证明草图；有限测试不是所有 Python/Java 程序的机器证明。
- 第一阶段完成状态和测试输出另保存在同目录的研究交付文档，不回填或抹去本节红灯历史。
