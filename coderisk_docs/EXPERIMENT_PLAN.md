# EXPERIMENT_PLAN.md

> 2026-10-08 更新：本科主实验以 [公平评测协议](proposal/FAIR_EVALUATION.md) 与 [数据标注规范](proposal/DATA_PROTOCOL.md) 为当前可执行约定，入口为 `experiment/run_fair_evaluation.py`。以下历史研究命题均视为待验证问题；历史E3/E4不能替代新版受控比较。真实数据实验尚待收集与冻结。

> 本文件定义 CodeRisk / PICAS 项目的实验设计。它用于指导实验数据构建、脚本开发、结果记录、论文第六章、答辩图表和期刊投稿。任何实验结论都必须能被本文件中的实验流程、指标和数据记录支撑。

---

## 1. 实验总目标

### 1.1 项目方法名称

```text
PICAS: Problem-aware Invariant Code Similarity Analysis
```

中文名称：

```text
题目感知与置换不变代码相似风险分析方法
```

### 1.2 实验核心问题

本项目实验不是简单证明系统能运行，而是证明以下研究命题：

```text
RQ1：题目复杂度自适应阈值是否能降低简单题自然相似导致的误报？
RQ2：置换不变规范化是否能提高对改名、格式化、局部重排等伪装方式的鲁棒性？
RQ3：多维结构相似度融合是否优于单一 token/AST 相似度？
RQ4：语言无关 IR 是否能在有限范围内支持 Java/Python/C 跨语言相似风险识别？
RQ5：稀有片段、边界处理和错误模式相似证据是否能提升人工复核解释性？
RQ6：PICAS 相比固定阈值和主流工具，在编程作业场景中是否具有更低误报率或更高综合 F1？
```

### 1.3 最终要支撑的论文结论

实验最终需要支撑以下结论：

1. 简单题、模板题中，固定阈值容易误报；PICAS 通过自然相似风险建模和动态阈值校准能降低误报率。
2. 在变量名替换、函数名替换、注释删除、格式调整等表层伪装下，置换不变规范化后的结构表示能保持更稳定的相似度。
3. 多维结构相似度融合比单一 token、字符串或 AST 相似度更稳健。
4. 对于 Java 与 Python 的常见算法题，语言无关 IR 可以提供有限但可解释的跨语言检测能力。
5. 系统输出风险等级与证据链，比单独输出相似度百分比更适合编程作业人工复核。

---

## 2. 实验原则

### 2.1 不直接判定抄袭

所有实验标签使用：

```text
similar / suspicious / transformed / independent / natural-similar
```

不要在数据文件中直接使用：

```text
plagiarized / cheating / guilty
```

论文表述中使用：

```text
相似风险
可疑相似
人工复核候选
结构相似样本
```

不要使用：

```text
确认抄袭
证明作弊
直接判罪
```

### 2.2 区分“代码相似”和“题目自然相似”

实验必须区分两种现象：

```text
A. 两份代码因为复制、改写或共享来源而相似。
B. 两份代码因为题目简单、解法空间小、模板固定而自然相似。
```

PICAS 的价值就在于能更好地区分这两类现象。

### 2.3 训练、验证、测试必须分离

如果动态阈值参数需要调优，必须使用验证集，不能在测试集上调参。

推荐划分：

```text
Train / Calibration Set: 50%
Validation Set: 20%
Test Set: 30%
```

如果样本量较小，使用按题目分组的 K 折交叉验证：

```text
Problem-level K-fold Cross Validation
```

要求：

```text
同一道题的所有代码对不能同时出现在训练和测试中。
```

这可以避免题目特征泄漏。

### 2.4 所有实验必须可复现

每次实验必须记录：

```text
experiment_id
experiment_name
git_commit
config_file
random_seed
dataset_version
baseline_version
model_version
start_time
end_time
machine_info
metric_result_path
log_path
```

### 2.5 所有结果必须保留失败案例

不要只展示成功案例。每个主要实验都应输出：

```text
false_positive_cases.csv
false_negative_cases.csv
borderline_cases.csv
representative_success_cases.csv
```

论文中至少分析 3 到 5 个失败案例。

---

## 3. 数据集总体设计

### 3.1 数据集组成

项目实验数据集建议由四部分组成：

```text
D1：自建编程作业数据集
D2：人工伪装改写数据集
D3：跨语言等价实现数据集
D4：AI 辅助改写数据集
```

可选增强：

```text
D5：公开代码克隆或代码相似度数据集
D6：真实课程历史提交数据集（必须脱敏且取得授权）
```

### 3.2 数据集命名

推荐命名：

```text
CodeRisk-PA-v1
```

含义：

```text
PA = Problem-aware Assignment
```

如果后续加入跨语言数据：

```text
CodeRisk-PA-XL-v1
```

含义：

```text
XL = Cross-Language
```

### 3.3 数据集目录结构

```text
datasets/
  coderisk-pa-v1/
    README.md
    DATA_CARD.md
    problems/
      P001/
        problem.json
        reference/
          java_ref_01.java
          python_ref_01.py
          c_ref_01.c
        submissions/
          java/
          python/
          c/
        pairs.csv
        transformations.csv
        labels.csv
      P002/
      P003/
    splits/
      train_problems.txt
      validation_problems.txt
      test_problems.txt
    metadata/
      problem_features.csv
      dataset_statistics.json
    generated/
      pair_features.parquet
      experiment_cache/
```

---

## 4. 题目类型设计

### 4.1 题目难度分组

题目按难度分为 4 类：

```text
G1：简单输入输出题
G2：基础结构题
G3：标准算法模板题
G4：复杂算法或综合逻辑题
```

### 4.2 G1 简单输入输出题

典型题型：

```text
A+B
求平均值
判断奇偶
简单字符串格式化
简单区间统计
```

特点：

```text
代码短
解法空间小
自然相似风险高
固定阈值容易误报
```

实验目的：

```text
证明动态阈值可以降低简单题误报。
```

### 4.3 G2 基础结构题

典型题型：

```text
数组求和
最大最小值
字符串统计
简单排序
二维数组遍历
```

特点：

```text
存在常见结构
但仍有一定实现差异
```

实验目的：

```text
验证 token/AST/规范化结构在基础题上的表现差异。
```

### 4.4 G3 标准算法模板题

典型题型：

```text
二分查找
DFS/BFS
最短路
并查集
动态规划入门
排序变体
```

特点：

```text
模板化风险高
算法结构天然相似
边界处理和细节差异更重要
```

实验目的：

```text
验证 TemplateRiskScore 和 RareFragmentSimilarity 的作用。
```

### 4.5 G4 复杂算法或综合逻辑题

典型题型：

```text
图算法综合题
多阶段动态规划
课程设计模块
文件处理任务
小型业务逻辑题
综合模拟题
```

特点：

```text
代码较长
解法空间较大
独立实现差异明显
结构高度相似更可疑
```

实验目的：

```text
证明复杂题中动态阈值可以更敏感地发现高风险结构相似。
```

---

## 5. 题目样本规模建议

### 5.1 最低可用规模

用于本科毕设最低规模：

```text
题目数：20
每题提交数：20
总提交数：400
代码对数量：每题 C(20,2)=190，总计约 3800 对
```

### 5.2 期刊增强规模

用于普通期刊或较有分量的应用型论文：

```text
题目数：40-60
每题提交数：30-50
总提交数：1200-3000
代码对数量：约 18,000-75,000 对
```

### 5.3 高强度增强规模

如果希望进一步冲更强期刊：

```text
题目数：100+
每题提交数：50+
总提交数：5000+
代码对数量：每题分层采样，不做全量两两比较
```

### 5.4 分层采样原则

代码对数量过大时，不建议全量计算。推荐分层采样：

```text
正样本：全部保留或高比例保留
自然相似负样本：重点保留
普通独立负样本：随机采样
边界分数样本：重点保留
```

---

## 6. 代码变换等级设计

### 6.1 变换等级总览

```text
L0：原始代码
L1：变量名替换
L2：函数名/参数名替换
L3：注释删除与格式扰动
L4：局部无依赖语句重排
L5：函数拆分与合并
L6：等价表达式替换
L7：跨语言重写
L8：AI 辅助改写
L9：混合强伪装改写（可选）
```

### 6.2 L0 原始代码

定义：

```text
未经过任何人工或自动变换的原始提交。
```

用途：

```text
作为基础样本和独立实现样本。
```

### 6.3 L1 变量名替换

变换示例：

```text
sum -> result
arr -> nums
i -> index
count -> cnt
```

评估重点：

```text
IdentifierMappingSimilarity
CanonicalTokenSimilarity
CanonicalASTSimilarity
```

预期：

```text
未规范化方法相似度下降；PICAS 下降较小。
```

### 6.4 L2 函数名和参数名替换

变换示例：

```text
solve -> process
check -> validate
n -> length
```

评估重点：

```text
FunctionNameCanonicalization
ParameterCanonicalization
Scope-aware Mapping
```

### 6.5 L3 注释删除与格式扰动

变换内容：

```text
删除注释
修改缩进
调整空行
修改花括号位置
```

评估重点：

```text
Preprocessing Robustness
Token Normalization
```

### 6.6 L4 局部无依赖语句重排

变换示例：

```text
a = input();
b = input();
```

可交换为：

```text
b = input();
a = input();
```

前提：

```text
不存在数据依赖、控制依赖和副作用冲突。
```

评估重点：

```text
Local Dependency Analysis
Order-insensitive Block Signature
```

### 6.7 L5 函数拆分与合并

变换内容：

```text
把一段逻辑拆成 helper 函数
把 helper 函数内联回主函数
```

评估重点：

```text
CallGraphSimilarity
Function-level Matching
OperationSequenceSimilarity
```

### 6.8 L6 等价表达式替换

变换示例：

```text
a + b -> b + a
x * 2 -> x + x
x <= y -> !(x > y)
```

注意：

```text
只处理安全、局部、可证明的等价变换。
不要为了实验强行引入语义不等价代码。
```

### 6.9 L7 跨语言重写

变换示例：

```text
Java -> Python
Python -> Java
Java -> C
```

最低要求：

```text
优先做 Java <-> Python。
C 作为增强。
```

评估重点：

```text
LanguageIndependentIRSimilarity
ControlFlowSignature
OperationSequenceSignature
```

### 6.10 L8 AI 辅助改写

变换方式：

```text
要求大模型在保持功能不变的前提下改写代码。
```

记录要求：

```text
model_name
prompt_template
temperature
generation_time
manual_check_status
```

评估重点：

```text
AI rewrite robustness
False negative rate under semantic-preserving rewrite
Evidence interpretability
```

### 6.11 L9 混合强伪装改写

可选增强：

```text
变量名替换 + 函数拆分 + 等价表达式 + 语句重排 + AI 改写
```

该等级难度较高，不作为 V1/V2 必做。

---

## 7. 标签体系设计

### 7.1 pair-level 标签

每个代码对使用以下标签：

```text
1 = transformed_similar
0 = independent
2 = natural_similar
3 = uncertain
```

说明：

```text
transformed_similar：由同一源代码经过变换得到，或人工确认高度相关。
independent：不同来源独立实现。
natural_similar：独立实现但因题目简单或模板固定而自然相似。
uncertain：无法可靠判断，不进入主实验，只进入案例分析。
```

### 7.2 风险评估标签

用于系统输出：

```text
LOW
MEDIUM
ELEVATED
HIGH
```

### 7.3 标签文件格式

`labels.csv`：

```csv
pair_id,problem_id,submission_a,submission_b,label,label_source,confidence,annotator,notes
P001_A_B,P001,A.java,B.java,transformed_similar,synthetic,1.0,system,L1 variable rename
```

### 7.4 标注来源

```text
synthetic：人工或脚本生成变换，标签可信度最高
manual：人工标注
historical：历史记录或教师记录
heuristic：规则推断，只能用于辅助分析
```

### 7.5 标签置信度

```text
1.0：确定
0.8：较确定
0.6：有争议
0.0-0.5：不进入主测试集
```

---

## 8. 数据防泄漏规则

### 8.1 题目级隔离

训练、验证、测试必须按题目隔离：

```text
同一道题不能同时出现在训练集和测试集。
```

### 8.2 源代码级隔离

由同一原始代码生成的 L1-L9 变换样本必须处于同一个 split。

### 8.3 模型辅助评分隔离

如果使用 LLM 辅助题目复杂度评分，不能把测试标签输入模型。

### 8.4 阈值调优隔离

动态阈值参数只能在训练集/验证集上确定，不能在测试集上反复调。

---

## 9. 指标体系

### 9.1 分类指标

主指标：

```text
Precision
Recall
F1-score
False Positive Rate
False Negative Rate
Accuracy
Balanced Accuracy
```

### 9.2 排序指标

对于按风险分数排序的代码对，使用：

```text
AUC-ROC
AUC-PR
Average Precision
Precision@K
Recall@K
MRR
```

### 9.3 分层指标

必须按以下维度分层报告：

```text
题目难度分组 G1-G4
变换等级 L0-L9
语言组合 Java-Java / Python-Python / Java-Python / Java-C / Python-C
题目自然相似风险低/中/高
模板风险低/中/高
代码长度短/中/长
```

### 9.4 阈值相关指标

```text
Optimal Threshold on Validation
DynamicThreshold Mean
DynamicThreshold Std
Threshold Shift by Problem Group
FPR Reduction on Simple Problems
Recall Change on Complex Problems
```

### 9.5 证据质量指标

人工评价：

```text
Evidence Relevance
Evidence Completeness
Evidence Usefulness
Evidence Redundancy
Review Time Reduction
```

评分区间：

```text
1-5 分
```

### 9.6 性能指标

```text
Average Analysis Time per Pair
Average Task Time per Problem
Parser Failure Rate
Memory Usage
Queue Waiting Time
Report Generation Time
```

---

## 10. 实验一：固定阈值 vs 动态阈值

### 10.1 实验目标

验证题目复杂度自适应阈值是否优于固定阈值。

### 10.2 对比方法

```text
B1：固定阈值 70%
B2：固定阈值 75%
B3：固定阈值 80%
B4：固定阈值 85%
PICAS-DT：动态阈值
```

### 10.3 实验数据

覆盖：

```text
G1 简单题
G2 基础题
G3 模板题
G4 复杂题
```

### 10.4 评估重点

```text
G1/G3 上的 False Positive Rate
G4 上的 Recall
整体 F1-score
```

### 10.5 预期结果

```text
动态阈值在简单题和模板题上应降低误报。
动态阈值在复杂题上不应显著降低召回。
```

### 10.6 必须输出图表

```text
不同题目组下 FPR 对比柱状图
不同题目组下 Recall 对比柱状图
动态阈值分布箱线图
固定阈值与动态阈值混淆矩阵
```

---

## 11. 实验二：置换不变规范化有效性

### 11.1 实验目标

验证标识符归一化、函数名归一化、参数名归一化、可交换表达式规范化是否提升鲁棒性。

### 11.2 对比方法

```text
Raw Token Similarity
Raw AST Similarity
Canonical Token Similarity
Canonical AST Similarity
PICAS without Canonicalization
PICAS full
```

### 11.3 数据范围

重点覆盖：

```text
L1 变量名替换
L2 函数名/参数名替换
L3 格式扰动
L4 局部语句重排
L6 等价表达式替换
```

### 11.4 评估指标

```text
Similarity Retention Rate
Recall@HighRisk
F1-score
False Negative Rate
```

### 11.5 Similarity Retention Rate

定义：

```text
SRR = similarity(transformed_pair) / similarity(original_pair)
```

解释：

```text
SRR 越高，说明方法对该变换越鲁棒。
```

### 11.6 必须输出图表

```text
不同变换等级下 SRR 曲线
规范化前后 Recall 对比图
规范化前后 FNR 对比图
变量名映射案例表
```

---

## 12. 实验三：多维相似度融合有效性

### 12.1 实验目标

验证综合风险评分是否优于单一相似度指标。

### 12.2 对比方法

```text
Token-only
AST-only
CFG-only
OperationSequence-only
RareFragment-only
Token + AST
Token + AST + CFG
PICAS full
```

### 12.3 评估重点

```text
整体 F1
AUC-PR
高风险 TopK 准确率
跨变换等级稳定性
```

### 12.4 消融实验

```text
PICAS - TokenSimilarity
PICAS - ASTSimilarity
PICAS - CFGSimilarity
PICAS - DataDependencySimilarity
PICAS - RareFragmentSimilarity
PICAS - ProblemAwareThreshold
PICAS - Canonicalization
```

### 12.5 必须输出图表

```text
消融实验表
多维指标贡献条形图
不同方法 PR 曲线
TopK 高风险命中率折线图
```

---

## 13. 实验四：跨语言检测能力

### 13.1 实验目标

验证语言无关 IR 对跨语言相似风险识别是否有效。

### 13.2 语言组合

最低要求：

```text
Java-Python
```

增强要求：

```text
Java-C
Python-C
```

### 13.3 对比方法

```text
Raw Token Similarity
Language-specific AST Similarity
OperationSequenceSimilarity
LanguageIndependentIRSimilarity
PICAS full
```

### 13.4 评估指标

```text
Recall
F1-score
AUC-PR
Parser Failure Rate
IR Mapping Coverage
```

### 13.5 IR Mapping Coverage

定义：

```text
成功映射到语言无关 IR 的节点数 / 原 AST 有效节点数
```

### 13.6 预期结果

```text
跨语言 token 相似度通常较低。
语言无关 IR 应在循环、条件、赋值、函数调用、返回语句等常见结构上提供更稳定相似度。
```

### 13.7 边界说明

论文中必须说明：

```text
本项目不声称完全解决跨语言语义等价检测。
本项目只在编程作业常见结构上探索有限的跨语言结构相似风险识别。
```

---

## 14. 实验五：简单题自然相似误报分析

### 14.1 实验目标

证明简单题和模板题中存在大量自然相似样本，固定阈值方法容易误报。

### 14.2 数据范围

```text
G1 简单输入输出题
G3 标准模板题
natural_similar 标签样本
```

### 14.3 对比方法

```text
固定阈值
PICAS dynamic threshold
PICAS dynamic threshold + template penalty
```

### 14.4 评估指标

```text
False Positive Rate on natural_similar pairs
Risk Level Downgrade Ratio
Manual Review Reduction
```

### 14.5 案例分析

必须展示至少 3 个自然相似案例：

```text
两个独立 A+B 实现
两个独立排序模板
两个独立 BFS 模板
```

每个案例展示：

```text
代码片段
固定阈值风险
PICAS 风险
动态阈值解释
```

---

## 15. 实验六：AI 改写鲁棒性

### 15.1 实验目标

测试大模型改写代码后，系统是否仍能识别结构相似风险。

### 15.2 数据生成

每个原始代码生成：

```text
AI rewrite v1：轻度改写
AI rewrite v2：中度改写
AI rewrite v3：强改写
```

提示词必须保存。

### 15.3 人工校验

AI 改写后的代码必须通过：

```text
编译/运行测试
样例测试
人工快速审查
```

不通过的样本不能进入主实验。

### 15.4 对比方法

```text
JPlag
Dolos
TokenSimilarity
ASTSimilarity
PICAS full
```

### 15.5 评估指标

```text
Recall under AI rewrite
False Negative Rate
Evidence Quality
```

### 15.6 注意事项

不要把 AI 改写实验写成“检测 AI 生成代码”。本项目检测的是：

```text
AI 辅助改写后是否仍保留异常相似结构。
```

---

## 16. 实验七：证据输出有效性

### 16.1 实验目标

验证结构化证据是否有助于人工复核。

### 16.2 对比方式

人工评审两种报告：

```text
A：只有相似度分数和代码对
B：相似度分数 + 动态阈值 + 多维指标 + 证据链 + 高亮片段
```

### 16.3 评审人员

推荐：

```text
2-5 名具备编程基础的同学或教师
```

### 16.4 评估指标

```text
判断一致性
平均复核时间
证据有用性评分
证据冗余评分
主观可信度评分
```

### 16.5 输出结果

```text
review_time_comparison.csv
evidence_rating.csv
inter_annotator_agreement.txt
```

### 16.6 论文写法

如果评审人数较少，不要过度声称用户研究。可以写成：

```text
辅助性人工复核评估
```

不要写成：

```text
大规模用户研究
```

---

## 17. 实验八：系统性能测试

### 17.1 实验目标

验证系统在合理规模任务下可运行。

### 17.2 测试场景

```text
单题 20 份代码
单题 50 份代码
单题 100 份代码
多题批量任务
跨语言任务
报告导出任务
```

### 17.3 指标

```text
总任务耗时
平均代码对分析耗时
解析耗时
规范化耗时
相似度计算耗时
证据生成耗时
报告生成耗时
峰值内存
失败率
```

### 17.4 性能边界

论文中不要虚构高并发能力。应明确：

```text
系统主要面向课程级批处理查重任务，而不是互联网高并发服务。
```

---

## 18. 统计显著性分析

### 18.1 推荐方法

对于分类结果：

```text
McNemar Test
```

对于多次折叠实验指标：

```text
Wilcoxon Signed-Rank Test
Paired t-test（仅在分布近似正态时使用）
```

对于置信区间：

```text
Bootstrap 95% Confidence Interval
```

### 18.2 报告要求

至少报告：

```text
mean
std
95% CI
p-value（如适用）
effect size（可选）
```

### 18.3 注意事项

如果样本量不足，不要过度强调 p-value。可以主要报告：

```text
效果提升幅度
置信区间
失败案例
```

---

## 19. 实验配置文件设计

### 19.1 配置文件目录

```text
configs/experiments/
  exp01_fixed_vs_dynamic.yaml
  exp02_canonicalization.yaml
  exp03_fusion_ablation.yaml
  exp04_cross_language.yaml
  exp05_natural_similarity.yaml
  exp06_ai_rewrite.yaml
  exp07_evidence_review.yaml
  exp08_performance.yaml
```

### 19.2 配置文件字段

```yaml
experiment_id: EXP-001
experiment_name: fixed_vs_dynamic_threshold
dataset: coderisk-pa-v1
split: test
random_seed: 20260617
methods:
  - fixed_threshold_70
  - fixed_threshold_75
  - fixed_threshold_80
  - fixed_threshold_85
  - picas_dynamic_threshold
metrics:
  - precision
  - recall
  - f1
  - false_positive_rate
  - false_negative_rate
output_dir: outputs/experiments/EXP-001
```

---

## 20. 实验输出目录规范

```text
outputs/experiments/
  EXP-001/
    config.yaml
    run.log
    metrics_summary.json
    metrics_by_problem_group.csv
    metrics_by_transform_level.csv
    predictions.csv
    confusion_matrix.csv
    figures/
      fpr_by_group.png
      recall_by_group.png
      threshold_distribution.png
    cases/
      false_positive_cases.csv
      false_negative_cases.csv
      representative_cases.md
```

---

## 21. 实验脚本命名规范

```text
experiment/
  run_experiment.py
  build_dataset.py
  generate_transformations.py
  run_baselines.py
  evaluate_metrics.py
  plot_results.py
  export_paper_tables.py
  export_case_studies.py
```

### 21.1 命令示例

```bash
python experiment/run_experiment.py --config configs/experiments/exp01_fixed_vs_dynamic.yaml
python experiment/evaluate_metrics.py --predictions outputs/experiments/EXP-001/predictions.csv
python experiment/plot_results.py --experiment EXP-001
```

---

## 22. 论文图表清单

### 22.1 必备表格

```text
表 1：数据集统计表
表 2：题目复杂度分组统计表
表 3：对比方法说明表
表 4：总体检测性能对比表
表 5：不同题目类型下的误报率对比表
表 6：不同伪装等级下的召回率对比表
表 7：消融实验结果表
表 8：跨语言检测结果表
表 9：系统性能测试表
```

### 22.2 必备图片

```text
图 1：PICAS 方法流程图
图 2：题目感知动态阈值计算流程图
图 3：置换不变规范化示例图
图 4：不同题目类型下 FPR 对比图
图 5：不同变换等级下 Recall 对比图
图 6：动态阈值分布箱线图
图 7：PR 曲线
图 8：消融实验贡献图
图 9：证据输出界面截图
```

---

## 23. 结果解释模板

### 23.1 固定阈值实验解释模板

```text
在简单输入输出题组中，固定阈值方法由于未考虑题目解法空间较小的问题，将大量自然相似样本判为高风险。PICAS 通过引入 NaturalSimilarityRisk 和 TemplateRiskScore 自动提高该类题目的风险阈值，使误报率下降。
```

### 23.2 规范化实验解释模板

```text
在变量名替换和函数名替换场景下，原始 token 相似度出现明显下降，而置换不变规范化后的结构相似度保持稳定，说明该表示对低层次标识符替换具有较强鲁棒性。
```

### 23.3 跨语言实验解释模板

```text
跨语言场景中，token 与语言特定 AST 的可比性较弱。语言无关 IR 将循环、条件、赋值和操作序列映射到统一结构后，能够在 Java-Python 常见算法题中保留部分结构相似信息。
```

---

## 24. 失败案例分析要求

每类失败案例至少保留一个：

```text
简单题仍然误报
复杂题漏报
AI 改写漏报
跨语言映射失败
解析器失败
证据片段定位不准
```

每个失败案例说明：

```text
样本编号
题目类型
语言组合
真实标签
系统预测
失败原因
后续改进方向
```

---

## 25. 实验验收标准

### 25.1 本科毕设最低验收

```text
至少 20 道题
至少 400 份代码或等价生成样本
至少 5 种对比方法
至少 4 个主要指标
至少 3 个消融实验
至少 5 个案例分析
```

### 25.2 期刊增强验收

```text
至少 40 道题
至少 1000 份代码或等价生成样本
覆盖 L1-L8 变换等级
包含 JPlag 或 Dolos 至少一个外部基线
包含动态阈值对比
包含置换不变规范化消融
包含跨语言实验
包含置信区间或显著性分析
```

### 25.3 高质量验收

```text
数据集可复现
实验脚本可一键运行
所有图表由脚本生成
论文表格可从输出文件导出
失败案例可追溯到原代码
```

---

## 26. 禁止事项

1. 禁止只展示系统截图而无实验数据。
2. 禁止只报告总体 Accuracy，不报告 FPR/FNR。
3. 禁止用测试集反复调动态阈值参数。
4. 禁止把自然相似样本当作普通负样本直接忽略。
5. 禁止把 AI 改写样本未经运行验证就加入正样本。
6. 禁止声称系统可以“自动认定抄袭”。
7. 禁止声称跨语言 IR 已完整解决语义等价检测。
8. 禁止只和弱基线对比，不和 JPlag/Dolos 或固定阈值方法对比。
9. 禁止删除失败案例。
10. 禁止虚构真实学生数据。

---

## 27. 与其他文档关系

```text
ALGORITHM_SPEC.md：定义 PICAS 方法和指标。
PROBLEM_AWARE_SCORING.md：定义题目复杂度与动态阈值。
CANONICALIZATION_SPEC.md：定义置换不变规范化。
BASELINES_AND_BENCHMARKS.md：定义对比方法和基准设置。
PAPER_OUTLINE.md：定义论文结构和实验结果放置位置。
TEST_PLAN.md：定义工程测试，不替代本实验计划。
```

---

## 28. 最终交付物

实验部分最终至少交付：

```text
datasets/ 或 dataset 构建脚本
configs/experiments/
outputs/experiments/
实验报告 Markdown
论文图表 PNG/SVG
论文表格 CSV/XLSX
失败案例分析文档
实验复现说明
```

---

## 29. V3 最小实验闭环（已实现）

### 29.1 实现范围

当前仓库已提供可复现的最小实验，不替代第 25 节规定的正式论文实验规模：

```text
配置：configs/experiments/minimal_v3.json
数据：experiment/datasets/v4-ready/cases.json
脚本：experiment/run_minimal_v3.py
输出：data/artifacts/experiments/<run-id>/
```

执行命令：

```powershell
python experiment\run_minimal_v3.py --config configs\experiments\minimal_v3.json --run-id PICAS-V4-READY-20260620-R2
```

每次运行输出 `run_manifest.json`、`metrics_summary.json`、`split_manifest.json`、`validation_calibration.json`、`predictions.csv`、按题型指标、E1-E4 对比 CSV、`failure_cases.csv`、`borderline_cases.csv` 和 `experiment_report.md`。清单记录 formulaVersion、algorithmVersion、datasetVersion、randomSeed、gitCommit 或本地源码标识。

### 29.2 当前结果边界

当前 36 个合成案例覆盖 simple_io、array_loop、sort_template、dfs_graph、dp_variant，包含 5 个 validation 与 5 个 test problem ID，problem/source overlap 均为 0。E1-E5 只汇总 test；validation 只选择固定阈值基线，生产动态公式未被修改。

最新真实运行中，改名案例 canonical token 均值为 1.0，raw token 均值约 0.066；动态阈值相对固定 0.70 将 natural-similar FPR 从 0.60 降到 0.40，但 recall 从 1.00 降到 0.60，且相对固定 0.75/0.80 未显示 FPR 优势。该反例必须保留，不能表述为正式 benchmark 或统计显著结论。

JPlag 6.2.0 已使用 Java 21 在 3 个合成 Java 提交上完成真实 smoke run，并生成原生/标准 CSV；该结果不并入 V3 E1-E5。正式实验仍需扩充经授权或公开数据、扩大外部基线规模，并加入置信区间和显著性分析。

---

## 30. 一句话总结

```text
本实验计划的核心目标，是证明 PICAS 不只是一个代码查重系统，而是一种能够结合题目上下文、结构规范化和证据输出的编程作业相似风险评估方法。
```

## 31. V4 Phase 1-2 最小实验

Phase 1 已运行 3-case normalized IR 实验和 JPlag 6.2.0 Java smoke baseline。Phase 2 使用独立固定数据集 `experiment/datasets/v4-phase2-crosslang/cases.json`，比较 raw token、AST、canonical、IR、lightweight control summary 和 lightweight data-flow summary。

Phase 2 的 0.70 review threshold 与 0.40/0.30/0.30 composite 只服务失败案例分类，未进入 FORMULA_SPEC_V1；运行中不得修改样例、标签或阈值。最新不可变运行 `PICAS-V4-PHASE2-XL-20260623-R2` 保留 1 个 false positive、2 个 false negative、1 个 expected parse fallback 和 unsupported syntax warning，不作为正式 benchmark。

## 32. Research V4 数据门禁与统一实验

统一 manifest：`experiment/datasets/research-v4/dataset.json`。每个归一化 case 必须具有 `pair_id`、`problem_id`、`problem_type`、`problem_group`、`dataset_split`、`split_preregistered`、`source_id`、`experiment_label`、`case_type`、`language`、`language_a`、`language_b`、`dataset_version`、`data_origin`、`source_type`、`synthetic`、`eligible_for_core_metrics`、题目元数据与 provenance；加载旧 shard 时可提供同值 `case_id`/`split` 兼容别名。

校验器同时拒绝 problem overlap、source overlap 和跨 split 精确代码哈希 overlap。AI_REWRITE 只有在记录 model、prompt、generation time、manual check 与 functional check 后才可进入核心指标。`UNCERTAIN` 永远不进入核心分类指标。

最新不可变运行 `PICAS-RESEARCH-V4-SEED-20260624-R2` 聚合 91 个 synthetic seed pair，其中 validation/test 为 41/50、eligible 85、problem 数为 15/18，problem/source/exact-hash overlap 均为 0。4 个 AI_REWRITE 使用 `source_type=placeholder` 且不进入核心指标。数量门槛的达到不代表正式 benchmark；当前仍缺至少 20 manual、8 verified ai_assisted、8 external 样例。

validation-only 校准从 `[-0.08,-0.04,0,0.04,0.08]` 选择实验 offset `-0.08`，并记录 `testSetUsedForSelection=false`、`productionFormulaChanged=false`。seed test 上校准后 F1 为 0.8085，生产 dynamic F1 为 0.6667；两者 NaturalSimilar FPR 均为 0.5714。这只验证 split 纪律和产物可追溯性，不支持修改生产公式。

同语言 seed 结果中 rename raw/canonical 均值为 0.250836/1.0。manifest-aligned JPlag 6.2.0 请求并匹配 72 pair，19 pair 因跨语言、placeholder、解析/不支持语法或非 eligible 被排除并记录。test-only seed 表中 JPlag fixed 0.70 F1 为 0.7826，PICAS dynamic F1 为 0.6667；该表用于检验 baseline 流程，不能作真实数据优劣结论。跨语言 eligible test 为 6 pair，experimental composite F1 为 0.6667 且 FPR 为 1.0，必须与 common-structure 误报一起报告。

## 33. Research V4 数据补充与运行手册

后续人工补数据和生成论文材料时，必须按以下手册执行：

```text
coderisk/experiment/datasets/research-v4/DATA_COLLECTION_GUIDE.md
coderisk/experiment/RUN_RESEARCH_V4.md
coderisk/experiment/RESULT_INTERPRETATION_GUIDE.md
coderisk/experiment/PAPER_MATERIALS_GUIDE.md
coderisk/experiment/RESEARCH_V4_CHECKLIST.md
```

手册要求：

```text
manual、ai_assisted、external、synthetic、placeholder 分目录存放。
AI_REWRITE 进入核心指标前必须有模型、prompt、生成时间、人工验证和功能验证。
external 必须记录来源、许可证或授权。
validation/test 必须 problem/source/hash-disjoint。
JPlag 对齐优先使用同语言、可解析、eligible 样例。
每次正式 run 后更新 TEST_REPORT、PAPER_OUTLINE、EXPERIMENT_PLAN 和 DATA_CARD。
```
