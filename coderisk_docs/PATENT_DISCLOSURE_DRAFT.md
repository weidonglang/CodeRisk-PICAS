# PATENT_DISCLOSURE_DRAFT.md

> 本文件是 CodeRisk / PICAS 项目的发明专利技术交底书草稿，用于向专利代理人、导师或项目负责人说明技术方案。它不是正式权利要求书，也不替代专业专利代理意见。正式申请前，应由专利代理人根据检索结果、申请主体和公开时点进行修改。
>
> **重要提醒：在提交专利申请前，不建议将本文件、核心算法细节、完整流程图、实验结论和源代码公开到 GitHub、博客、论文预印本或答辩公开材料中。**

---

## 1. 拟申请名称

### 1.1 推荐中文名称

```text
一种面向编程作业的题目复杂度自适应代码相似风险检测方法、装置及存储介质
```

### 1.2 备选中文名称

```text
一种基于题目感知动态阈值与置换不变结构表示的代码相似风险检测方法及系统
```

```text
一种面向多语言程序提交的代码相似风险评估方法、装置、设备及计算机可读存储介质
```

### 1.3 英文内部名称

```text
PICAS: Problem-aware Invariant Code Similarity Analysis
```

---

## 2. 技术领域

本发明涉及计算机软件工程、程序分析、代码相似度检测、代码克隆检测、教育信息化与编程作业辅助评审领域，尤其涉及一种结合题目复杂度评估、置换不变结构规范化、多维结构相似度融合和动态阈值校准的代码相似风险检测方法、装置及存储介质。

---

## 3. 背景技术

### 3.1 编程作业代码查重的现实需求

在高校程序设计课程、算法训练平台、在线评测系统和课程设计实践中，教师通常需要对大量学生提交的代码进行相似度检测，以发现可能存在的复制、改写、变量名替换、函数名替换、跨语言重写或 AI 辅助改写等情况。

常见检测方法包括：

1. 字符串相似度检测；
2. Token 序列相似度检测；
3. 代码指纹检测；
4. 抽象语法树 AST 相似度检测；
5. 控制流或数据流结构相似度检测；
6. 现有工具化查重系统输出的相似分数。

这些方法能够在部分场景下发现高度相似代码，但在真实编程作业场景中仍存在不足。

### 3.2 现有技术的主要问题

#### 3.2.1 固定阈值不适合不同题目

现有检测流程通常采用统一阈值，例如 70%、80% 或 85%。然而，不同题目的自然相似程度差异很大：

- 简单输入输出题、模板化排序题、标准 DFS/BFS 题，独立完成的代码也可能高度相似；
- 复杂业务逻辑题、综合算法题、开放式课程设计题，若结构高度相似则更可疑；
- 采用统一阈值容易在简单题上误报，在复杂题上漏报。

#### 3.2.2 表层改写会影响检测稳定性

抄袭者可能通过以下方式降低相似度：

1. 修改变量名；
2. 修改函数名；
3. 修改参数名；
4. 删除注释和调整格式；
5. 调整局部语句顺序；
6. 拆分或合并函数；
7. 替换等价表达式；
8. 使用 AI 对代码进行重写。

普通字符串或 token 方法容易被这类表层改写干扰。

#### 3.2.3 多语言提交难以统一比较

同一道题可能允许 Java、Python、C、C++、Go 等语言提交。不同语言在语法形式、标准库、循环表达、输入输出方式和类型系统上存在差异，导致同一算法逻辑在不同语言中的表面结构差别较大。直接比较 token 或语言原生 AST 难以准确反映跨语言相似性。

#### 3.2.4 输出相似分数不足以辅助人工复核

现有系统常直接输出相似百分比或代码片段高亮，但缺乏对“为什么可疑”的结构化说明。对于教师或评审人员而言，仅有分数难以判断：

- 相似是否由题目本身导致；
- 相似片段是否属于常见模板；
- 是否存在稳定变量重命名映射；
- 是否存在稀有边界处理逻辑相同；
- 是否存在相同错误模式。

因此，需要一种能够输出风险等级、动态阈值、多维指标和证据链的相似风险评估方案。

---

## 4. 发明目的

本发明旨在提出一种面向编程作业场景的代码相似风险检测方法，解决现有技术中固定阈值不合理、简单题误报率较高、改名伪装影响检测、跨语言结构难以比较、检测结果解释性不足等问题。

具体目标包括：

1. 根据题目自身特征和历史提交分布，生成题目复杂度、模板化风险、解法空间和自然相似风险等指标；
2. 对待检测代码进行标识符归一化、函数名归一化、参数名归一化、可交换表达式规范化和结构指纹生成；
3. 将不同编程语言代码映射到语言无关中间表示，提取控制结构、操作序列、数据依赖和输入输出模式；
4. 融合 token、AST、控制流、数据依赖、操作序列、稀有片段、标识符映射等多维相似度；
5. 根据题目复杂度和自然相似风险动态生成相似风险阈值；
6. 输出相似风险等级、超过阈值情况、关键证据片段、变量映射关系、相同边界逻辑和人工复核建议。

---

## 5. 技术方案概述

本发明提供一种代码相似风险检测方法，包括以下步骤：

```text
S1：获取题目描述、输入输出格式、约束条件、参考答案和待检测代码集合；
S2：对题目进行特征提取，计算题目复杂度、解法空间、模板化风险和自然相似风险；
S3：对代码进行语言识别、预处理和解析，生成 token、AST、函数列表、变量列表、控制结构和数据依赖信息；
S4：对代码结构进行置换不变规范化，生成规范 token、规范 AST、结构指纹和标识符映射；
S5：将代码映射为语言无关中间表示，提取控制流签名、数据依赖签名和操作序列；
S6：对代码对计算多维相似度；
S7：基于题目特征动态生成相似风险阈值；
S8：融合多维相似度与题目风险因子生成综合风险分数；
S9：根据综合风险分数、动态阈值和证据强度输出风险等级；
S10：生成结构化证据报告与人工复核建议。
```

---

## 6. 系统组成

本发明可实现为一种系统或装置，包括以下模块。

### 6.1 题目信息获取模块

用于获取题目描述、输入格式、输出格式、约束条件、样例输入输出、题目标签、参考答案、历史提交代码及元数据。

### 6.2 题目复杂度评估模块

用于计算：

```text
DifficultyScore
SolutionSpaceScore
TemplateWeightedSimilarityScore
NaturalSimilarityRisk
HistoricalSimilarityDistribution
StructuralCheckApplicability
```

其中：

- DifficultyScore 表示题目实现难度；
- SolutionSpaceScore 表示可能解法空间大小；
- TemplateWeightedSimilarityScore 表示题目是否容易套用标准模板；
- NaturalSimilarityRisk 表示独立完成代码自然相似的风险；
- HistoricalSimilarityDistribution 表示历史提交中的相似度分布特征；
- StructuralCheckApplicability 表示当前题目适合进行结构查重的程度。

### 6.3 代码解析模块

用于对 Java、Python、C 等语言的代码进行解析，输出：

```text
TokenSequence
AST
FunctionList
VariableList
ControlStructureList
CallGraphCandidate
ReadWriteSet
IOPattern
```

首期可采用 tree-sitter 作为统一解析底座，对 Java/Python/C 提供多语言语法树支持；必要时针对 Java 使用 JavaParser，针对 Python 使用内置 ast 模块进行补充。

### 6.4 置换不变规范化模块

用于消除变量名、函数名、参数名、局部标识符命名差异对检测结果的影响，生成：

```text
CanonicalTokenSequence
CanonicalAST
CanonicalStructureFingerprint
IdentifierMapping
ScopeAwareVariableMap
NormalizedExpressionTree
```

核心处理包括：

1. 标识符作用域感知编号；
2. 函数名归一化；
3. 参数名归一化；
4. 局部变量编号规范化；
5. 可交换表达式排序；
6. AST 子树规范表示；
7. 局部无依赖语句的稳定排序。

### 6.5 语言无关中间表示模块

用于将不同语言的结构映射到统一 IR：

```text
LOOP
CONDITION
ASSIGNMENT
UPDATE
RETURN
CALL
INPUT
OUTPUT
COLLECTION_OPERATION
ARITHMETIC_OPERATION
COMPARISON_OPERATION
```

该模块生成：

```text
LanguageIndependentIR
ControlFlowSignature
DataDependencySignature
OperationSequence
AlgorithmStepSketch
```

### 6.6 多维相似度计算模块

用于计算代码对之间的多维相似度，包括但不限于：

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
BugPatternSimilarity
IOPatternSimilarity
CrossLanguageIRSimilarity
```

### 6.7 动态阈值生成模块

用于根据题目复杂度、模板化风险、自然相似风险和历史提交相似分布生成动态阈值。

基础表达可为：

```text
DynamicThreshold = clamp(
    BaseThreshold
    + a * NaturalSimilarityRisk
    + b * TemplateWeightedSimilarityScore
    - c * DifficultyScore
    - d * SolutionSpaceScore
    + e * HistoricalSimilarityAdjustment,
    MinThreshold,
    MaxThreshold
)
```

其中：

- 自然相似风险越高，阈值越高；
- 模板化风险越高，阈值越高；
- 题目难度越高，阈值可适当降低；
- 解法空间越大，阈值可适当降低；
- 历史提交相似分布越集中，阈值可适当提高。

### 6.8 风险融合与证据输出模块

用于生成最终结果：

```text
WeightedSimilarityScore
DynamicThreshold
RiskLevel
ExceededThreshold
MetricBreakdown
EvidenceList
ReviewSuggestion
```

证据包括：

1. 相似代码片段；
2. 相似函数；
3. 相似 AST 子结构；
4. 相似控制流模式；
5. 相似数据依赖模式；
6. 稳定变量重命名关系；
7. 相同边界条件；
8. 相同异常处理；
9. 相同魔法数；
10. 相同错误或特殊处理逻辑。

---

## 7. 核心算法流程

### 7.1 输入

```text
Question Q
ReferenceSolutions R = {r1, r2, ...}
Submissions S = {s1, s2, ..., sn}
LanguageSet L = {Java, Python, C, ...}
OptionalHistoricalSubmissions H
```

### 7.2 输出

```text
ResultMatrix M
EvidenceReports E
ProblemProfile P
RiskSummary G
```

其中：

- M 表示代码对之间的风险矩阵；
- E 表示结构化证据报告；
- P 表示题目画像；
- G 表示任务整体风险统计。

### 7.3 题目画像生成

```text
P = BuildProblemProfile(Q, R, H)
```

P 包括：

```text
text_length
io_complexity
constraint_count
sample_count
reference_loc
reference_function_count
reference_cyclomatic_complexity
data_structure_count
algorithm_tag_count
template_indicator
historical_similarity_mean
historical_similarity_std
historical_similarity_p90
```

### 7.4 代码规范化

对于每份代码 si：

```text
parsed_i = Parse(si)
canonical_i = Canonicalize(parsed_i)
ir_i = BuildLanguageIndependentIR(canonical_i)
fingerprint_i = BuildFingerprint(canonical_i, ir_i)
```

### 7.5 代码对相似度计算

对于每个代码对 si, sj：

```text
metrics_ij = ComputeSimilarity(canonical_i, canonical_j, ir_i, ir_j)
```

metrics_ij 包括：

```text
token_similarity
canonical_token_similarity
ast_similarity
canonical_ast_similarity
control_flow_similarity
data_dependency_similarity
operation_sequence_similarity
rare_fragment_similarity
identifier_mapping_similarity
bug_pattern_similarity
io_pattern_similarity
cross_language_ir_similarity
```

### 7.6 动态阈值计算

```text
threshold_q = GenerateDynamicThreshold(P)
```

### 7.7 风险分数计算

```text
risk_ij = WeightedFusion(metrics_ij, P)
```

其中权重受题目画像影响。例如：

- 模板题降低常见结构权重；
- 复杂题提高稀有片段、数据依赖和控制流权重；
- 跨语言比较提高 IR 相似度权重；
- 简单题提高阈值并提高自然相似惩罚。

### 7.8 证据生成

```text
evidence_ij = GenerateEvidence(si, sj, metrics_ij, canonical_i, canonical_j, ir_i, ir_j)
```

### 7.9 风险等级输出

```text
if risk_ij < threshold_q - margin_low:
    level = LOW
elif risk_ij < threshold_q:
    level = MEDIUM
elif risk_ij < threshold_q + margin_high:
    level = HIGH
else:
    level = HIGH
```

系统不输出“抄袭”结论，只输出“相似风险等级”和“人工复核建议”。

---

## 8. 关键技术点一：题目复杂度自适应阈值

### 8.1 技术问题

同一相似度分数在不同题目中的含义不同。例如：

- A+B 题中 85% 相似可能是自然现象；
- 复杂图算法题中 85% 相似可能高度可疑。

### 8.2 技术方案

系统根据题目特征生成题目画像，并计算动态阈值。

输入特征包括：

```text
题目描述长度
输入输出复杂度
约束条件数量
样例数量
参考答案代码行数
参考答案函数数量
圈复杂度
控制结构数量
数据结构种类
算法标签数量
历史提交相似度均值
历史提交相似度标准差
历史提交相似度高分位数
```

输出指标包括：

```text
DifficultyScore
SolutionSpaceScore
TemplateWeightedSimilarityScore
NaturalSimilarityRisk
DynamicThreshold
```

### 8.3 技术效果

该机制能够：

1. 对简单题提高判定阈值，降低自然相似导致的误报；
2. 对复杂题降低判定阈值或提高结构权重，提升可疑相似代码召回；
3. 对模板题降低通用模板结构权重，突出稀有片段和特殊边界逻辑；
4. 对历史提交高度集中题目自动提高自然相似容忍度。

---

## 9. 关键技术点二：置换不变结构规范化

### 9.1 技术问题

变量名、函数名和参数名修改是常见伪装方式。若直接比较原始 token 或字符串，检测结果会被命名差异影响。

### 9.2 技术方案

系统对代码进行作用域感知的标识符编号和结构规范化：

```text
变量名 -> VAR_SCOPE_INDEX
函数名 -> FUNC_INDEX
参数名 -> PARAM_INDEX
类名/结构体名 -> TYPE_INDEX
临时变量 -> TMP_INDEX
```

例如：

```java
int sum = a + b;
```

与：

```java
int result = x + y;
```

可规范化为：

```text
TYPE_INT VAR_1 = VAR_2 + VAR_3
```

### 9.3 扩展处理

1. 可交换表达式排序：`a + b` 与 `b + a` 规范为相同结构；
2. 逻辑条件规范化：`x > y` 与 `y < x` 统一表达；
3. AST 子树规范表示：对等价子树生成稳定 fingerprint；
4. 局部无依赖语句排序：在不改变数据依赖的前提下进行稳定排序；
5. 函数拆分识别：通过调用序列和数据依赖缓解函数边界变化影响。

### 9.4 技术效果

该机制增强系统对以下伪装的鲁棒性：

```text
变量名替换
函数名替换
参数名替换
格式调整
注释删除
局部语句轻微换序
等价表达式替换
```

---

## 10. 关键技术点三：语言无关中间表示

### 10.1 技术问题

同一算法在 Java、Python、C 中表达形式不同，导致 token 和 AST 直接比较困难。

### 10.2 技术方案

系统将不同语言结构映射为统一中间表示，包括：

```text
ITERATE_SEQUENCE
INDEX_LOOP
CONDITION_BRANCH
ACCUMULATE_UPDATE
ARRAY_ACCESS
MAP_LOOKUP
RECURSIVE_CALL
SORT_OPERATION
QUEUE_OPERATION
STACK_OPERATION
RETURN_VALUE
INPUT_READ
OUTPUT_WRITE
```

示例：

Java 增强 for 循环、Python for-in 循环和 C 下标循环，均可抽象为：

```text
ITERATE_SEQUENCE
  CONDITION
  UPDATE
```

### 10.3 技术效果

该机制可提升跨语言重写代码之间的结构相似识别能力，尤其适用于算法题和课程作业场景中的 Java-Python、Python-C、Java-C 对比。

---

## 11. 关键技术点四：多维风险融合

### 11.1 技术问题

单一相似度指标容易受到代码长度、模板结构、语言差异和格式变化影响。

### 11.2 技术方案

系统采用多维指标融合：

```text
WeightedSimilarityScore =
  w1 * CanonicalTokenSimilarity
+ w2 * CanonicalASTSimilarity
+ w3 * ControlFlowSimilarity
+ w4 * DataDependencySimilarity
+ w5 * OperationSequenceSimilarity
+ w6 * RareFragmentSimilarity
+ w7 * IdentifierMappingSimilarity
+ w8 * BugPatternSimilarity
+ w9 * CrossLanguageIRSimilarity
- p1 * NaturalSimilarityPenalty
- p2 * TemplatePenalty
```

权重根据题目画像和语言组合动态调整。

### 11.3 技术效果

该机制能够在不同场景下突出更可靠的证据来源：

- 简单题：降低通用 token / AST 结构权重；
- 复杂题：提高控制流、数据依赖、稀有片段权重；
- 跨语言：提高 IR 相似度权重；
- 模板题：降低模板片段权重，提高特殊边界和错误模式权重。

---

## 12. 关键技术点五：结构化证据输出

### 12.1 技术问题

仅输出相似百分比不利于人工复核。

### 12.2 技术方案

系统输出证据链：

```text
证据类型
证据位置
相似片段
相似分数
相似原因
是否属于模板片段
是否属于稀有片段
是否跨语言映射
人工复核建议
```

### 12.3 技术效果

该机制能辅助教师或管理员从分数判断转向证据判断，减少误判并增强结果可解释性。

---

## 13. 有益效果

与现有技术相比，本发明至少具有以下有益效果：

1. **降低简单题误报**：根据题目自然相似风险动态提高阈值，减少独立完成代码被误判为高风险的情况；
2. **提高复杂题检测敏感性**：对复杂题提高结构证据权重，使高结构相似代码更容易被发现；
3. **增强改名伪装鲁棒性**：通过置换不变规范化削弱变量名、函数名和参数名替换的影响；
4. **支持跨语言结构比较**：通过语言无关 IR 对 Java、Python、C 等语言进行统一结构表达；
5. **增强结果可解释性**：输出动态阈值、多维指标和结构化证据链，而不是仅输出相似分数；
6. **便于人工复核**：提供相似片段、变量映射、控制流结构、稀有片段和复核建议；
7. **适合教育场景**：不直接判定抄袭，而输出相似风险等级，降低伦理和管理风险。

---

## 14. 附图说明建议

正式申请可准备以下附图。

### 图 1：系统总体流程图

```text
题目与代码输入
  -> 题目画像生成
  -> 代码解析
  -> 置换不变规范化
  -> 语言无关 IR 构建
  -> 多维相似度计算
  -> 动态阈值生成
  -> 风险融合
  -> 证据报告输出
```

### 图 2：题目复杂度自适应阈值生成流程图

```text
题目文本特征
参考答案静态特征
历史提交分布特征
  -> 题目复杂度评分
  -> 模板风险评分
  -> 自然相似风险评分
  -> 动态阈值
```

### 图 3：置换不变规范化流程图

```text
原始代码
  -> 语言解析
  -> 作用域分析
  -> 标识符编号
  -> 表达式规范化
  -> AST 子树指纹
  -> 规范结构表示
```

### 图 4：跨语言 IR 映射示意图

```text
Java AST / Python AST / C AST
  -> 语言特定节点映射
  -> 统一结构节点
  -> 控制流签名
  -> 操作序列
```

### 图 5：风险报告生成示意图

```text
多维相似度
动态阈值
证据片段
题目画像
  -> 风险等级
  -> 指标分解
  -> 人工复核建议
```

---

## 15. 具体实施方式

### 15.1 实施例一：同语言 Java 作业检测

输入：

```text
题目：数组求和并输出最大值
语言：Java
提交数量：80
参考答案：1 份
```

处理过程：

1. 系统提取题目输入输出复杂度、参考答案 LOC、控制结构数量；
2. 计算该题为低难度、高自然相似风险；
3. 对 Java 代码进行 token 和 AST 解析；
4. 对变量名、函数名、参数名进行归一化；
5. 对所有代码对计算多维相似度；
6. 动态阈值高于基础阈值；
7. 对仅存在通用结构相似的代码对输出低/中风险；
8. 对存在相同特殊边界处理、相同错误模式和高度稳定变量映射的代码对输出高风险。

技术效果：降低简单题中自然相似导致的误报。

### 15.2 实施例二：变量名替换伪装检测

输入两份代码，一份将 `sum/count/index` 替换为 `ans/res/k`。

处理过程：

1. 系统解析作用域；
2. 将变量按声明顺序和使用关系编号；
3. 生成规范 token 序列；
4. 比较规范 AST 和数据依赖；
5. 输出稳定变量映射证据。

技术效果：变量名替换后仍能识别结构相似。

### 15.3 实施例三：跨语言 Java-Python 检测

输入 Java 与 Python 两份代码，均实现同一算法。

处理过程：

1. Java AST 和 Python AST 分别解析；
2. 循环、条件、赋值、数组访问和输出操作映射为统一 IR；
3. 计算 IR 操作序列相似度和控制流相似度；
4. 根据语言组合提高 CrossLanguageIRSimilarity 权重；
5. 输出跨语言结构相似证据。

技术效果：能够初步识别跨语言重写场景中的结构相似。

### 15.4 实施例四：模板题自然相似降权

输入标准 DFS 模板题的大量提交。

处理过程：

1. 系统识别参考答案与历史提交中存在高度集中的模板结构；
2. 计算 TemplateWeightedSimilarityScore 较高；
3. 提高动态阈值；
4. 对常见 DFS 模板片段进行降权；
5. 对特殊剪枝条件、边界处理、错误恢复逻辑进行重点比较。

技术效果：避免将标准算法模板误判为高风险，重点保留稀有片段证据。

---

## 16. 可选算法细节

### 16.1 题目画像计算

```text
DifficultyScore = normalize(
  a1 * reference_loc
+ a2 * reference_cyclomatic_complexity
+ a3 * control_structure_count
+ a4 * data_structure_count
+ a5 * constraint_complexity
)
```

```text
TemplateWeightedSimilarityScore = normalize(
  b1 * algorithm_template_indicator
+ b2 * historical_similarity_concentration
+ b3 * reference_structure_commonness
)
```

```text
NaturalSimilarityRisk = normalize(
  c1 * io_simplicity
+ c2 * low_solution_space_indicator
+ c3 * template_risk_score
+ c4 * historical_similarity_mean
)
```

### 16.2 风险融合

```text
FinalWeightedSimilarityScore = Σ(w_i * metric_i) - NaturalSimilarityPenalty - TemplatePenalty
```

其中 `w_i` 可根据题目类型、语言组合和实验配置调整。

### 16.3 证据强度

```text
EvidenceStrength =
  evidence_similarity
* evidence_rarity
* evidence_coverage
* evidence_location_importance
```

证据强度越高，越适合用于人工复核。

---

## 17. 权利要求草案

> 以下仅为技术交底阶段草案，不建议直接提交。正式权利要求应由代理人根据检索结果、保护范围和申请策略改写。

### 权利要求 1：方法独立权利要求草案

一种面向编程作业的代码相似风险检测方法，其特征在于，包括：

1. 获取待检测题目的题面文本、输入输出格式、约束条件、参考答案和至少两份待检测代码；
2. 基于所述题面文本、输入输出格式、约束条件和参考答案提取题目特征，计算题目复杂度分数、解法空间分数、模板化风险分数和自然相似风险分数；
3. 对所述待检测代码进行语言识别和语法解析，获得 token 序列、抽象语法树、函数信息、变量信息和控制结构信息；
4. 对所述待检测代码进行置换不变结构规范化，生成规范 token 序列、规范抽象语法树和结构指纹；
5. 将所述待检测代码映射为语言无关中间表示，获得控制流签名、数据依赖签名和操作序列；
6. 基于所述规范 token 序列、规范抽象语法树、控制流签名、数据依赖签名和操作序列计算多维相似度；
7. 基于所述题目复杂度分数、解法空间分数、模板化风险分数和自然相似风险分数生成动态相似风险阈值；
8. 根据所述多维相似度和动态相似风险阈值生成综合风险分数和风险等级；
9. 输出包含风险等级、综合风险分数、动态相似风险阈值、多维相似度分解和结构化证据的检测报告。

### 权利要求 2：题目复杂度特征

根据权利要求 1 所述的方法，其中，所述题目特征包括以下至少两种：题目描述长度、输入输出字段数量、约束条件数量、样例数量、参考答案代码行数、参考答案函数数量、参考答案圈复杂度、数据结构数量、控制结构数量、算法标签数量、历史提交相似度均值、历史提交相似度标准差和历史提交相似度高分位数。

### 权利要求 3：置换不变规范化

根据权利要求 1 所述的方法，其中，所述置换不变结构规范化包括：对变量名、函数名、参数名、类名或结构体名进行作用域感知编号，并对可交换表达式和等价比较表达式进行规范排序，以生成不受标识符命名差异影响的代码结构表示。

### 权利要求 4：语言无关中间表示

根据权利要求 1 所述的方法，其中，所述语言无关中间表示包括循环节点、条件节点、赋值节点、函数调用节点、返回节点、输入节点、输出节点、集合操作节点、算术操作节点和比较操作节点中的至少一种。

### 权利要求 5：动态阈值

根据权利要求 1 所述的方法，其中，所述动态相似风险阈值随自然相似风险分数和模板化风险分数增大而提高，随题目复杂度分数和解法空间分数增大而降低。

### 权利要求 6：证据输出

根据权利要求 1 所述的方法，其中，所述结构化证据包括相似代码片段、相似函数、相似抽象语法树子结构、相似控制流结构、相似数据依赖关系、标识符映射关系、相同边界条件、相同异常处理逻辑、相同魔法数和相同错误模式中的至少一种。

### 权利要求 7：装置权利要求草案

一种代码相似风险检测装置，包括：

1. 题目信息获取单元；
2. 题目复杂度评估单元；
3. 代码解析单元；
4. 置换不变规范化单元；
5. 语言无关中间表示构建单元；
6. 多维相似度计算单元；
7. 动态阈值生成单元；
8. 风险融合单元；
9. 证据报告生成单元；

其中，各单元被配置为执行权利要求 1 至 6 任一项所述的方法。

### 权利要求 8：电子设备权利要求草案

一种电子设备，包括处理器和存储器，所述存储器中存储有计算机程序，所述计算机程序被所述处理器执行时实现权利要求 1 至 6 任一项所述的方法。

### 权利要求 9：计算机可读存储介质权利要求草案

一种计算机可读存储介质，其上存储有计算机程序，所述计算机程序被处理器执行时实现权利要求 1 至 6 任一项所述的方法。

### 权利要求 10：计算机程序产品权利要求草案

一种计算机程序产品，包括计算机程序或指令，所述计算机程序或指令被处理器执行时实现权利要求 1 至 6 任一项所述的方法。

---

## 18. 申请前检索关键词

建议在提交前检索以下关键词，供代理人判断新颖性与创造性：

```text
代码相似度检测 动态阈值
代码查重 题目难度 自适应
程序相似度 自然相似风险
代码克隆检测 置换不变
代码相似度 语言无关中间表示
编程作业 查重 风险评估
AST 相似度 动态阈值
代码查重 证据输出
cross-language code similarity detection
problem-aware code similarity
permutation-invariant code representation
```

---

## 19. 公开与投稿顺序建议

建议顺序：

```text
1. 完成技术交底书草稿
2. 与导师/代理人确认申请主体和保护范围
3. 进行初步专利检索
4. 提交专利申请
5. 再公开论文、GitHub、演示视频或完整技术细节
6. 后续申请软著和投稿论文
```

如果必须先进行校内开题或中期答辩，应避免公开：

```text
完整权利要求草案
核心公式细节
完整算法流程图
全部实验数据和结论
完整源代码仓库
```

---

## 20. 与论文和软著的边界

### 20.1 与论文的关系

论文重点写：

```text
问题定义
方法设计
系统实现
实验验证
消融分析
失败案例
```

专利重点写：

```text
技术问题
技术方案
技术效果
流程步骤
模块组成
权利要求保护范围
```

### 20.2 与软著的关系

软著保护软件表达，即源码和文档；专利尝试保护技术方案。两者可以同时布局，但材料不能混同。

---

## 21. 当前版本待补充内容

正式交底前建议补充：

```text
1. 系统核心流程图
2. 动态阈值公式最终参数说明
3. 置换不变规范化示例图
4. 跨语言 IR 节点示例
5. 3 个完整实施例输入输出
6. 实验初步结果表
7. 与现有工具的差异表
8. 可选保护点排序
```

---

## 22. Codex 开发注意事项

在专利申请前，Codex 开发生成的公开内容应遵守：

1. GitHub 仓库可先设为 private；
2. README 不写完整算法公式；
3. 不公开完整 `PATENT_DISCLOSURE_DRAFT.md`；
4. 不公开核心实验结论；
5. 提交记录中避免出现“专利核心权利要求”等敏感描述；
6. 演示版本可展示系统功能，但不展示完整技术细节。

---

## 23. 最小可申请技术方案

如果项目时间有限，专利申请可收敛为：

```text
一种题目复杂度自适应的代码相似风险检测方法
```

核心只保护：

1. 题目画像生成；
2. 动态阈值生成；
3. 置换不变结构相似度；
4. 证据化风险报告。

不强行保护所有跨语言 IR 细节，避免方案过大导致不稳定。

---

## 24. 推荐保护重点排序

优先级从高到低：

```text
P1：题目复杂度/自然相似风险驱动的动态阈值生成
P2：置换不变结构规范化后的多维相似风险融合
P3：基于题目画像的相似证据降权与加权机制
P4：跨语言 IR 相似度在代码查重中的融合
P5：风险等级与结构化证据报告生成
```

---

## 25. 文件状态

```text
文档类型：专利技术交底书草稿
适用阶段：专利申请前内部讨论
公开建议：不公开
当前状态：可作为与导师/代理人沟通的初稿
```


## 表述边界补充

禁止宣称 PICAS 能准确判断抄袭、完整识别 AI 改写、证明两个程序语义等价或完整解决跨语言查重。推荐结论表述为：在自建编程作业数据集上，PICAS 相比固定阈值方法能够降低简单题自然相似导致的误报，并在标识符替换和格式调整等表层改写场景下保持更稳定的相似风险评估。
