# PAPER_OUTLINE.md

> 本文件定义 CodeRisk / PICAS 项目的期刊论文大纲、章节内容、图表安排、创新点表达和写作边界。论文写作必须围绕“题目感知 + 置换不变 + 多维证据 + 动态阈值”展开，避免写成普通系统开发报告。

---

## 1. 论文定位

### 1.1 推荐中文题目

```text
基于题目复杂度自适应与置换不变表示的代码相似风险检测方法研究
```

备选：

```text
面向编程作业的题目感知代码相似风险检测方法与系统实现
```

```text
基于动态阈值与结构规范化的多语言代码相似风险评估方法
```

### 1.2 推荐英文题目

```text
PICAS: Problem-aware Invariant Code Similarity Analysis for Programming Assignments
```

或：

```text
A Problem-aware and Permutation-invariant Approach to Code Similarity Risk Detection
```

### 1.3 论文类型

更适合定位为：

```text
计算机应用类论文
软件工程应用类论文
教育信息化与编程作业管理交叉类论文
源代码相似度检测改进方法论文
```

不建议定位为：

```text
纯理论算法论文
顶级代码克隆检测理论论文
大模型代码生成检测论文
```

### 1.4 论文核心一句话

```text
本文针对编程作业代码查重中简单题自然相似误报、固定阈值不合理以及标识符替换伪装等问题，提出一种题目感知与置换不变的代码相似风险检测方法 PICAS，并通过动态阈值、多维结构相似度和结构化证据输出提升相似风险评估的准确性与可解释性。
```

---

## 2. 推荐摘要结构

### 2.1 中文摘要模板

```text
编程作业代码相似度检测是高校程序设计课程和在线评测平台中的重要任务。现有方法多基于字符串、Token、抽象语法树或代码指纹计算代码之间的相似度，但在实际教学场景中仍存在简单题自然相似导致误报、不同题目使用统一阈值不合理、变量名替换等表层伪装影响检测结果以及检测结果可解释性不足等问题。针对上述问题，本文提出一种面向编程作业的题目感知与置换不变代码相似风险检测方法 PICAS。该方法从题目上下文构建题目画像，对代码进行标识符规范化并融合稳定的 Token/AST 指标，以动态阈值输出相似风险等级和结构化证据；有限跨语言 IR 与轻量结构摘要只作为零生产权重的探索性能力。当前 91-pair synthetic seed 仅用于验证数据门禁、校准、基线对齐和论文表格流程。摘要中的真实效果、外部基线比较和改写鲁棒性结论必须在可追溯 validation/test 数据冻结并重跑后填写，不得从 seed placeholder 推导。
```

### 2.2 关键词

```text
代码相似度检测；代码查重；编程作业；动态阈值；置换不变表示；抽象语法树；代码克隆检测；可解释性
```

### 2.3 英文关键词

```text
Code similarity detection; Programming assignments; Dynamic threshold; Permutation-invariant representation; Abstract syntax tree; Code clone detection; Explainability
```

---

## 3. 论文贡献点写法

### 3.1 推荐贡献点

论文贡献建议写成 4 条：

```text
（1）提出一种题目感知的相似风险校准机制，从题目复杂度、解法空间、模板化风险和自然相似风险等角度建模不同题目的自然相似程度，并据此生成动态检测阈值。

（2）提出一种置换不变代码结构规范化方法，对变量名、函数名、参数名、可交换表达式和部分局部无依赖语句进行规范化，增强系统对表层伪装改写的鲁棒性。

（3）设计一种融合 Token、AST、控制流、数据依赖、操作序列和稀有片段的多维相似风险评分方法，并输出风险等级、动态阈值和结构化证据链。

（4）设计可扩展的数据集 schema、隔离校验、外部基线对齐和消融实验工具链；真实人工、AI-assisted 和 external 样本及正式效果结论待可追溯数据补齐后验证。
```

### 3.2 不建议写的贡献

不要写：

```text
首次提出代码查重算法。
完全解决跨语言代码抄袭检测。
可以自动判断学生是否抄袭。
全面超越所有现有工具。
基于群论的全新代码查重理论。
```

### 3.3 更稳妥的表述

建议写：

```text
面向编程作业场景的改进方法。
在自建可追溯数据集和外部基线上的正式表现待真实数据冻结后填写；synthetic seed 数值不得写入最终结论。
为人工复核提供辅助证据。
探索有限跨语言结构相似风险识别。
借鉴置换不变性思想进行结构规范化。
```

---

## 4. 论文整体结构

推荐 7 章结构：

```text
第 1 章 绪论
第 2 章 相关工作与技术基础
第 3 章 问题定义与总体框架
第 4 章 PICAS 方法设计
第 5 章 系统实现
第 6 章 实验设计与结果分析
第 7 章 总结与展望
```

如果目标期刊篇幅较短，可压缩为 5 个大节：

```text
1 引言
2 相关工作
3 方法设计
4 实验与分析
5 系统实现与总结
```

---

## 5. 第 1 章：绪论

### 5.1 研究背景

内容要点：

```text
程序设计课程和在线评测平台中，编程作业提交量大。
教师需要辅助工具发现高度相似代码对。
传统代码相似度检测方法常用字符串、Token、AST、指纹等技术。
随着 AI 辅助编程发展，代码改写和表层伪装更容易。
```

### 5.2 问题引出

重点写四个问题：

```text
简单题自然相似导致误报。
固定阈值无法适应不同题目。
标识符替换和结构轻度改写影响检测稳定性。
相似度百分比缺乏可解释证据。
```

### 5.3 研究意义

包括：

```text
提高编程作业相似风险分析效率。
降低简单题误报导致的人工复核压力。
为教师提供可解释证据。
为代码查重系统引入题目上下文建模思路。
```

### 5.4 本文主要工作

对应贡献点。

### 5.5 本章小结

简要总结研究背景、问题和本文目标。

---

## 6. 第 2 章：相关工作与技术基础

### 6.1 代码相似度检测与代码克隆检测

介绍：

```text
Type-1 Clone：完全相同或仅空白/注释不同
Type-2 Clone：标识符、类型、字面量不同
Type-3 Clone：存在语句增删改
Type-4 Clone：语义相似但结构不同
```

对应本项目：

```text
PICAS 主要面向 Type-1、Type-2、部分 Type-3 和有限跨语言结构相似，不声称完全解决 Type-4 语义克隆。
```

### 6.2 字符串与 Token 方法

写：

```text
优点：实现简单，速度快。
缺点：对变量名替换、语句重排、函数拆分敏感。
```

### 6.3 AST 与结构方法

写：

```text
AST 能捕获代码语法结构，比 token 更稳健。
但不同语言 AST 差异较大，对跨语言和语义等价仍有限。
```

### 6.4 程序依赖与控制流方法

写：

```text
CFG/PDG 可以刻画更深层结构，但实现成本更高。
本文采用轻量控制流和数据依赖签名作为工程折中。
```

### 6.5 现有工具

介绍：

```text
MOSS
JPlag
Dolos
```

注意写法：

```text
这些工具在代码相似度检测中具有代表性，但一般不直接建模题目自然相似风险和动态阈值问题。
```

### 6.6 AI 改写带来的新挑战

写：

```text
大模型可以辅助重写代码，使代码表面差异变大。
这要求检测方法更关注结构、行为线索和证据链。
```

### 6.7 本章小结

引出：

```text
现有方法多关注代码之间的相似性，较少考虑题目上下文和自然相似风险，因此本文提出 PICAS。
```

---

## 7. 第 3 章：问题定义与总体框架

### 7.1 问题定义

定义输入：

```text
题目 Q
提交集合 S = {s1, s2, ..., sn}
参考实现 R（可选）
检测配置 C
```

定义输出：

```text
每个代码对的风险分数 RiskScore
动态阈值 DynamicThreshold
风险等级 RiskLevel
证据集合 EvidenceSet
人工复核建议 ReviewSuggestion
```

### 7.2 任务边界

明确：

```text
本文输出相似风险，不直接判定抄袭。
本文关注编程作业场景，不处理通用软件仓库级克隆检测。
本文跨语言检测限定在 Java/Python/C 的常见作业结构。
```

### 7.3 总体框架

放图：

```text
图 1：PICAS 总体流程图
```

流程：

```text
题目输入与特征提取
代码预处理
多语言解析
置换不变规范化
多维相似度计算
题目感知动态阈值
风险等级与证据输出
```

### 7.4 系统架构概述

简述：

```text
Spring Boot 主业务系统
Python analysis-service 算法服务
MySQL 存储任务和结果
Vue 前端展示报告和证据
```

### 7.5 本章小结

说明后续第四章详细展开方法。

---

## 8. 第 4 章：PICAS 方法设计

这是论文核心章节。

### 8.1 章节结构

```text
4.1 题目复杂度与自然相似风险建模
4.2 代码预处理与多语言解析
4.3 置换不变代码结构规范化
4.4 多维相似度计算
4.5 题目感知动态阈值生成
4.6 风险等级与结构化证据输出
4.7 算法复杂度分析
```

---

## 9. 4.1 题目复杂度与自然相似风险建模

### 9.1 写作目标

说明系统为什么要看题目，而不是只看代码。

### 9.2 特征设计

写：

```text
题目描述长度
输入输出格式复杂度
约束条件数量
样例数量
参考答案代码行数
参考答案函数数量
圈复杂度
控制结构数量
数据结构种类
历史提交相似度分布
```

### 9.3 四个核心分数

```text
DifficultyScore
SolutionSpaceScore
TemplateRiskScore
NaturalSimilarityRisk
```

### 9.4 公式表达

建议用轻量公式，不要堆太复杂数学。

示例：

```text
ProblemFeature(Q) = [f1, f2, ..., fk]
```

```text
NaturalSimilarityRisk = g(DifficultyScore, SolutionSpaceScore, TemplateRiskScore, HistoricalSimilarity)
```

### 9.5 解释

写清楚：

```text
题目越简单，自然相似风险越高。
模板化程度越高，自然相似风险越高。
解法空间越大，结构高度相似越可疑。
```

---

## 10. 4.2 代码预处理与多语言解析

### 10.1 内容

包括：

```text
注释删除
空白规范化
编码处理
语言识别
Token 提取
AST 构建
函数列表提取
变量列表提取
控制结构提取
```

### 10.2 语言支持

写：

```text
Java 和 Python 为主要支持语言。
C 为增强支持语言。
```

### 10.3 解析失败处理

说明：

```text
解析失败时保留 token 和文本级特征，不直接中断整个任务。
```

---

## 11. 4.3 置换不变代码结构规范化

### 11.1 写作目标

说明如何抵抗变量名、函数名、参数名替换。

### 11.2 标识符归一化

示例：

```java
int sum = a + b;
```

规范化为：

```text
TYPE VAR_1 = VAR_2 + VAR_3
```

### 11.3 作用域感知映射

说明：

```text
不同作用域中的变量独立编号。
同一作用域中按首次出现顺序编号。
```

### 11.4 函数名和参数名归一化

说明：

```text
自定义函数名归一化为 FUNC_1、FUNC_2。
入口函数、语言内置函数和标准库函数保留语义标签。
```

### 11.5 可交换表达式规范化

说明：

```text
a + b 与 b + a 归一化为同一结构。
```

但必须强调：

```text
只处理安全可交换运算，不处理可能改变语义的表达式。
```

### 11.6 局部无依赖语句重排

说明：

```text
只有在不存在数据依赖、控制依赖和副作用时，才允许生成顺序无关签名。
```

### 11.7 AST 子树规范指纹

说明：

```text
为规范化 AST 子树生成 hash，用于结构匹配。
```

---

## 12. 4.4 多维相似度计算

### 12.1 指标列表

```text
TokenSimilarity
CanonicalTokenSimilarity
ASTSimilarity
CanonicalASTSimilarity
ControlFlowSimilarity
DataDependencySimilarity
OperationSequenceSimilarity
RareFragmentSimilarity
IdentifierMappingSimilarity
LanguageIndependentIRSimilarity
```

### 12.2 稀有片段相似度

重点写，因为这是可解释性亮点。

稀有片段包括：

```text
特殊边界条件
魔法数
异常分支
罕见 API 组合
特殊递归终止条件
特殊数组下标处理
相同错误处理逻辑
```

### 12.3 综合风险分数

示例：

生产版必须与 `FORMULA_SPEC_V1` 一致：

```text
weighted_similarity_score = Σ wi * Sim_i
dynamic_threshold = f(problem_profile)
risk_margin = weighted_similarity_score - dynamic_threshold
calibrated_risk_score = clamp(0.5 + risk_margin / margin_scale, 0, 1)
```

NaturalSimilarityRisk 与 TemplateRiskScore 通过动态阈值校准，不得在生产最终分数中再次使用无界 penalty。权重或阈值参数只能在 validation 上校准，test 只做最终评估。

---

## 13. 4.5 题目感知动态阈值生成

### 13.1 基本思想

```text
简单题提高阈值。
模板题提高阈值或降低通用结构权重。
复杂题适当降低阈值。
解法空间大的题中，结构相似更可疑。
```

### 13.2 公式示例

```text
DynamicThreshold(Q) = BaseThreshold
                    + α * NaturalSimilarityRisk
                    + β * TemplateRiskScore
                    - γ * DifficultyScore
                    - δ * SolutionSpaceScore
```

### 13.3 阈值裁剪

```text
DynamicThreshold ∈ [ThresholdMin, ThresholdMax]
```

### 13.4 解释生成

系统报告中要能说明：

```text
该题自然相似风险较高，因此阈值被提高。
该题解法空间较大，因此结构相似更可疑。
```

---

## 14. 4.6 风险等级与结构化证据输出

### 14.1 风险等级

```text
LOW
MEDIUM
ELEVATED
HIGH
```

### 14.2 证据类型

```text
相似代码片段
相似函数
相似 AST 子树
相似控制流结构
变量重命名映射
相同边界条件
相同异常处理
稀有片段相似
跨语言 IR 对齐结构
```

### 14.3 人工复核建议

报告中必须写：

```text
本系统输出为相似风险提示，需要结合课程规则和人工复核后判断。
```

---

## 15. 4.7 算法复杂度分析

### 15.1 两两比较复杂度

若同题提交数为 n：

```text
pair_count = n(n-1)/2
```

### 15.2 优化策略

```text
先粗筛再精算
按 token fingerprint 召回候选
分块计算
缓存解析结果
缓存规范化结果
并行分析
```

### 15.3 论文表述

写成工程优化，不要强行声称理论最优。

---

## 16. 第 5 章：系统实现

### 16.1 系统架构

对应 `ARCHITECTURE.md`。

内容：

```text
前端 Vue
Spring Boot 后端
Python 分析服务
MySQL
Redis 可选
文件存储
实验脚本
```

### 16.2 功能模块

```text
用户与权限模块
题目管理模块
代码提交模块
检测任务模块
分析结果模块
证据展示模块
实验管理模块
报告导出模块
```

### 16.3 数据库设计

对应 `DATABASE_SCHEMA.md`。

重点表：

```text
question
submission
detection_task
analysis_result
evidence
problem_feature
similarity_metric
experiment_run
experiment_result
```

### 16.4 接口设计

对应 `API_SPEC.md`。

### 16.5 前端展示

重点截图：

```text
任务创建页
题目复杂度页
风险总览页
代码对比页
证据链页面
实验看板页
```

### 16.6 本章写作边界

不要把系统实现写成论文核心。系统实现服务于方法验证。

---

## 17. 第 6 章：实验设计与结果分析

### 17.1 数据集

写：

```text
自建编程作业数据集 CodeRisk-PA-v1
题目数量
提交数量
语言分布
难度分布
变换等级分布
标签分布
```

### 17.2 对比方法

对应 `BASELINES_AND_BENCHMARKS.md`。

包括：

```text
Raw Text
Token Similarity
AST Similarity
JPlag
Dolos
PICAS-NoDT
PICAS-NoCanon
PICAS-Full
```

### 17.3 评价指标

```text
Precision
Recall
F1-score
FPR
FNR
AUC-PR
Precision@K
Average Time
```

### 17.4 实验 1：动态阈值有效性

放：

```text
固定阈值 vs 动态阈值
不同题目组 FPR/Recall/F1
```

### 17.5 实验 2：置换不变规范化有效性

放：

```text
L1-L6 变换等级下 Recall/FNR/SRR
```

### 17.6 实验 3：多维融合与消融实验

放：

```text
PICAS full 与各消融版本对比
```

### 17.7 实验 4：跨语言检测

放：

```text
Java-Python
Java-C
Python-C
```

### 17.8 实验 5：AI 改写鲁棒性

放：

```text
L8 AI rewrite 下不同方法召回率
```

### 17.9 实验 6：证据输出案例分析

放：

```text
高风险案例
自然相似降级案例
失败案例
```

### 17.10 实验 7：性能测试

放：

```text
不同提交规模下运行时间
报告生成时间
解析失败率
```

### 17.11 本章小结

总结：

```text
PICAS 在降低简单题误报、抵抗表层伪装、提供解释证据方面具有优势。
```

---

## 18. 第 7 章：总结与展望

### 18.1 工作总结

写：

```text
本文提出了 PICAS 方法。
实现了完整系统。
构建了 synthetic seed 与数据录入/校验工具链；正式实验数据集仍待补充可追溯样例。
通过对比和消融验证了方法有效性。
```

### 18.2 不足

必须诚实写：

```text
跨语言 IR 覆盖有限。
数据集规模仍有限。
动态阈值参数仍依赖规则和验证集校准。
对强语义等价改写识别能力有限。
AI 改写样本规模有待扩大。
```

### 18.3 展望

```text
引入更强的程序依赖图。
扩展更多语言。
结合运行行为相似度。
构建更大规模公开评测集。
引入教师反馈闭环优化阈值。
```

---

## 19. 论文图表安排

### 19.1 图清单

```text
图 1：系统应用场景图
图 2：PICAS 总体流程图
图 3：题目复杂度评分流程图
图 4：置换不变规范化示例
图 5：语言无关 IR 映射示意图
图 6：系统架构图
图 7：动态阈值分布图
图 8：不同题目组误报率对比图
图 9：不同变换等级召回率对比图
图 10：证据输出界面截图
```

### 19.2 表清单

```text
表 1：相关方法对比表
表 2：题目特征定义表
表 3：相似度指标定义表
表 4：数据集统计表
表 5：对比方法说明表
表 6：总体实验结果表
表 7：题目分组结果表
表 8：变换等级结果表
表 9：消融实验结果表
表 10：性能测试结果表
```

---

## 20. 相关工作对比表模板

| 方法/工具 | 主要特征 | 是否考虑题目难度 | 是否动态阈值 | 是否支持证据输出 | 是否支持跨语言 |
|---|---|---:|---:|---:|---:|
| 字符串相似度 | 表层文本比较 | 否 | 否 | 弱 | 否 |
| Token 方法 | token 序列或集合 | 否 | 否 | 弱 | 弱 |
| AST 方法 | 语法树结构 | 否 | 否 | 中 | 弱 |
| JPlag | 成熟代码相似度工具 | 否/有限 | 否/有限 | 中 | 视语言支持 |
| Dolos | 多语言查重与可视化 | 否/有限 | 否/有限 | 中 | 视工具能力 |
| PICAS | 题目感知 + 规范化 + 动态阈值 | 是 | 是 | 强 | 有限支持 |

注意：

```text
表中对 JPlag/Dolos 的能力描述必须以实际实验版本为准。
不要贬低现有工具。
```

---

## 21. 方法命名规范

全文统一使用：

```text
PICAS
```

第一次出现：

```text
Problem-aware Invariant Code Similarity Analysis, PICAS
```

中文：

```text
题目感知与置换不变代码相似风险分析方法
```

不要混用：

```text
CodeRisk 算法
动态查重算法
群论查重算法
```

`CodeRisk` 用作系统名称，`PICAS` 用作方法名称。

---

## 22. 期刊投稿侧重点

### 22.1 应用型计算机期刊

强调：

```text
系统完整性
算法改进
实验对比
工程可用性
```

### 22.2 软件工程类期刊

强调：

```text
需求场景
架构设计
工具链
实验评测
可解释报告
```

### 22.3 教育信息化类期刊

强调：

```text
编程作业管理
教师人工复核
简单题误报问题
教学公平性辅助
```

### 22.4 不建议主攻方向

```text
纯 AI 检测期刊
纯理论算法期刊
顶级软件工程会议
```

除非后续实验规模和理论贡献显著增强。

---

## 23. 写作边界与风险控制

### 23.1 关于抄袭判断

必须写：

```text
本文方法用于相似风险提示，最终判断仍需人工复核。
```

### 23.2 关于跨语言

必须写：

```text
本文跨语言检测主要基于语言无关结构表示，对 Java/Python/C 常见编程作业结构进行有限支持。
```

### 23.3 关于动态阈值

必须写：

```text
动态阈值不是绝对标准，而是结合题目特征的风险校准策略。
```

### 23.4 关于大模型

如果使用 LLM 辅助：

```text
LLM 仅用于辅助题目分析或生成解释，不直接作为最终相似风险判定依据。
```

---

## 24. 专利与论文顺序提醒

如果同时准备专利和论文：

```text
先整理专利技术交底书。
先提交专利申请。
再公开论文、GitHub、完整技术细节。
```

论文中可以保留必要方法描述，但在专利提交前不要公开完整实现细节。

---

## 25. 论文和系统文档对应关系

| 论文内容 | 对应项目文档 |
|---|---|
| 研究背景与问题 | PROJECT_SPEC.md |
| 总体框架 | ARCHITECTURE.md |
| 算法方法 | ALGORITHM_SPEC.md |
| 规范化方法 | CANONICALIZATION_SPEC.md |
| 动态阈值 | PROBLEM_AWARE_SCORING.md |
| 数据库与实现 | DATABASE_SCHEMA.md / API_SPEC.md |
| 实验设计 | EXPERIMENT_PLAN.md |
| 对比方法 | BASELINES_AND_BENCHMARKS.md |
| 测试与性能 | TEST_PLAN.md |

---

## 26. 最低可投稿版本要求

如果想形成一篇还算有分量的期刊论文，至少完成：

```text
1. Java + Python 支持
2. 题目复杂度评分
3. 动态阈值
4. 置换不变规范化
5. 多维相似度融合
6. 风险证据输出
7. 自建实验数据集
8. 固定阈值对比
9. Token/AST 对比
10. 至少一个外部工具对比
11. 消融实验
12. 失败案例分析
```

---

## 27. 推荐写作顺序

```text
1. 先写第 3 章总体框架。
2. 再写第 4 章方法设计。
3. 同步跑实验，生成第 6 章表格。
4. 再补第 2 章相关工作。
5. 最后写第 1 章绪论和摘要。
```

不要先写摘要，因为实验结果没出来前摘要容易虚。

---

## 28. 一句话总结

```text
论文必须把 CodeRisk 写成一个由 PICAS 方法驱动的研究型系统，而不是一个普通代码查重网站；核心说服力来自题目感知动态阈值、置换不变规范化、多维证据输出和可复现实验对比。
```


## 表述边界补充

禁止宣称 PICAS 能准确判断抄袭、完整识别 AI 改写、证明两个程序语义等价或完整解决跨语言查重。推荐结论表述为：在自建编程作业数据集上，PICAS 相比固定阈值方法能够降低简单题自然相似导致的误报，并在标识符替换和格式调整等表层改写场景下保持更稳定的相似风险评估。

## 29. Research V4 当前论文可用结果

当前只可写为“91-pair synthetic seed toolchain pre-experiment”。表 4-10 可引用 `data/artifacts/experiments/PICAS-RESEARCH-V4-SEED-20260624-R2/paper_tables/` 中的 CSV，但必须同时披露：所有样例均为 synthetic seed、4 个 AI_REWRITE 是排除指标的 placeholder、仍缺 manual/verified ai_assisted/external 数据、Dolos 未运行、旧 7 个跨语言 case 的 split 未预注册。

seed 数据可支持的克制流程结论：数据门禁实现 0 problem/source/hash overlap；canonical token 在 rename seed case 上均值 1.0，高于 raw token 0.250836；validation-only 校准能够完整记录参数选择且没有使用 test 选参；JPlag 能按 manifest 对齐 72 pair。seed 数值只能证明工具链可运行，不能证明 PICAS 对真实学生提交更优。

正式论文结论必须等待可追溯数据补充后重跑。尤其不得把 placeholder 写成 AI-assisted 实验，不得宣称 AI 改写鲁棒性；跨语言 experimental composite 的 seed F1 0.6667/FPR 1.0 只用于说明 common structure 误报和 unsupported syntax 漏报仍然存在。摘要、贡献点和结论中的效果句应在真实 test 结果冻结后填写。

## 30. Research V4 论文材料生成流程

论文表格、失败案例、threats to validity、limitations、future work 和稳定/实验功能边界的具体取材流程见：

```text
coderisk/experiment/PAPER_MATERIALS_GUIDE.md
coderisk/experiment/RESULT_INTERPRETATION_GUIDE.md
coderisk/experiment/RESEARCH_V4_CHECKLIST.md
```

写作顺序建议：

```text
1. 按 DATA_COLLECTION_GUIDE.md 补充 manual、verified ai_assisted、external 数据。
2. 按 RUN_RESEARCH_V4.md 校验数据、运行 JPlag、运行完整实验。
3. 从 paper_tables/ 引用表格，从 case_analysis/ 选择失败案例。
4. 在 TEST_REPORT.md、EXPERIMENT_PLAN.md 和本文件中同步最新 run id、数据来源比例和结论边界。
5. 只把 synthetic seed 写为流程验证；正式效果句等待真实 test 结果冻结后填写。
```
