# TEST_PLAN.md

> 本文件定义 CodeRisk / PICAS 的测试计划。测试目标不是简单证明“系统能跑”，而是证明系统在工程链路、算法正确性、题目感知动态阈值、置换不变规范化、证据输出、实验复现和安全边界上都可验证。

---

## 1. 测试目标

### 1.1 总体目标

测试体系必须覆盖：

```text
后端业务接口
前端核心流程
Python 分析服务
代码解析与规范化
多维相似度计算
题目复杂度评分
动态阈值生成
证据片段定位
实验评测流程
报告导出
文件上传安全
异常与降级处理
```

### 1.2 项目特殊测试目标

本项目区别于普通 Web 系统，必须额外验证：

```text
简单题自然相似风险较高时，动态阈值会提高。
复杂题解法空间较大时，结构相似会更可疑。
变量名、函数名、参数名替换后，规范化结果应保持稳定。
通用模板相似不能直接导致高风险。
稀有片段相似应提升风险证据权重。
解析失败时不得伪造 AST/CFG/IR 证据。
系统输出的是风险辅助判断，而不是抄袭结论。
```

---

## 2. 测试分层

### 2.1 测试层级

```text
Unit Test：函数级与类级测试
Integration Test：模块联调测试
API Test：接口测试
Algorithm Golden Test：算法金样例测试
E2E Test：端到端流程测试
Experiment Test：实验复现测试
Security Test：上传与权限安全测试
Performance Test：性能和容量测试
Regression Test：回归测试
Acceptance Test：验收测试
```

### 2.2 推荐工具

```text
Java Backend：JUnit 5, Mockito, Spring Boot Test, Testcontainers（可选）
Python Analysis：pytest, pytest-cov
Frontend：Vitest, Playwright（增强版）
API：Postman / Newman / HTTPie
Performance：JMeter / k6
Static Check：Checkstyle / Spotless / Ruff / Black / ESLint
```

---

## 3. 后端测试

### 3.1 用户与权限测试

V1 若暂不启用完整权限，也要保留接口测试。

测试用例：

```text
登录成功
登录失败
未登录访问受保护接口
普通用户访问他人任务
管理员访问所有任务
Token 过期
```

验收标准：

```text
错误码明确
不会泄露密码 hash
权限失败返回 FORBIDDEN 或 UNAUTHORIZED
```

### 3.2 题目管理测试

测试用例：

```text
创建题目成功
题目标题为空失败
题目描述为空失败
更新题目成功
查询题目详情成功
分页查询题目成功
删除题目为逻辑删除
已删除题目不进入普通列表
```

### 3.3 代码上传测试

测试用例：

```text
上传 Java 文件成功
上传 Python 文件成功
上传 C 文件成功
上传空文件失败
上传超大文件失败
上传不支持后缀失败
文件名包含 ../ 时被拒绝或安全重命名
重复文件 hash 可识别
批量上传部分成功部分失败
```

验收标准：

```text
所有上传文件保存到受控目录
数据库记录 raw_code_path
不执行上传代码
不使用原始文件名作为唯一存储路径
```

### 3.4 检测任务测试

测试用例：

```text
创建任务成功
submission 数量小于 2 时失败
题目不存在时失败
提交不属于该题目时失败
启动任务成功
重复启动任务被拒绝
查询任务进度成功
任务失败时记录 error_message
任务完成后可查询结果
```

### 3.5 结果与证据测试

测试用例：

```text
查询结果总览成功
按风险等级过滤成功
按风险分数排序成功
查询结果详情成功
查询 similarity metrics 成功
查询 threshold adjustment 成功
查询 evidence 成功
查询 identifier mappings 成功
查询 diff-view 成功
```

验收标准：

```text
结果包含 raw_similarity_score
结果包含 calibrated_risk_score
结果包含 dynamic_threshold
结果包含 risk_level
结果包含 evidence_count
```

### 3.6 报告导出测试

测试用例：

```text
任务未完成时不允许导出完整报告
任务完成后导出 HTML 成功
导出报告路径入库
报告文件可下载
报告包含题目特征、阈值解释、风险结果和证据
```

---

## 4. 分析服务测试

### 4.1 语言识别测试

测试样例：

```text
.java -> java
.py -> python
.c -> c
.h -> c 或 header
未知后缀 -> UNKNOWN
```

验收标准：

```text
不支持语言必须明确返回 UNSUPPORTED_LANGUAGE
不能错误地当作其他语言继续结构分析
```

### 4.2 代码清洗测试

测试用例：

```text
删除单行注释
删除多行注释
保留字符串中的 // 和 /* */
统一换行符
保留行号映射
去除多余空白但不破坏语义
```

关键要求：

```text
清洗后代码必须能够映射回原始代码行号。
证据高亮依赖行号映射，不能只保存清洗后行号。
```

### 4.3 Token 提取测试

测试用例：

```text
Java 基础 token 提取
Python 基础 token 提取
C 基础 token 提取
忽略注释影响
字符串字面量稳定处理
数字常量稳定处理
```

### 4.4 AST 解析测试

测试用例：

```text
Java class/function/loop/if 解析
Python function/loop/if 解析
C function/loop/if 解析
语法错误代码 fallback
空文件失败
超长文件可被限制
```

验收标准：

```text
解析成功返回 AST artifact
解析失败返回 parse diagnostics
解析失败允许 token fallback
```

---

## 5. 置换不变规范化测试

### 5.1 变量名归一化测试

输入 A：

```java
int sum = a + b;
```

输入 B：

```java
int result = x + y;
```

期望：

```text
TYPE VAR_1 = VAR_2 + VAR_3
```

测试标准：

```text
变量名不同但结构相同时 canonical tokens 一致或高度相似。
```

### 5.2 作用域测试

测试用例：

```text
不同函数中的局部变量独立编号
内层作用域变量遮蔽外层变量
参数和局部变量分开编号
全局变量单独标记
```

### 5.3 函数名归一化测试

测试用例：

```text
solve() 和 mainLogic() 结构相似时函数名不影响主体相似度
递归函数名调用需要映射为 SELF_CALL
库函数名不能全部归一化丢失语义
```

### 5.4 可交换表达式测试

输入：

```text
a + b
b + a
x * y
y * x
```

期望：

```text
加法和乘法表达式 canonical 后一致
减法和除法不得随意交换
```

### 5.5 局部语句重排测试

测试用例：

```text
两个无依赖赋值语句交换后保持相似
存在数据依赖时不得交换
存在 IO 顺序依赖时不得交换
存在函数副作用时不得交换
```

### 5.6 AST Fingerprint 测试

测试用例：

```text
变量改名后 fingerprint 稳定
格式化后 fingerprint 稳定
删除注释后 fingerprint 稳定
更换核心算法后 fingerprint 明显变化
```

---

## 6. 题目复杂度评分测试

### 6.1 简单题测试

题目：A+B 或统计偶数。

期望：

```text
DifficultyScore 低
SolutionSpaceScore 低
TemplateRiskScore 中高
NaturalSimilarityRisk 高
RecommendedThreshold 高于默认阈值
```

### 6.2 模板题测试

题目：排序、二分、标准 DFS。

期望：

```text
TemplateRiskScore 高
NaturalSimilarityRisk 中高
通用模板证据权重降低
```

### 6.3 复杂题测试

题目：动态规划变形、图算法综合、业务规则题。

期望：

```text
DifficultyScore 高
SolutionSpaceScore 高
NaturalSimilarityRisk 低或中
结构高度相似时更容易超过动态阈值
```

### 6.4 参考答案特征测试

测试用例：

```text
无参考答案时仅用题面特征评分
有参考答案时加入行数、函数数、圈复杂度
多个参考答案时取统计特征
参考答案解析失败时不影响题面评分
```

### 6.5 评分稳定性测试

同一题目、同一 feature_version，多次计算应保持一致。

验收标准：

```text
不允许无种子随机性影响评分
不允许依赖不可复现的 LLM 直接给最终分
```

---

## 7. 动态阈值测试

### 7.1 阈值方向测试

测试规则：

```text
自然相似风险升高 -> 阈值应升高
模板风险升高 -> 阈值应升高或通用结构权重降低
题目难度升高 -> 阈值可降低
解法空间升高 -> 阈值可降低
```

### 7.2 阈值边界测试

必须限制阈值范围：

```text
minThreshold <= dynamicThreshold <= maxThreshold
```

推荐：

```text
0.60 <= dynamicThreshold <= 0.95
```

测试用例：

```text
极简单题不会超过 0.95
极复杂题不会低于 0.60
缺少题目特征时使用默认阈值
```

### 7.3 阈值解释测试

每个结果必须能返回：

```text
baseThreshold
difficultyAdjustment
solutionSpaceAdjustment
templateRiskAdjustment
naturalSimilarityAdjustment
finalThreshold
explanation
```

---

## 8. 相似度计算测试

### 8.1 TokenSimilarity 测试

测试用例：

```text
完全相同代码 -> 高相似
只改格式 -> 高相似
只改变量名 -> 中高相似
完全不同算法 -> 低相似
```

### 8.2 ASTSimilarity 测试

测试用例：

```text
变量名修改后 AST 结构相似度高
同样控制结构不同变量名 -> 高相似
同题不同解法 -> 中低相似
不同题代码 -> 低相似
```

### 8.3 ControlFlowSimilarity 测试

测试用例：

```text
for-if-count 结构相同 -> 高
for 改 while 但逻辑相同 -> 中高
递归和迭代解法 -> 中或低，取决于 IR 版本
```

### 8.4 DataDependencySimilarity 测试

测试用例：

```text
相同变量读写链 -> 高
变量名不同但依赖关系相同 -> 高
只控制结构相同但数据流不同 -> 不应过高
```

### 8.5 RareFragmentSimilarity 测试

测试用例：

```text
相同魔法数处理 -> 提升风险
相同特殊边界条件 -> 提升风险
相同错误处理分支 -> 提升风险
普通 for 循环不应被判为稀有片段
```

### 8.6 综合风险测试

测试用例：

```text
所有通道高 -> 高风险
Token 高但 AST/CFG 低 -> 中或低风险
AST 高但自然相似风险高 -> 风险被校准
稀有片段高且题目复杂 -> 风险提升
```

---

## 9. 证据生成测试

### 9.1 证据完整性

每条证据必须包含：

```text
evidence_type
confidence
similarity_score
code_a_start_line
code_a_end_line
code_b_start_line
code_b_end_line
title
description
```

测试不允许：

```text
没有行号的可视化证据
没有说明的证据
没有 confidence 的证据
```

### 9.2 证据准确性

测试用例：

```text
高亮行号确实对应相似片段
变量映射表与代码中标识符一致
AST 证据不指向无关代码
稀有片段证据不包含普通模板结构
```

### 9.3 证据排序

期望排序：

```text
高置信度优先
稀有片段优先
结构证据优先于纯 token 证据
同类证据按 similarity_score 排序
```

### 9.4 证据上限

测试：

```text
maxEvidencePerPair = 20 时，不返回超过 20 条主证据
但 summary 中可以记录总证据数量
```

---

## 10. 跨语言测试

### 10.1 Java-Python 等价结构测试

样例：

```text
Java enhanced for + if + count
Python for + if + count
```

期望：

```text
IR 层结构相似度中高
Token 相似度低
结果解释应说明跨语言结构相似，而非 token 相似
```

### 10.2 Java-C 等价结构测试

样例：

```text
Java 数组循环
C 数组下标循环
```

期望：

```text
在有限 IR 支持下能识别循环、条件、计数结构
若无法识别，应明确显示跨语言证据不足
```

### 10.3 非等价跨语言测试

```text
同题但完全不同算法
不同题但都有 for-if 结构
```

期望：

```text
不得仅因通用控制结构相似给高风险
```

---

## 11. 实验测试

### 11.1 数据集导入测试

测试用例：

```text
导入公开样本成功
导入人工伪装样本成功
导入 AI 改写样本成功
样本标签正确保存
伪装等级正确保存
语言对正确保存
```

### 11.2 对比方法测试

必须能运行：

```text
STRING_BASELINE
TOKEN_BASELINE
AST_BASELINE
FIXED_THRESHOLD
PICAS_STANDARD
PICAS_ABLATION_NO_PROBLEM
PICAS_ABLATION_NO_CANONICAL
```

增强版运行：

```text
JPLAG
DOLOS
PICAS_CROSSLANG
```

### 11.3 指标计算测试

给定混淆矩阵：

```text
TP, FP, TN, FN
```

必须正确计算：

```text
Precision
Recall
F1
Accuracy
False Positive Rate
False Negative Rate
```

### 11.4 分组统计测试

必须支持按以下维度分组：

```text
题目难度
伪装等级
语言对
方法名
是否启用动态阈值
是否启用规范化
```

### 11.5 消融实验测试

测试目标：

```text
去掉题目感知模块后，简单题误报率应上升或不下降。
去掉规范化模块后，变量名伪装召回率应下降。
去掉稀有片段模块后，高级伪装识别能力应下降或不提升。
```

---

## 12. 前端测试

### 12.1 页面可用性测试

页面：

```text
题目列表
题目详情
任务创建
任务进度
结果总览
代码对比证据
实验看板
报告下载
```

测试：

```text
页面能打开
接口错误有提示
加载中有状态
空数据有占位
分页正常
排序正常
筛选正常
```

### 12.2 代码对比测试

测试用例：

```text
Monaco Editor 正确显示 Java/Python/C
左右代码滚动正常
证据点击后跳转对应行
高亮范围准确
多条证据可切换
```

### 12.3 图表测试

测试内容：

```text
多维相似度雷达图
动态阈值分解图
风险分布柱状图
实验指标折线/柱状图
消融实验对比图
```

验收标准：

```text
图表数据来自 API，不写死
指标名称与后端一致
空数据时不报错
```

---

## 13. API 测试

### 13.1 Postman/Newman 集合

建议维护：

```text
postman/CodeRisk-Core.postman_collection.json
postman/CodeRisk-Experiment.postman_collection.json
```

核心流程：

```text
创建题目
上传参考答案
上传提交
计算题目特征
创建任务
启动任务
轮询状态
查询结果
查询证据
导出报告
```

### 13.2 API 响应测试

每个接口测试：

```text
success 字段存在
code 字段存在
message 字段存在
data 字段存在
traceId 字段存在
失败时错误码明确
```

---

## 14. 安全测试

### 14.1 文件上传安全

测试用例：

```text
上传 ../evil.java
上传空文件
上传超大文件
上传 exe 改后缀
上传包含大量特殊字符的文件名
上传压缩炸弹样式文件（若支持 zip）
```

验收标准：

```text
系统不崩溃
文件不会写出 storage 目录
不执行用户代码
错误信息不暴露服务器路径
```

### 14.2 权限测试

测试用例：

```text
未登录下载报告
普通用户访问他人任务
普通用户删除他人题目
普通用户运行实验管理接口
```

### 14.3 代码执行安全

必须确认：

```text
系统只解析代码，不运行代码。
任何上传文件不得被 shell 执行。
分析服务不得使用 eval/exec 执行用户代码。
```

---

## 15. 性能测试

### 15.1 基础性能目标

V1：

```text
20 份代码以内任务可稳定完成
100 个代码对以内任务可稳定展示
单结果详情 2 秒内返回
结果总览分页 2 秒内返回
```

V2：

```text
100 份代码任务可完成
4950 个代码对可批处理
支持异步状态查询
```

### 15.2 性能测试场景

```text
10 份代码小任务
50 份代码中任务
100 份代码大任务
单文件 1000 行
混合 Java/Python/C
高风险证据较多任务
```

### 15.3 指标

```text
任务总耗时
平均单代码对耗时
解析耗时
规范化耗时
相似度计算耗时
证据生成耗时
结果入库耗时
接口响应时间
```

---

## 16. 回归测试

每次修改算法后必须运行：

```text
Golden Case Test
Canonicalization Test
Problem Scoring Test
Threshold Test
Evidence Test
Experiment Metric Test
```

回归测试必须保证：

```text
旧的核心样例结果不发生无法解释的变化
若算法版本变化导致结果变化，必须记录 algorithm_version
```

---

## 17. Golden Cases 设计

必须建立 `tests/golden_cases/`，包括：

```text
case_001_identical_code
case_002_variable_rename
case_003_function_rename
case_004_format_comment_change
case_005_local_reorder_safe
case_006_local_reorder_unsafe
case_007_template_natural_similarity
case_008_complex_high_similarity
case_009_cross_language_equivalent
case_010_different_algorithm_same_problem
case_011_ai_rewrite
case_012_parse_failed_fallback
```

每个 Golden Case 包含：

```text
question.md
A.java / A.py / A.c
B.java / B.py / B.c
expected.json
README.md
```

expected.json 示例：

```json
{
  "expectedRiskLevel": "HIGH",
  "expectedMetricRanges": {
    "AST_SIMILARITY": [0.80, 1.00],
    "TOKEN_SIMILARITY": [0.50, 1.00]
  },
  "expectedEvidenceTypes": ["AST_SUBTREE", "IDENTIFIER_MAPPING"],
  "notes": "变量名替换后仍应识别为高结构相似。"
}
```

---

## 18. 推荐测试命令

### 18.1 后端

```bash
cd backend-springboot
mvn test
```

### 18.2 分析服务

```bash
cd analysis-service-python
pytest -q
pytest --cov=app tests/
```

### 18.3 前端

```bash
cd frontend-vue
npm install
npm run lint
npm run test
npm run build
```

### 18.4 全量测试脚本

建议提供：

```bash
bash scripts/run_all_tests.sh
```

内容：

```text
后端测试
Python 测试
前端构建
API smoke test
Golden cases
```

---

## 19. 验收测试清单

项目达到毕设完整版至少满足：

```text
1. 能创建题目并上传多份代码。
2. 能完成 Java/Python 至少两种语言检测。
3. 能输出 token 与 AST 相似度。
4. 能完成变量名、函数名、参数名规范化。
5. 能计算 DifficultyScore、SolutionSpaceScore、TemplateRiskScore、NaturalSimilarityRisk。
6. 能生成 dynamicThreshold。
7. 能输出 weightedSimilarityScore、dynamicThreshold、riskMargin、calibratedRiskScore、exceedThreshold 与 marginScale。
8. 能输出 LOW/MEDIUM/ELEVATED/HIGH 风险等级。
9. 能展示相似代码片段和证据类型。
10. 能导出检测报告。
11. 能运行至少一组对比实验。
12. 能展示固定阈值与动态阈值差异。
```

项目达到期刊增强版至少满足：

```text
1. 有公开或自建实验数据集。
2. 有 L0-L8 伪装等级样本。
3. 有至少 4 种 baseline。
4. 有消融实验。
5. 有 Precision、Recall、F1、FPR、FNR。
6. 有按题目难度分组分析。
7. 有失败案例分析。
8. 有运行时间分析。
9. 有可复现实验配置。
10. 有导出的实验报告和图表。
```

---

## 20. 禁止事项

```text
禁止没有测试就修改核心算法。
禁止只测试 happy path。
禁止没有 Golden Case 就声称规范化有效。
禁止没有固定阈值 baseline 就声称动态阈值有效。
禁止解析失败时输出结构证据。
禁止前端写死实验结果图表。
禁止只用一两个样例证明论文结论。
禁止把 LLM 输出当作最终测试 oracle。
```

---

## 21. 测试通过标准

每次阶段交付必须满足：

```text
后端核心单元测试通过
Python 分析服务单元测试通过
Golden Cases 通过
API Smoke Test 通过
前端 build 通过
无阻断级安全问题
核心文档与实现保持一致
```

阶段性允许存在非阻断问题，但必须记录在：

```text
TEST_REPORT.md
KNOWN_ISSUES.md
```

---

## 22. 测试报告模板

每次大版本输出测试报告：

```text
版本号：
测试日期：
测试范围：
测试环境：
通过用例数：
失败用例数：
阻断问题：
非阻断问题：
算法 Golden Cases 结果：
实验指标摘要：
性能测试摘要：
结论：是否可进入下一阶段
```

## 23. V4 前置收口自动化覆盖

当前新增回归覆盖：风险等级四个精确边界、calibrated score clamp、Python 嵌套作用域 shadowing、Java 变量/函数/参数改名、解析失败 token-only 且无 AST/canonical/mapping 证据、Flyway V1/V2、分页结果契约、复现字段、报告安全措辞、Research V4 schema/哈希/覆盖统计、problem/source/hash split 泄漏拒绝、录入辅助、JPlag manifest 对齐、validation-only 校准和统一论文表格输出。

阶段测试报告与非阻断问题分别记录在项目根目录 `TEST_REPORT.md` 和 `KNOWN_ISSUES.md`。

## 24. V4 Phase 1-2 回归覆盖

```text
PICAS_STANDARD 不生成任何 CROSSLANG metric/evidence
三个 CROSSLANG metric 权重均为 0
Java/Python IR 与 lightweight summary golden cases
解析失败无 IR/control/data-flow structure evidence
unsupported syntax 保留 warning
Phase 2 固定 7-case 数据集与运行中不修改 test set 标记
JPlag 6.2.0 native CSV adapter
前端/HTML 报告实验性与非完整 CFG/DFG 标注
```

## 25. Research V4 数据与实验门禁

```text
Research manifest 聚合现有 shard，空 manual shard 不得伪造样例
每 case 必填 label/case type/language/problem/source/split/version/origin/provenance
problem/source/exact-code hash 任一跨 split overlap 均失败
声明 hash 与实际文件 hash 不一致时失败；路径逃逸时失败
synthetic/placeholder/source_type/eligible 组合必须一致
UNCERTAIN 不进入核心分类指标
未完成人工与功能验证的 AI_REWRITE 不进入核心指标
校准候选只能按 validation 指标排序，testSetUsedForSelection 必须为 false
JPlag 输入、排除原因、原生输出和 pair_id 映射必须可追溯
统一 runner 输出 E1-E5、跨语言矩阵、外部基线注册、论文表格、失败与边界案例
run manifest 固定 productionFormulaChanged=false、experimentalMetricsProductionWeight=0.0
PICAS_STANDARD 运行态回归不出现任何 CROSSLANG metric
```

补数据、运行实验和论文取材必须使用以下检查清单：

```text
coderisk/experiment/RESEARCH_V4_CHECKLIST.md
```

验收时至少确认：

```text
DATA_COLLECTION_GUIDE.md 中的 source_type 与 eligibility 规则被遵守
RUN_RESEARCH_V4.md 中的 validator、calibration、JPlag 和 full runner 命令可执行
RESULT_INTERPRETATION_GUIDE.md 中的禁止夸大表述被遵守
PAPER_MATERIALS_GUIDE.md 中的 seed/exploratory/formal claim 边界被遵守
```
