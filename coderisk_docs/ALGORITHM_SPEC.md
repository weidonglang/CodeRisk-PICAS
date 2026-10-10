# ALGORITHM_SPEC.md

> 2026-10-10 阶段 4：隔离离线 Direct LLM baseline 已实现（mock/dry-run/授权导入），不调用网络，不改变生产公式；真实模型未运行，下方历史“计划中”按当时状态理解。提示词、Schema、预算、缓存、validation-only 对照及局限见 [LLM 实验协议](research/LLM_BASELINE.md)。

> 2026-10-10 后续研究阶段 3：q_p(s) 的隔离实验入口已实现，采用现有 production S 的可信独立参考上尾、质量门禁与规则冷启动回退；没有改本文生产融合/阈值。参考池当前空、效果未验证，不等于下文广义结构方法已完成。两种参考协议及已实现/未验证边界见 [统计研究说明](research/NATURAL_SIMILARITY_CALIBRATION.md)；LLM 对照仍计划中，历史负结果不变。

> 2026-10-10 开题研究校正：本文的广义结构变换、群/轨道及高级指标描述应按设计目标理解；已验证的群模型仅是固定名称域、保护外部名称、捕获规避的统一标识符置换，作用对象仅完整 canonical token 序列，不是 PICAS 加权分。直接函数 keyword 绑定、动态访问回退和 Java 声明点本次修复，生产公式未调整；统计校准/LLM 仍计划中。源码/测试对照见 [精准审计](research/IMPLEMENTATION_AUDIT.md) 与 [条件定义](research/GROUP_ACTION_INVARIANCE.md)。历史 ConPlag Full 并非最高 F1，不改写负结果。

> 2026-10-09 本轮增量：新增现行融合的代数贡献诊断：读取冻结分数和阈值，不拟合、不重评分。raw/AST/canonical 使用 n-gram 集合 Jaccard；不能将名为 sequence_similarity 的函数解释为 LCS 或语义检测。生产权重、阈值与分数兼容字段不变。 依据与边界见 [前三项推进记录](proposal/NEXT_THREE_PROGRESS.md)。

> 2026-10-09 新增独立的 [版本/自然相似复核上下文](proposal/VERSION_AND_NATURAL_SIMILARITY.md)，不进入评分权重：登记模板的精确原始 Token 匹配，8 Token 以下片段忽略，按下标去重；剩余 Token 值集合诊断无顺序信息、空侧保持 null。短有效代码及版本/解析限制触发依据不足/背景复核提示；门槛未校准，不决定独立/派生关系。生产分数、题目画像和阈值公式保持原逻辑。

> 2026-10-08 C/HTML 增量：C 使用 Tree-sitter 语法树和局部作用域规范化；宏/typedef/extern/复杂原型等明确降级。HTML 使用标签/属性结构序列与保留文本、属性值的规范化，默认融合权重 0.25/0.30/0.45，映射权重 0；固定阈值 0.85 可配置但未经标注数据校准。公式 `HTML_STRUCTURE_FIXED_V1` 不应用算法题画像，降级时仅词法评分。空或仅注释源码相似度为 0。详见 [多语言记录](proposal/MULTILANGUAGE_PROGRESS.md)；Java/Python 正常输入的融合与题目阈值配置沿用原版本。

> 2026-10-08 正确性修订见 [核心修复记录](proposal/CORE_REVIEW.md)：Java注释与字面量、局部绑定、Python列偏移、映射统计和证据范围已修复，融合系数与题目阈值规则不变。当前“规范化”限定为已实现和已测试的标识符作用域处理，不代表以下设计中的全部重排、交换或语义能力已实现。

> 本文件定义 CodeRisk / PICAS 的算法总设计。它用于指导 `analysis-service-python`、后端结果存储、前端证据展示、实验脚本、论文方法章节和专利技术交底。任何相似度算法新增或修改，都必须先检查是否与本文件一致。



## 0.2 数学表述边界

本文档中的“置换不变”主要指面向标识符重命名、局部无依赖重排和可交换表达式规范化的工程性规范表示。它借鉴“不变量”和“变换下保持稳定”的思想，但不宣称构成完整的群论证明。

禁止在论文、专利、README 或答辩中宣称：

```text
本系统基于群论证明两个程序等价。
本系统可以完整判断代码语义等价。
本系统可以完整识别所有跨语言改写。
```

推荐表述：

```text
本文构建面向标识符重命名、局部无依赖重排和可交换表达式的规范化表示，使代码表示在若干表层变换下保持稳定，从而提升代码相似风险检测的鲁棒性。
```

---

## 1. 算法定位

### 1.1 方法名称

```text
PICAS: Problem-aware Invariant Code Similarity Analysis
```

中文名称：

```text
题目感知与置换不变代码相似风险分析方法
```

### 1.2 核心目标

PICAS 不直接判断“抄袭成立”，而是在特定题目背景下输出：

```text
多维相似度指标 + 题目动态阈值 + 综合风险分数 + 风险等级 + 结构化证据 + 人工复核建议
```

系统关注的问题不是简单的“两个代码像不像”，而是：

```text
在这道题的自然相似风险、模板化风险和解法空间背景下，这两份代码的相似程度是否异常。
```

### 1.3 算法主线

整体算法由 6 个阶段组成：

```text
Input
→ Code Preprocessing
→ Code Parsing and Feature Extraction
→ Permutation-Invariant Canonicalization
→ Multi-dimensional Similarity Calculation
→ Problem-aware Dynamic Thresholding
→ Risk Level and Evidence Generation
→ Output Report
```

---

## 2. 输入与输出定义

### 2.1 输入对象

一次检测任务至少包含：

```text
Question Q
Submissions S = {s1, s2, ..., sn}
Optional Reference Solutions R = {r1, r2, ..., rm}
DetectionConfig C
```

### 2.2 Question Q

题目对象包含：

```text
question_id
question_title
question_description
input_format
output_format
constraints
sample_input
sample_output
time_limit
memory_limit
tags
optional_reference_solutions
optional_historical_submissions
```

### 2.3 Submission s

代码提交对象包含：

```text
submission_id
question_id
student_id 或 anonymous_id
language
file_name
raw_code
clean_code
parser_status
created_time
```

### 2.4 DetectionConfig C

检测配置包含：

```text
supported_languages
pairing_strategy
similarity_metrics_enabled
problem_aware_threshold_enabled
canonicalization_enabled
cross_language_ir_enabled
evidence_level
report_format
```

### 2.5 输出对象

每对代码输出一个 `PairRiskResult`：

```text
result_id
submission_a_id
submission_b_id
language_pair
metrics
problem_scores
weighted_similarity_score
dynamic_threshold
risk_margin
calibrated_risk_score
risk_level
exceed_threshold
margin_scale
evidence_list
review_suggestion
formula_version
algorithm_version
created_time
```

---

## 3. 总体算法流程

### 3.1 主流程伪代码

```text
function AnalyzeTask(question Q, submissions S, config C):
    problemProfile = AnalyzeProblem(Q)
    parsedSubmissions = []

    for each submission s in S:
        clean = PreprocessCode(s.raw_code, s.language)
        parsed = ParseCode(clean, s.language)
        features = ExtractCodeFeatures(parsed, s.language)
        canonical = CanonicalizeCode(parsed, features, C)
        ir = BuildLanguageIndependentIR(parsed, canonical, s.language, C)
        parsedSubmissions.add(CodeProfile(s, clean, parsed, features, canonical, ir))

    results = []
    for each pair (a, b) in Pairing(parsedSubmissions, C):
        metrics = ComputeSimilarityMetrics(a, b, problemProfile, C)
        threshold = ComputeDynamicThreshold(problemProfile, metrics, C)
        risk = ComputeFinalRisk(metrics, problemProfile, threshold, C)
        evidences = GenerateEvidence(a, b, metrics, problemProfile, risk, C)
        level = AssignRiskLevel(risk, threshold, problemProfile)
        results.add(PairRiskResult(a, b, metrics, threshold, risk, level, evidences))

    return TaskReport(problemProfile, results)
```

### 3.2 算法版本化要求

所有结果必须保存算法版本，避免实验不可复现：

```text
algorithm_version = "picas-v0.1.0"
canonicalization_version = "canon-v0.1.0"
problem_scoring_version = "pas-v0.1.0"
metric_config_hash = SHA256(metric_config_json)
```

---

## 4. 代码预处理算法

### 4.1 目标

代码预处理用于减少无关差异，但不得破坏语义结构。

### 4.2 处理内容

必须处理：

```text
统一换行符
统一编码
删除或保留注释的双版本输出
去除无意义空白
保留原始行号映射
识别文件语言
识别解析失败原因
```

### 4.3 双视图设计

每份代码必须保留两个视图：

```text
RawView：原始代码，用于前端展示和证据定位
CleanView：清洗代码，用于 token、AST 和结构分析
```

行号映射必须保存：

```text
raw_line -> clean_line
clean_line -> raw_line
```

原因：证据输出需要回到用户可见的原始代码行号。

---

## 5. 解析与基础特征提取

### 5.1 解析器优先级

首期建议：

```text
Java：tree-sitter-java 或 JavaParser
Python：tree-sitter-python 或 Python ast
C：tree-sitter-c，作为增强项
```

跨语言统一能力优先基于 tree-sitter。

### 5.2 解析失败策略

解析失败时不能直接任务失败，应降级：

```text
ParserSuccess：使用 AST + token + structure
ParserPartial：使用 token + lightweight structure
ParserFailed：使用 token + text fingerprint，并标记低可信度
```

结果中必须记录：

```text
parser_status
parser_error_message
metric_reliability
```

### 5.3 基础特征

每份代码提取：

```text
token_sequence
normalized_token_sequence
ast_node_sequence
ast_tree
function_list
variable_list
literal_list
operator_sequence
control_structure_sequence
loop_count
branch_count
function_count
call_sequence
io_pattern
exception_pattern
line_count
cyclomatic_complexity_estimate
```

---

## 6. 多维相似度指标

### 6.1 指标总览

系统至少定义以下指标：

```text
TokenSimilarity
CanonicalTokenSimilarity
ASTStructureSimilarity
CanonicalASTSimilarity
ControlFlowSimilarity
DataDependencySimilarity
OperationSequenceSimilarity
RareFragmentSimilarity
IdentifierMappingSimilarity
IOPatternSimilarity
BugPatternSimilarity
LiteralPatternSimilarity
CrossLanguageIRSimilarity
```

不是所有阶段都必须实现全部指标，但数据结构必须预留。

---

## 7. TokenSimilarity

### 7.1 定义

TokenSimilarity 衡量清洗后 token 序列的相似程度。

### 7.2 推荐实现

V1 实现：

```text
k-gram token fingerprint + Jaccard similarity
```

候选公式：

```text
TokenSimilarity(A, B) = |KGram(A) ∩ KGram(B)| / |KGram(A) ∪ KGram(B)|
```

其中：

```text
KGram(A) = set of token k-grams in A
k 默认取 5，可配置为 3/5/7
```

### 7.3 注意事项

1. 注释和格式不应影响 token 相似度；
2. 关键字和运算符权重应高于普通标识符；
3. 对超短代码应避免 Jaccard 过度放大；
4. 对模板代码应结合 TemplatePenalty 降权。

---

## 8. CanonicalTokenSimilarity

### 8.1 定义

CanonicalTokenSimilarity 使用置换不变规范化后的 token 序列计算相似度。

### 8.2 作用

它用于识别：

```text
变量名替换
函数名替换
参数名替换
局部命名风格变化
```

### 8.3 输出

同时输出变量映射证据：

```text
A.sum -> B.result
A.i -> B.index
A.arr -> B.nums
```

注意：映射关系仅作为结构相似证据，不代表主观抄袭结论。

---

## 9. ASTStructureSimilarity

### 9.1 定义

ASTStructureSimilarity 衡量两份代码的抽象语法树结构相似度。

### 9.2 V1 推荐实现

可先实现轻量版本：

```text
AST node type sequence similarity
AST subtree fingerprint Jaccard
Tree edit distance 的近似方案
```

### 9.3 推荐公式

```text
ASTStructureSimilarity =
0.4 * NodeTypeSequenceSimilarity
+ 0.4 * SubtreeFingerprintSimilarity
+ 0.2 * FunctionStructureSimilarity
```

### 9.4 AST 子树指纹

每个节点生成结构指纹：

```text
fingerprint(node) = hash(node_type + sorted_or_ordered(child_fingerprints))
```

是否排序由节点语义决定：

```text
有序结构：语句块、函数体、参数列表
可交换结构：a+b、a*b、x==y、集合式条件的一部分
```

---

## 10. CanonicalASTSimilarity

### 10.1 定义

在 AST 规范化后计算结构相似度。

### 10.2 与 ASTStructureSimilarity 的区别

```text
ASTStructureSimilarity：保留原始标识符和原始局部结构
CanonicalASTSimilarity：弱化标识符差异、规范化可交换表达式、局部重排可选
```

### 10.3 适用场景

用于检测 L1-L6 伪装等级：

```text
L1 修改变量名
L2 修改函数名
L3 删除注释/修改格式
L4 局部语句换序
L5 函数拆分/合并
L6 等价表达式替换
```

---

## 11. ControlFlowSimilarity

### 11.1 定义

ControlFlowSimilarity 衡量控制结构序列和控制流形态是否相似。

### 11.2 控制结构抽象

将控制结构抽象为：

```text
IF
IF_ELSE
FOR_LOOP
WHILE_LOOP
DO_WHILE_LOOP
ENHANCED_FOR
SWITCH
TRY_CATCH
RECURSIVE_CALL
RETURN_BRANCH
BREAK_CONTINUE
```

### 11.3 V1/V2 实现方式

先实现控制结构序列：

```text
ControlSeq = [FOR_LOOP, IF, UPDATE, RETURN]
```

相似度：

```text
ControlFlowSimilarity = normalized_LCS(ControlSeqA, ControlSeqB)
```

### 11.4 V3 增强

构建简化 CFG：

```text
basic_block
edge_type
branch_condition_type
loop_back_edge
exit_node
```

再计算图结构近似相似度。

---

## 12. DataDependencySimilarity

### 12.1 定义

衡量变量读写依赖和数据流模式是否相似。

### 12.2 抽象形式

```text
DEF(var)
USE(var)
UPDATE(var)
ACCUMULATE(var)
COMPARE(var)
INDEX_ACCESS(array, index)
CALL_INPUT(args)
CALL_OUTPUT(result)
```

### 12.3 V2 实现

先实现轻量数据依赖签名：

```text
DataFlowSignature = sequence of read/write/update patterns
```

示例：

```text
INIT_ACCUMULATOR -> ITERATE_SEQUENCE -> CONDITIONAL_FILTER -> ACCUMULATE -> RETURN
```

### 12.4 限制

数据依赖分析不追求编译器级精确性。必须在文档和论文中说明：

```text
本系统采用静态轻量数据依赖签名，用于相似风险分析，不用于程序正确性证明。
```

---

## 13. OperationSequenceSimilarity

### 13.1 定义

衡量运算符和核心操作序列是否相似。

### 13.2 操作符抽象

```text
ARITH_ADD
ARITH_SUB
ARITH_MUL
ARITH_DIV
MOD
COMPARE_EQ
COMPARE_LT
COMPARE_GT
LOGICAL_AND
LOGICAL_OR
ASSIGN
INCREMENT
APPEND
SORT
MAP_GET
MAP_PUT
LIST_ADD
```

### 13.3 作用

用于识别同一算法思路中的核心操作序列，如：

```text
取模判断 → 条件过滤 → 计数累加
排序 → 双指针移动 → 条件比较
哈希表查询 → 插入 → 更新计数
```

---

## 14. RareFragmentSimilarity

### 14.1 定义

RareFragmentSimilarity 衡量两份代码是否共享在当前题目或数据集中较少出现的结构片段。

### 14.2 为什么重要

普通循环和输入输出相似不一定可疑，但以下相似更有风险：

```text
相同的特殊边界处理
相同的魔法数
相同的异常分支
相同的非必要辅助函数
相同的罕见表达式组合
相同的 bug 或错误处理逻辑
```

### 14.3 推荐实现

对每个结构片段计算稀有度：

```text
rarity(fragment) = log((N + 1) / (df(fragment) + 1))
```

其中：

```text
N = 当前题目提交总数或实验集样本数
df(fragment) = 包含该片段的提交数量
```

相似度：

```text
RareFragmentSimilarity(A, B) =
weighted_overlap(FragmentsA, FragmentsB, rarity)
```

### 14.4 证据输出

稀有片段必须输出证据：

```text
fragment_type
fragment_description
rarity_score
code_a_lines
code_b_lines
reason
```

---

## 15. IdentifierMappingSimilarity

### 15.1 定义

衡量两个代码之间标识符映射关系是否稳定。

### 15.2 示例

```text
A.sum    -> B.result
A.n      -> B.length
A.arr    -> B.nums
A.check  -> B.validate
```

如果映射关系在多个函数或多个语句块中稳定出现，则可作为证据。

### 15.3 注意事项

不能因为变量名语义相近就提高风险。该指标关注的是：

```text
结构位置一致 + 使用模式一致 + 映射稳定
```

而不是自然语言含义。

---

## 16. IOPatternSimilarity

### 16.1 定义

衡量输入输出处理模式是否相似。

### 16.2 降权原则

输入输出相似通常由题目格式决定，因此默认权重较低。

对于简单题，IOPatternSimilarity 必须被 NaturalSimilarityPenalty 进一步降权。

---

## 17. BugPatternSimilarity

### 17.1 定义

衡量两个代码是否存在相同或高度相似的错误模式。

### 17.2 可检测模式

```text
相同边界遗漏
相同 off-by-one 风险
相同异常处理分支
相同无效判断
相同魔法数
相同死代码结构
相同调试输出残留
```

### 17.3 风险解释

相同 bug 是较强证据，但必须谨慎表述：

```text
“检测到相似的异常/边界处理模式，建议人工复核”
```

不得表述为：

```text
“因为 bug 相同，所以一定抄袭”
```

---

## 18. CrossLanguageIRSimilarity

### 18.1 定义

跨语言 IR 相似度衡量不同语言代码在抽象操作层面的相似性。

### 18.2 首期范围

优先支持：

```text
Java ↔ Python
```

增强支持：

```text
Java ↔ C
Python ↔ C
```

### 18.3 IR 节点

初始 IR 包含：

```text
FUNCTION_DEF
INPUT_READ
OUTPUT_WRITE
VARIABLE_INIT
ASSIGNMENT
SEQUENCE_ITERATION
INDEX_LOOP
CONDITION
ARITHMETIC_OP
COMPARISON_OP
ACCUMULATION
COLLECTION_UPDATE
FUNCTION_CALL
RETURN
```

### 18.4 示例

Java：

```java
for (int x : arr) {
    if (x % 2 == 0) count++;
}
```

Python：

```python
for x in arr:
    if x % 2 == 0:
        count += 1
```

统一抽象：

```text
SEQUENCE_ITERATION
  CONDITION(MOD_EQ_ZERO)
  ACCUMULATION(COUNT_INCREMENT)
```

---

## 19. 综合风险评分

### 19.1 基础公式

推荐初始公式：

```text
RawSimilarityScore =
  w1 * TokenSimilarity
+ w2 * CanonicalTokenSimilarity
+ w3 * ASTStructureSimilarity
+ w4 * CanonicalASTSimilarity
+ w5 * ControlFlowSimilarity
+ w6 * DataDependencySimilarity
+ w7 * OperationSequenceSimilarity
+ w8 * RareFragmentSimilarity
+ w9 * IdentifierMappingSimilarity
+ w10 * BugPatternSimilarity
+ w11 * CrossLanguageIRSimilarity
```

默认权重：

```text
w1  = 0.08
w2  = 0.10
w3  = 0.12
w4  = 0.16
w5  = 0.12
w6  = 0.10
w7  = 0.08
w8  = 0.12
w9  = 0.06
w10 = 0.04
w11 = 0.02
```

权重总和应为 1.00。未实现指标的权重必须重新归一化。

### 19.2 题目惩罚与校正

```text
ProblemAdjustedScore =
RawSimilarityScore
- p1 * NaturalSimilarityPenalty
- p2 * TemplatePenalty
+ p3 * RareEvidenceBonus
+ p4 * StableMappingBonus
```

其中：

```text
NaturalSimilarityPenalty = f(NaturalSimilarityRisk, common_structure_overlap)
TemplatePenalty = f(TemplateRiskScore, template_fragment_overlap)
RareEvidenceBonus = f(RareFragmentSimilarity, rarity_score)
StableMappingBonus = f(IdentifierMappingSimilarity, mapping_coverage)
```

### 19.3 分数范围

所有分数统一为：

```text
0.0 <= score <= 1.0
```

前端展示时转换为百分比。

---

## 20. 动态阈值接口

动态阈值由 `PROBLEM_AWARE_SCORING.md` 详细定义。本文件只规定算法调用接口：

```text
threshold = ComputeDynamicThreshold(problem_profile, metric_profile, config)
```

输出：

```text
base_threshold
adjustment_items
final_threshold
threshold_reason
```

示例：

```json
{
  "base_threshold": 0.80,
  "adjustment_items": [
    {"name": "high_natural_similarity", "delta": 0.06},
    {"name": "medium_difficulty", "delta": -0.02},
    {"name": "high_template_risk", "delta": 0.04}
  ],
  "final_threshold": 0.88,
  "threshold_reason": "该题自然相似风险和模板化风险较高，因此提高阈值以降低简单题误报。"
}
```

---

## 21. 风险等级划分

### 21.1 基础规则

风险不是简单按分数区间，而应结合动态阈值：

```text
risk_margin = weighted_similarity_score - dynamic_threshold
```

建议：

```text
低风险：risk_margin < -0.10
中风险：-0.10 <= risk_margin < 0
较高风险：0 <= risk_margin < 0.10
高风险：risk_margin >= 0.10
```

### 21.2 输出措辞

允许：

```text
低风险
中风险
较高风险
高风险
建议人工复核
```

禁止：

```text
抄袭
确定抄袭
作弊成立
直接判定违规
```

---

## 22. 证据生成算法

### 22.1 证据类型

```text
TOKEN_OVERLAP
CANONICAL_TOKEN_OVERLAP
AST_SUBTREE_MATCH
CONTROL_FLOW_MATCH
DATA_DEPENDENCY_MATCH
OPERATION_SEQUENCE_MATCH
RARE_FRAGMENT_MATCH
IDENTIFIER_MAPPING_MATCH
IO_PATTERN_MATCH
BUG_PATTERN_MATCH
CROSS_LANGUAGE_IR_MATCH
```

### 22.2 证据对象结构

```json
{
  "evidence_id": "E-001",
  "evidence_type": "AST_SUBTREE_MATCH",
  "severity": "HIGH",
  "similarity_score": 0.91,
  "code_a_start_line": 12,
  "code_a_end_line": 24,
  "code_b_start_line": 10,
  "code_b_end_line": 22,
  "description": "两份代码存在高度相似的循环-条件-累加结构。",
  "review_hint": "建议检查该结构是否来自题目模板或课程示例。",
  "metric_source": "CanonicalASTSimilarity"
}
```

### 22.3 证据排序

证据排序优先级：

```text
RareFragmentMatch
BugPatternMatch
CanonicalASTMatch
DataDependencyMatch
ControlFlowMatch
IdentifierMappingMatch
TokenOverlap
IOPatternMatch
```

原因：普通 token/IO 相似证据较弱，稀有片段和异常模式证据较强。

---

## 23. 人工复核建议生成

### 23.1 生成规则

根据风险等级和证据类型生成复核建议：

```text
低风险：一般无需重点复核
中风险：建议抽查相似片段
较高风险：建议人工查看主要结构证据
高风险：建议结合提交时间、课堂模板、历史记录进行重点复核
```

### 23.2 禁止事项

复核建议不得包含：

```text
处罚建议
违规定性
学生主观动机判断
无法验证的事实判断
```

---

## 24. 任务级聚合分析

系统需要输出任务整体报告：

```text
total_submissions
total_pairs
risk_distribution
high_risk_pair_count
average_similarity
average_dynamic_threshold
problem_profile_summary
common_template_fragments
cluster_summary
```

### 24.1 相似关系图

可选生成代码相似关系图：

```text
node = submission
edge = risk_margin over dynamic_threshold
edge_weight = risk_margin
```

用于前端展示高风险群组。

---

## 25. 实验模式

算法必须支持实验运行模式：

```text
experiment_id
dataset_id
attack_level
baseline_method
metric_config
random_seed
output_dir
```

实验结果必须可保存为：

```text
CSV
JSON
Markdown report
PNG charts，可由后续脚本生成
```

---

## 26. 与数据库的关系

算法输出应映射到以下表：

```text
analysis_result
similarity_metric
evidence
problem_feature
experiment_result
```

具体字段由 `DATABASE_SCHEMA.md` 定义。

---

## 27. 与前端的关系

前端必须能够展示：

```text
最终风险分数
动态阈值
超过阈值的 margin
多维相似度雷达图
证据列表
代码高亮片段
变量映射表
题目复杂度解释
人工复核建议
```

算法输出 JSON 必须为前端展示保留充分字段。

---

## 28. 算法实现优先级

### 28.1 V1 必做

```text
PreprocessCode
TokenSimilarity
BasicASTStructureSimilarity
BasicEvidenceGeneration
PairRiskResult
```

### 28.2 V2 必做

```text
CanonicalTokenSimilarity
CanonicalASTSimilarity
IdentifierMappingSimilarity
ProblemAdjustedScore
DynamicThreshold Integration
RiskLevel Assignment
```

### 28.3 V3 必做

```text
RareFragmentSimilarity
OperationSequenceSimilarity
ControlFlowSimilarity
Experiment Mode
Ablation Switches
```

### 28.4 V4 增强

```text
DataDependencySimilarity
CrossLanguageIRSimilarity
BugPatternSimilarity
External Baseline Import
Large-scale Experiment Optimization
```

---

## 29. 质量要求

### 29.1 可解释性

任何高风险结果都必须至少包含：

```text
1 个结构证据
1 个代码片段定位
1 个动态阈值解释
1 条人工复核建议
```

### 29.2 可复现性

实验结果必须保存：

```text
算法版本
配置文件
输入数据集版本
随机种子
运行时间
指标输出
```

### 29.3 鲁棒性

系统必须处理：

```text
空文件
超短代码
语法错误代码
不同编码
混合换行符
大文件
解析失败
重复提交
```

---

## 30. 自检清单

每次修改算法后，必须检查：

```text
[ ] 是否仍然输出风险而不是抄袭结论
[ ] 是否保存算法版本
[ ] 是否保留原始代码行号映射
[ ] 是否支持解析失败降级
[ ] 是否能够输出证据
[ ] 是否能够解释动态阈值
[ ] 是否未把简单 IO 相似当成强证据
[ ] 是否未过度依赖大模型
[ ] 是否支持实验模式
[ ] 是否有单元测试覆盖核心函数
```
