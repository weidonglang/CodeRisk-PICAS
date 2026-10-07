# BASELINES_AND_BENCHMARKS.md

> 本文件定义 CodeRisk / PICAS 项目的对比基线、基准数据、运行协议和结果报告规范。它用于保证实验不是“自说自话”，而是能和固定阈值、传统 token/AST 方法以及 JPlag、Dolos、MOSS 等工具形成可解释对比。

---

## 1. 文件目标

### 1.1 为什么必须有基线

如果只展示 PICAS 自己的结果，论文说服力不足。必须回答：

```text
PICAS 相比传统方法提升在哪里？
PICAS 相比固定阈值方法提升在哪里？
PICAS 相比成熟工具在编程作业场景中有什么差异？
PICAS 的哪些模块真正有贡献？
```

### 1.2 基线分类

本项目基线分为五类：

```text
B0：弱基线
B1：传统相似度基线
B2：结构相似度基线
B3：外部工具基线
B4：PICAS 消融基线
```

### 1.3 基线选择原则

1. 既要有简单基线，也要有强基线。
2. 既要有内部可控实现，也要有外部成熟工具。
3. 所有基线必须使用同一测试集。
4. 阈值调优必须在验证集进行。
5. 不能只挑对 PICAS 有利的样本。
6. 对外部工具不支持的功能，要清楚说明边界。

---

## 2. 外部工具背景说明

### 2.1 MOSS

MOSS 是 Stanford 提供的经典程序相似度检测系统，主要应用于编程课作业中的程序相似性检测。它适合作为历史经典基线或背景对照。

注意：

```text
MOSS 适合说明传统程序相似度检测背景。
是否作为实际实验基线，取决于账号、调用限制、课程使用许可和数据隐私要求。
```

### 2.2 JPlag

JPlag 是常用的源代码相似度检测工具，支持多种编程语言，并提供命令行和报告能力。它适合作为本项目最重要的外部强基线之一。

### 2.3 Dolos

Dolos 是面向编程练习的源代码相似度检测工具，支持多语言，并利用 tree-sitter 解析器库。它提供交互式报告和可视化能力，适合作为另一个外部强基线。

### 2.4 相关注意

外部工具输出的“相似”不等价于确认抄袭。PICAS 也必须坚持输出“相似风险”和“人工复核建议”。

---

## 3. 基线总表

| 编号 | 方法 | 类型 | 是否必做 | 主要用途 |
|---|---|---|---|---|
| B0-1 | Random Score | 弱基线 | 可选 | 检查实验流程 |
| B0-2 | Code Length Heuristic | 弱基线 | 可选 | 检查长度偏置 |
| B1-1 | Raw Text Similarity | 字符串 | 必做 | 表层相似对比 |
| B1-2 | Normalized Text Similarity | 字符串 | 必做 | 去空白/注释后对比 |
| B1-3 | Token Jaccard | Token | 必做 | token 集合相似 |
| B1-4 | Token Edit Distance | Token | 必做 | token 序列相似 |
| B2-1 | Raw AST Similarity | AST | 必做 | 基础结构对比 |
| B2-2 | AST Fingerprint | AST | 必做 | 树结构指纹对比 |
| B2-3 | CFG Signature | 控制流 | 增强 | 控制流结构对比 |
| B3-1 | JPlag | 外部工具 | 期刊增强必做 | 成熟工具强基线 |
| B3-2 | Dolos | 外部工具 | 期刊增强必做 | 多语言工具强基线 |
| B3-3 | MOSS | 外部工具 | 可选 | 经典工具对照 |
| B4-1 | PICAS w/o DynamicThreshold | 消融 | 必做 | 验证动态阈值贡献 |
| B4-2 | PICAS w/o Canonicalization | 消融 | 必做 | 验证规范化贡献 |
| B4-3 | PICAS w/o RareFragment | 消融 | 必做 | 验证稀有片段贡献 |
| B4-4 | PICAS w/o IR | 消融 | 增强 | 验证跨语言 IR 贡献 |

---

## 4. 弱基线

### 4.1 Random Score

方法：

```text
为每个代码对随机生成 0-1 分数。
```

用途：

```text
验证评估脚本没有明显错误。
```

不要在论文主结果中过度展示。

### 4.2 Code Length Heuristic

方法：

```text
根据代码行数、token 数、函数数差异估计相似风险。
```

示例：

```text
score = 1 - abs(len_a - len_b) / max(len_a, len_b)
```

用途：

```text
检验是否存在长度偏置。
```

---

## 5. 字符串基线

### 5.1 Raw Text Similarity

输入：

```text
原始代码文本
```

处理：

```text
不删除注释
不删除空白
不做标识符归一化
```

相似度：

```text
SequenceMatcher ratio
Levenshtein normalized similarity
```

用途：

```text
作为最低层表层相似度基线。
```

### 5.2 Normalized Text Similarity

处理：

```text
删除注释
统一换行
统一空白
去除多余空行
```

用途：

```text
验证简单预处理能改善多少。
```

### 5.3 注意事项

字符串方法在变量名替换、语句重排、函数拆分、跨语言改写中通常较弱。论文中要如实说明。

---

## 6. Token 基线

### 6.1 Token Jaccard Similarity

定义：

```text
J(A,B) = |tokens(A) ∩ tokens(B)| / |tokens(A) ∪ tokens(B)|
```

特点：

```text
忽略顺序
实现简单
对重复结构不敏感
```

### 6.2 Token Cosine Similarity

定义：

```text
将 token 计数转为向量后计算余弦相似度。
```

特点：

```text
可反映 token 频次
但不理解结构
```

### 6.3 Token Edit Distance

定义：

```text
对 token 序列计算编辑距离，并归一化为相似度。
```

特点：

```text
保留顺序信息
对局部重排敏感
```

### 6.4 Token Winnowing Fingerprint

可选增强：

```text
对 token k-gram 生成 hash，并使用 winnowing 选择指纹。
```

用途：

```text
模拟经典代码指纹方法。
```

---

## 7. AST 基线

### 7.1 Raw AST Node Sequence Similarity

方法：

```text
将 AST 前序遍历为节点类型序列，再计算序列相似度。
```

优点：

```text
比 token 更关注结构。
```

缺点：

```text
不同语言 AST 节点不可直接比较。
对语句重排和函数拆分仍敏感。
```

### 7.2 AST Fingerprint Similarity

方法：

```text
对 AST 子树生成结构指纹，比较子树指纹集合。
```

相似度：

```text
Jaccard / Weighted Jaccard
```

### 7.3 Tree Edit Distance

可选增强：

```text
计算两棵 AST 的树编辑距离。
```

注意：

```text
树编辑距离可能计算成本高，只适合小规模样本或抽样实验。
```

---

## 8. 控制流和数据流基线

### 8.1 CFG Signature

提取：

```text
if_count
loop_count
switch_count
return_count
branch_depth
loop_nesting_depth
```

相似度：

```text
数值向量余弦相似度
结构序列相似度
```

### 8.2 Data Dependency Signature

提取：

```text
变量定义-使用关系
赋值依赖
累加依赖
数组读写依赖
函数调用依赖
```

注意：

```text
V1 可以做轻量级依赖特征，不要求完整静态分析。
```

---

## 9. 外部基线：JPlag

### 9.1 作用

JPlag 用于代表成熟的源代码相似度检测工具。

### 9.2 推荐使用场景

```text
Java-Java
Python-Python
C-C
```

如果版本支持，也可测试部分其他语言。

### 9.3 输入准备

每个题目建立一个 JPlag 输入目录：

```text
baselines/jplag/input/P001/
  student_001/Main.java
  student_002/Main.java
  student_003/Main.java
```

### 9.4 推荐命令模板

具体命令以当前安装版本为准。建议封装为脚本：

```bash
python experiment/baselines/run_jplag.py --problem P001 --language java --input datasets/coderisk-pa-v1/problems/P001/submissions/java --output outputs/baselines/jplag/P001
```

脚本内部再调用 JPlag CLI。

### 9.5 输出解析

需要提取：

```text
submission_a
submission_b
similarity_score
matched_tokens_or_fragments
report_path
```

统一写入：

```text
outputs/baselines/jplag/P001/predictions.csv
```

字段：

```csv
method,problem_id,submission_a,submission_b,score,rank,raw_report_path
jplag,P001,A.java,B.java,0.873,1,outputs/baselines/jplag/P001/report/index.html
```

### 9.6 公平性要求

1. JPlag 使用原始代码输入。
2. 不把 PICAS 规范化后的代码输入 JPlag，除非作为额外实验并明确说明。
3. 阈值在验证集调优。
4. 语言不支持或运行失败的样本要记录，不可静默删除。

---

## 10. 外部基线：Dolos

### 10.1 作用

Dolos 用于代表支持多语言、带可视化报告的现代代码相似度检测工具。

### 10.2 推荐使用场景

```text
Java-Java
Python-Python
C-C
部分跨语言或多语言混合输入（视工具支持能力而定）
```

### 10.3 输入准备

```text
baselines/dolos/input/P001/files/
  A.java
  B.java
  C.java
```

### 10.4 推荐命令模板

```bash
python experiment/baselines/run_dolos.py --problem P001 --language java --input datasets/coderisk-pa-v1/problems/P001/submissions/java --output outputs/baselines/dolos/P001
```

### 10.5 输出解析

统一转换为：

```csv
method,problem_id,submission_a,submission_b,score,rank,raw_report_path
```

### 10.6 注意事项

Dolos 的报告格式可能随版本变化。必须通过适配器读取，不要让主实验脚本直接依赖某个 HTML 结构。

---

## 11. 外部基线：MOSS

### 11.1 作用

MOSS 用于经典工具对照。

### 11.2 是否必做

```text
本科毕设：可选
期刊增强：可选但有加分
```

### 11.3 使用限制

需要考虑：

```text
账号申请
调用限制
数据隐私
网络稳定性
是否允许上传代码
```

### 11.4 如果不能使用 MOSS

论文中可以在相关工作部分介绍 MOSS，但实验基线使用 JPlag 和 Dolos。

---

## 12. PICAS 消融基线

### 12.1 PICAS-Full

完整方法：

```text
Canonicalization + Multi-dimensional Similarity + Problem-aware Scoring + Dynamic Threshold + Evidence Generation
```

### 12.2 PICAS-NoDT

去掉动态阈值：

```text
使用固定阈值或全局验证集最佳阈值。
```

目的：

```text
验证题目感知动态阈值的贡献。
```

### 12.3 PICAS-NoCanon

去掉置换不变规范化：

```text
使用原始 token/AST 特征。
```

目的：

```text
验证规范化对 L1-L4 伪装的贡献。
```

### 12.4 PICAS-NoRare

去掉稀有片段相似度：

```text
不使用特殊边界处理、魔法数、异常分支、罕见 API 等证据。
```

目的：

```text
验证 RareFragmentSimilarity 对复杂题和模板题的贡献。
```

### 12.5 PICAS-NoIR

去掉语言无关 IR：

```text
只使用语言内 token/AST/CFG 特征。
```

目的：

```text
验证跨语言检测能力来源。
```

### 12.6 PICAS-NoProblemFeature

去掉题目特征：

```text
不使用 DifficultyScore、TemplateRiskScore、NaturalSimilarityRisk。
```

目的：

```text
验证题目上下文建模贡献。
```

---

## 13. Benchmark 数据设计

### 13.1 主数据集

主数据集必须是项目自建的编程作业场景数据集：

```text
CodeRisk-PA-v1
```

原因：

```text
本项目研究的是题目感知相似风险检测，必须有题目特征、自然相似样本和变换等级标签。
```

### 13.2 可选公开数据集

可选用于补充实验：

```text
POJ-104
BigCloneBench
IR-Plag
ConPlag
其他公开代码克隆或代码查重数据集
```

注意：

```text
公开 clone 数据集不一定包含题目自然相似风险标签，不能完全替代 CodeRisk-PA-v1。
```

### 13.3 公开数据集使用原则

1. 只使用许可证允许的数据。
2. 明确数据集来源。
3. 不修改标签后冒充自建标签。
4. 如果标签质量存在争议，必须在论文中说明。
5. 公开数据集作为补充，不覆盖主实验主线。

---

## 14. Benchmark 任务定义

### 14.1 Pair Classification

输入：

```text
代码对 A/B + 题目 Q
```

输出：

```text
是否为高风险相似对
```

指标：

```text
Precision / Recall / F1 / FPR / FNR / AUC
```

### 14.2 Suspicious Pair Ranking

输入：

```text
同一道题的所有提交
```

输出：

```text
按风险分数排序的代码对
```

指标：

```text
Precision@K
Recall@K
Average Precision
MRR
```

### 14.3 Transformation Robustness

输入：

```text
原始代码与 L1-L9 改写代码对
```

输出：

```text
不同变换等级下的召回率和相似度保持率
```

指标：

```text
Recall by Level
Similarity Retention Rate
FNR by Level
```

### 14.4 Natural Similarity Suppression

输入：

```text
自然相似负样本
```

输出：

```text
是否被误判为高风险
```

指标：

```text
FPR on natural_similar
Risk Downgrade Ratio
```

---

## 15. 阈值调优协议

### 15.1 固定阈值组

测试以下固定阈值：

```text
0.70
0.75
0.80
0.85
0.90
```

### 15.2 全局最优阈值

在验证集上选择使 F1 最大的全局阈值：

```text
T_global = argmax F1(validation)
```

### 15.3 动态阈值

PICAS 使用：

```text
T_dynamic(Q) = BaseThreshold + f(ProblemFeatures)
```

其中参数只在训练/验证集确定。

### 15.4 禁止事项

```text
禁止在测试集上挑选最佳阈值后作为最终结果。
禁止每个基线使用不同的测试集。
禁止只报告最有利阈值而不说明调参方式。
```

---

## 16. 公平比较规则

### 16.1 输入一致

所有方法使用相同代码对、相同题目 split。

### 16.2 标签一致

所有方法使用同一 `labels.csv`。

### 16.3 调参一致

所有方法都只能使用训练集/验证集调参。

### 16.4 失败样本记录

外部工具失败时，必须记录：

```text
method
problem_id
submission_id
failure_stage
error_message
```

### 16.5 运行环境记录

记录：

```text
OS
CPU
RAM
Python version
Java version
Tool version
Git commit
```

---

## 17. Baseline Wrapper 设计

### 17.1 目录结构

```text
experiment/baselines/
  run_text_baseline.py
  run_token_baseline.py
  run_ast_baseline.py
  run_jplag.py
  run_dolos.py
  run_moss.py
  parse_jplag_report.py
  parse_dolos_report.py
  baseline_common.py
```

### 17.2 统一输出格式

所有 baseline 输出统一为：

```csv
method,problem_id,pair_id,submission_a,submission_b,language_a,language_b,score,pred_label,threshold,rank,status,error_message
```

### 17.3 状态字段

```text
SUCCESS
PARSE_FAILED
LANGUAGE_NOT_SUPPORTED
TIMEOUT
TOOL_ERROR
SKIPPED
```

---

## 18. 结果汇总格式

### 18.1 总体结果表

```csv
method,precision,recall,f1,fpr,fnr,auc_roc,auc_pr,average_time_ms
```

### 18.2 分组结果表

```csv
method,group_type,group_name,precision,recall,f1,fpr,fnr,count
```

其中 `group_type`：

```text
problem_difficulty
transform_level
language_pair
template_risk
natural_similarity_risk
```

### 18.3 消融结果表

```csv
variant,removed_module,precision,recall,f1,fpr,fnr,delta_f1,delta_fpr
```

---

## 19. 对比实验矩阵

### 19.1 最低矩阵

```text
Raw Text
Token Jaccard
Token Edit Distance
Raw AST
PICAS-NoDT
PICAS-NoCanon
PICAS-Full
```

### 19.2 期刊增强矩阵

```text
Raw Text
Normalized Text
Token Jaccard
Token Edit Distance
AST Fingerprint
CFG Signature
JPlag
Dolos
PICAS-NoDT
PICAS-NoCanon
PICAS-NoRare
PICAS-NoIR
PICAS-Full
```

### 19.3 高质量矩阵

可加入：

```text
CodeBLEU
CrystalBLEU
Tree Edit Distance
CodeBERTScore
MOSS
```

注意：

```text
代码生成评价指标不是专门的代码查重工具，若使用必须明确其定位为补充相似度基线。
```

---

## 20. 论文中如何呈现基线

### 20.1 相关工作部分

说明：

```text
MOSS、JPlag、Dolos 是源代码相似度检测中的典型工具。
```

### 20.2 实验设置部分

说明：

```text
本文选择字符串、Token、AST、JPlag、Dolos 和若干 PICAS 消融版本作为对比方法。
```

### 20.3 结果分析部分

重点分析：

```text
PICAS 是否降低简单题误报。
PICAS 是否提高伪装代码召回。
PICAS 是否在跨语言样本上更稳定。
PICAS 的动态阈值是否带来实际收益。
```

---

## 21. 不应做的对比

禁止以下不公平对比：

1. 只和字符串相似度比，不和 JPlag/Dolos 比。
2. 给 PICAS 使用题目标签调参，却不给基线使用验证集调参。
3. 删除外部工具失败样本但不报告。
4. 把跨语言样本强行输入不支持跨语言的工具后直接判其失败。
5. 使用不同数据集分别报告不同方法。
6. 只挑 PICAS 表现好的题目展示。
7. 用测试集最优阈值作为固定阈值结果。

---

## 22. 基线验收标准

### 22.1 本科毕设验收

至少完成：

```text
Raw Text
Token Jaccard
Token Edit Distance
Raw AST
PICAS-NoDT
PICAS-NoCanon
PICAS-Full
```

### 22.2 期刊增强验收

至少完成：

```text
JPlag
Dolos
PICAS-NoRare
PICAS-NoIR
分组指标
消融实验
显著性或置信区间
```

### 22.3 高质量验收

完成：

```text
外部工具报告可追溯
baseline wrapper 可一键运行
结果 CSV 可直接生成论文表格
失败样本有记录
```

---

## 23. 参考来源记录

### 23.1 工具来源

开发文档和论文中应记录以下工具来源：

```text
MOSS official page
JPlag GitHub repository / documentation
Dolos official documentation / repository
```

### 23.2 文献来源

后续 `PAPER_OUTLINE.md` 和论文正文中再补：

```text
代码克隆检测
源代码抄袭检测
AST/CFG/PDG 相似度
代码指纹
AI 改写与代码查重
```

### 23.3 版本记录

实际运行时记录：

```text
JPlag version
Dolos version
MOSS access date
Parser version
tree-sitter version
```

---

## 24. 一句话总结

```text
本文件的核心任务，是确保 PICAS 的实验结果不是孤立展示，而是在固定阈值、传统相似度、成熟工具和自身消融版本之间形成公平、可复现、可解释的对比。
```


## 表述边界补充

禁止宣称 PICAS 能准确判断抄袭、完整识别 AI 改写、证明两个程序语义等价或完整解决跨语言查重。推荐结论表述为：在自建编程作业数据集上，PICAS 相比固定阈值方法能够降低简单题自然相似导致的误报，并在标识符替换和格式调整等表层改写场景下保持更稳定的相似风险评估。
