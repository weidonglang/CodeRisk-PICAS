# PROJECT_SPEC.md

> 2026-10-09 本轮增量：新增作者发布的 IR-Plag 接收、已观察 ConPlag 融合分解和本地单后端异步执行/失败恢复。Java/Python 主研究范围不变，新数据正式资格仍为零，生产评分公式不变。 依据与边界见 [前三项推进记录](proposal/NEXT_THREE_PROGRESS.md)。

> 2026-10-09 新增 [版本与自然相似复核](proposal/VERSION_AND_NATURAL_SIMILARITY.md)：提交版本声明、共同模板登记/精确 Token 范围、短有效代码依据不足提示已贯通上传、结果与报告。属于未校准的复核背景，不修改生产相似分数或公式，不声称已实现跨版本语义转换或证明误报下降。

> 2026-10-09 数据研究工具增量：[质量复核与离线盲审工作台](proposal/DATA_REVIEW_WORKBENCH.md)已完成。公开标签探索评测单独运行，不修改正式样本资格、生产分数、阈值公式或 API。

> 2026-10-08 已实现范围增量：用户要求的 C、HTML 已接通上传、同语言任务、结构检测、证据和报告。C 为局部绑定子集；HTML 为不执行网页的源码结构分支，使用待校准固定阈值，不纳入算法题画像。跨语言范围仍为有限 Java/Python。论文主评测及可信数据限制见 [多语言进展](proposal/MULTILANGUAGE_PROGRESS.md)，下文完整研究设计不代表全部已实现。

> 本文件定义 CodeRisk / PICAS 项目的完整规格。它用于指导开发、论文撰写、专利交底、软著说明和答辩展示。开发过程中若需求扩展，必须先判断是否服务本文件的研究主线。

---

## 1. 项目名称

### 1.1 中文名称

**基于题目复杂度自适应与置换不变结构表示的代码相似风险检测系统**

### 1.2 英文名称

**CodeRisk: Problem-aware Invariant Code Similarity Risk Detection System**

### 1.3 方法简称

```text
PICAS: Problem-aware Invariant Code Similarity Analysis
```

---

## 2. 项目定位

本项目面向编程作业、算法题提交、课程设计和实验报告代码提交场景，设计并实现一个题目感知型代码相似风险检测系统。

系统不是简单比较两份代码是否相同，而是综合考虑：

1. 代码表层相似度；
2. 代码结构相似度；
3. 标识符替换后的规范结构相似度；
4. 题目复杂度；
5. 解法空间大小；
6. 模板化风险；
7. 自然相似风险；
8. 稀有结构或特殊边界处理相似性；
9. 是否跨语言表达同一算法逻辑；
10. 是否存在可解释的相似证据链。

最终系统输出的是：

```text
风险等级 + 风险分数 + 动态阈值 + 多维指标 + 相似证据 + 人工复核建议
```

而不是直接输出：

```text
抄袭 / 不抄袭
```

---

## 3. 背景与问题

现有代码相似度检测通常关注代码之间的 token、字符串、AST 或结构相似性。这些方法在同语言、同题目、明显复制场景下效果较好，但在编程作业场景中仍存在以下问题。

### 3.1 简单题误报问题

对于 A+B、数组求和、排序、简单循环统计等题目，独立完成的代码也可能高度相似。如果使用统一阈值，容易把自然相似代码误判为高风险。

### 3.2 固定阈值不合理

不同题目的解法空间不同。简单题应提高风险阈值，复杂题则应降低结构相似容忍度。统一使用 75%、80% 或 85% 阈值缺乏题目上下文。

### 3.3 表层伪装问题

提交者可能通过以下方式降低表面相似度：

```text
修改变量名
修改函数名
删除注释
调整格式
交换局部语句
拆分或合并函数
替换等价表达式
AI 辅助改写
跨语言重写
```

系统需要对这些低层次变换具有鲁棒性。

### 3.4 跨语言检测困难

同一题目可能允许 Java、Python、C 等多语言提交。不同语言语法结构差异大，直接 token 或 AST 对比效果有限。

### 3.5 结果不可解释问题

仅输出一个相似度百分比不利于人工复核。系统必须告诉教师或管理员：哪里相似、为什么相似、相似是否超出自然范围。

---

## 4. 总体目标

本项目的总体目标是构建一个具备研究价值、工程完整性和答辩展示性的代码相似风险检测系统。

### 4.1 工程目标

1. 支持题目管理；
2. 支持多份代码上传；
3. 支持 Java/Python，增强支持 C；
4. 支持代码预处理；
5. 支持基础 token/AST 相似度；
6. 支持标识符归一化；
7. 支持题目复杂度评分；
8. 支持动态阈值；
9. 支持风险报告；
10. 支持代码对比和证据展示；
11. 支持实验看板；
12. 支持报告导出。

### 4.2 研究目标

1. 建立题目复杂度与自然相似风险建模方法；
2. 建立置换不变代码结构规范化方法；
3. 建立多维结构相似度融合评分方法；
4. 建立动态阈值风险判定方法；
5. 构建面向伪装改写的评测集；
6. 与固定阈值、token、AST、现有工具进行对比；
7. 通过消融实验验证每个模块贡献。

### 4.3 成果目标

1. 本科毕业设计系统；
2. 软件著作权材料；
3. 发明专利技术交底书草稿；
4. 普通或较有分量的应用型计算机期刊论文；
5. 可展示的 GitHub 项目；
6. 可复现实验报告。

---

## 5. 核心创新点

### 5.1 题目感知动态阈值

传统查重系统常使用固定阈值。本项目根据题目复杂度、解法空间、模板化风险和自然相似风险动态调整阈值。

核心思想：

```text
题目越简单，自然相似风险越高，阈值应提高；
题目越模板化，通用结构权重应降低；
题目越复杂，结构高度相似越可疑；
解法空间越大，两份代码高度相似越值得关注。
```

输出指标：

```text
DifficultyScore
SolutionSpaceScore
TemplateRiskScore
NaturalSimilarityRisk
DynamicThreshold
```

### 5.2 置换不变结构规范化

将变量名、函数名、参数名等标识符替换视作不改变代码核心结构的变换，构建 canonical representation。

支持：

```text
变量名归一化
函数名归一化
参数名归一化
作用域内编号
常量抽象
可交换表达式排序
基础 AST 子树指纹
局部无依赖语句重排，增强项
```

### 5.3 多维相似度融合

系统不依赖单一指标，而是综合：

```text
TokenSimilarity
ASTSimilarity
ControlFlowSimilarity
DataDependencySimilarity
OperationSequenceSimilarity
RareFragmentSimilarity
IdentifierMappingSimilarity
IOPatternSimilarity
BugPatternSimilarity
```

第一阶段必须实现 token、AST、identifier mapping；其他指标按路线逐步增强。

### 5.4 结构化证据输出

系统输出：

1. 相似代码片段；
2. 相似函数；
3. 相似 AST 子结构；
4. 控制结构相似证据；
5. 变量重命名映射；
6. 相同边界条件；
7. 相同错误处理或异常分支；
8. 稀有片段相似说明；
9. 人工复核建议。

### 5.5 跨语言结构表示探索

通过语言无关 IR 对不同语言的核心结构进行统一抽象。

首期优先：

```text
Java <-> Python
```

增强支持：

```text
C
```

未来扩展：

```text
Go
Rust
JavaScript
```

---

## 6. 用户角色

### 6.1 管理员

权限：

1. 管理用户；
2. 管理题目；
3. 创建检测任务；
4. 上传代码集合；
5. 查看所有检测结果；
6. 导出报告；
7. 查看实验看板。

### 6.2 教师 / 助教

权限：

1. 创建课程或题目；
2. 上传学生提交；
3. 发起检测；
4. 查看风险结果；
5. 查看证据；
6. 标注复核结果；
7. 导出复核报告。

### 6.3 普通用户，低优先级

可选支持：

1. 上传个人代码；
2. 查看个人检测结果；
3. 下载个人报告。

第一阶段可以不实现复杂普通用户角色。

---

## 7. 核心业务流程

### 7.1 题目创建流程

```text
输入题目标题
输入题目描述
输入输入格式
输入输出格式
输入约束条件
可选上传参考答案
系统提取题目特征
系统计算题目复杂度和自然相似风险
保存题目特征
```

### 7.2 检测任务流程

```text
选择题目
上传多份代码
识别语言
清洗代码
提取 token / AST / canonical representation
生成代码对
计算多维相似度
计算动态阈值
生成风险等级
定位证据
保存结果
展示报告
```

### 7.3 人工复核流程

```text
查看风险列表
选择高风险代码对
查看左右代码对比
查看相似片段
查看变量映射
查看动态阈值解释
给出复核意见
导出复核报告
```

### 7.4 实验评测流程

```text
选择实验数据集
选择对比方法
运行检测
生成指标
保存配置
输出图表
生成实验报告
```

---

## 8. 功能需求

### 8.1 题目管理模块

必须支持：

1. 新增题目；
2. 修改题目；
3. 查看题目详情；
4. 上传参考答案；
5. 自动提取题目特征；
6. 展示 DifficultyScore、SolutionSpaceScore、TemplateRiskScore、NaturalSimilarityRisk。

### 8.2 代码提交模块

必须支持：

1. 单文件上传；
2. 批量上传；
3. zip 上传，增强项；
4. 语言识别；
5. 文件大小限制；
6. 编码格式检测；
7. 解析失败提示；
8. 提交元数据保存。

### 8.3 检测任务模块

必须支持：

1. 创建任务；
2. 启动任务；
3. 查询任务状态；
4. 失败重试；
5. 查看任务日志；
6. 任务取消，增强项。

任务状态：

```text
CREATED
UPLOADED
ANALYZING
COMPLETED
FAILED
CANCELLED
```

### 8.4 代码分析模块

必须支持：

1. 注释删除；
2. 空白规范化；
3. token 提取；
4. AST 提取；
5. 标识符归一化；
6. 结构指纹生成；
7. 相似度计算；
8. 证据定位。

### 8.5 题目复杂度评分模块

必须支持：

1. 题目文本长度特征；
2. 输入输出复杂度；
3. 约束条件数量；
4. 参考答案行数；
5. 参考答案函数数量；
6. 参考答案圈复杂度，增强项；
7. 控制结构数量；
8. 数据结构种类；
9. 模板关键词识别；
10. 历史提交分布，增强项。

### 8.6 风险报告模块

必须支持：

1. 总体风险分数；
2. 动态阈值；
3. 风险等级；
4. 多维相似度；
5. 代码对比；
6. 证据列表；
7. 复核建议；
8. PDF/HTML/Markdown 导出，至少实现一种。

### 8.7 实验模块

必须支持：

1. 数据集管理；
2. 方法配置；
3. 实验运行；
4. 指标计算；
5. 结果保存；
6. 图表展示；
7. 消融实验。

---

## 9. 非功能需求

### 9.1 可复现性

1. 所有算法参数应配置化；
2. 每次实验保存配置；
3. 每次实验保存数据集版本；
4. 每次实验保存运行时间；
5. 论文图表必须能由脚本生成。

### 9.2 可解释性

1. 风险分数必须可拆解；
2. 动态阈值必须给出解释；
3. 证据必须对应具体代码片段；
4. 前端必须展示证据链。

### 9.3 鲁棒性

1. 代码解析失败不能导致任务整体崩溃；
2. 单份代码异常应记录为失败提交；
3. 分析服务异常应返回明确错误；
4. 大批量任务应支持异步处理。

### 9.4 性能

本科毕设阶段目标：

```text
单题 50 份代码以内可稳定分析
单个代码对基础分析 < 3 秒，视代码大小可调整
任务状态可查询
前端结果页响应流畅
```

期刊增强阶段目标：

```text
支持 100-500 份代码离线实验
实验脚本可批处理
指标计算可复现
```

### 9.5 安全性

1. 上传文件类型限制；
2. 上传文件大小限制；
3. 不执行用户上传代码；
4. 文件路径隔离；
5. 防止路径穿越；
6. API 基础鉴权；
7. 敏感配置不提交仓库。

---

## 10. 核心数据对象

### 10.1 Question

```text
id
title
description
input_format
output_format
constraints_text
reference_solution_path
difficulty_score
solution_space_score
template_risk_score
natural_similarity_risk
created_at
updated_at
```

### 10.2 Submission

```text
id
question_id
student_id
language
file_name
raw_code_path
clean_code_path
parser_status
created_at
```

### 10.3 DetectionTask

```text
id
question_id
task_name
status
total_submissions
total_pairs
finished_pairs
created_by
created_at
finished_at
```

### 10.4 AnalysisResult

```text
id
task_id
submission_a_id
submission_b_id
token_similarity
ast_similarity
control_flow_similarity
data_dependency_similarity
rare_fragment_similarity
identifier_mapping_similarity
weighted_similarity_score
dynamic_threshold
risk_margin
calibrated_risk_score
risk_level
exceed_threshold
margin_scale
formula_version
algorithm_version
metric_config_hash
created_at
```

### 10.5 Evidence

```text
id
result_id
evidence_type
code_a_start_line
code_a_end_line
code_b_start_line
code_b_end_line
similarity_score
description
metadata_json
```

---

## 11. 风险等级规则

风险等级必须以 `FORMULA_SPEC.md` 为真源，依据 `risk_margin = weighted_similarity_score - dynamic_threshold` 计算：

```text
LOW       risk_margin < -0.10
MEDIUM    -0.10 <= risk_margin < 0
ELEVATED  0 <= risk_margin < 0.10
HIGH      risk_margin >= 0.10
```

说明：

1. 风险等级必须结合动态阈值；
2. 不得只用固定 60/75/85 分界；
3. 不得使用 CRITICAL / 极高风险；
4. UI 中必须展示动态阈值来源、risk_margin 和人工复核建议；
5. 系统不得输出“抄袭成立”。

---

## 12. 版本范围

### 12.1 V1 基础可运行版

目标：完成最小闭环。

必须包含：

1. 题目创建；
2. Java/Python 上传；
3. 代码清洗；
4. token 相似度；
5. AST 节点类型相似度；
6. 标识符归一化；
7. 风险结果列表；
8. 代码对比页。

### 12.2 V2 本科毕设版

目标：体现核心创新。

必须包含：

1. 题目复杂度评分；
2. 自然相似风险；
3. 动态阈值；
4. 多维相似度融合；
5. 结构化证据输出；
6. 报告导出；
7. 基础实验对比。

### 12.3 V3 期刊增强版

目标：支撑投稿。

必须包含：

1. L0-L8 伪装数据集；
2. 固定阈值对比；
3. token/AST/本文方法对比；
4. JPlag/Dolos 对比，至少导入外部结果；
5. 消融实验；
6. 失败案例分析；
7. 统计图表；
8. 论文复现实验脚本。

### 12.4 V4 研究扩展版

目标：进一步增强。

可选包含：

1. Java/Python/C 跨语言 IR；
2. 控制流图相似度；
3. 数据依赖图相似度；
4. AI 改写检测；
5. 大规模 benchmark；
6. 统计显著性分析。

---

## 13. 明确不做内容

为避免范围失控，以下内容不作为核心目标：

```text
在线运行学生代码
自动判罚学生
完整教务系统
复杂班级管理
复杂权限矩阵
商业 SaaS 多租户
在线 IDE
AI 自动审判抄袭
全语义等价证明
大规模分布式计算平台
```

---

## 14. 答辩展示主线

推荐答辩按如下顺序：

1. 普通代码查重为什么会误报简单题；
2. 本系统如何分析题目复杂度和自然相似风险；
3. 本系统如何进行置换不变规范化；
4. 本系统如何计算多维相似度；
5. 本系统如何动态生成阈值；
6. 本系统如何输出证据而不是直接判抄袭；
7. 实验如何证明动态阈值降低误报；
8. 实验如何证明规范化提升伪装检测能力；
9. 系统演示；
10. 局限和展望。

---

## 15. 论文贡献表述建议

论文中可写为：

1. 提出一种面向编程作业场景的题目感知代码相似风险检测框架；
2. 设计题目复杂度、解法空间、模板化风险与自然相似风险联合建模方法；
3. 设计置换不变的代码结构规范化表示，用于增强对变量名、函数名替换等伪装方式的鲁棒性；
4. 设计融合 token、AST、控制流、数据依赖和稀有片段的多维相似度评分方法；
5. 构建分层伪装数据集并通过对比实验和消融实验验证方法有效性。

---

## 16. 验收标准

项目至少满足以下条件才算阶段完成：

```text
[ ] 能创建题目
[ ] 能上传多份代码
[ ] 能生成代码对
[ ] 能完成 Java/Python 基础解析
[ ] 能计算 token 相似度
[ ] 能计算 AST 相似度
[ ] 能完成标识符归一化
[ ] 能计算题目复杂度分数
[ ] 能计算动态阈值
[ ] 能输出风险等级
[ ] 能输出相似证据
[ ] 能前端查看代码对比
[ ] 能导出或查看报告
[ ] 能运行至少一组对比实验
[ ] 能保存实验结果
```

---

## 17. 自检结论

本规格文件已按以下原则设计：

1. 主线明确：题目感知型代码相似风险检测；
2. 创新点明确：动态阈值、置换不变、多维证据；
3. 工程边界明确：不做普通管理系统；
4. 版本范围明确：V1 到 V4 逐步增强；
5. 成果导向明确：毕设、期刊、专利、软著均可复用。



### AnalysisResult 字段口径补充

`analysis_result` 主结果记录必须保存用于复现生产版公式的核心字段：

```text
id
task_id
submission_a_id
submission_b_id
weighted_similarity_score
dynamic_threshold
risk_margin
calibrated_risk_score
risk_level
exceed_threshold
margin_scale
formula_version
algorithm_version
metric_config_hash
created_at
```

`analysis_metric`：单独保存每个相似度指标、权重、版本和解释，不把所有指标堆入主结果表。

`evidence`：单独保存结构化证据、严重程度、代码行号和 `metadata_json`。
