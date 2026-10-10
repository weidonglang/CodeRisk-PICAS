# ROADMAP.md

> 2026-10-10 研究阶段 2 完成工具链增量：14 方法隔离消融及 synthetic 实跑，新测试 19 项、当前工作树全量 337 项通过；生产公式/规范化源码与上一批哈希不变。正式关系效果仍未验收，下一步先补可信独立解答参考与新题冻结，再设计/验证统计上尾校准；不能用旧 test 调参。见 [消融结果与限制](research/SIMILARITY_ABLATION.md)。

> 2026-10-10 开题第一批完成：精准实现审计 + 有限改名规范化修复、自动置换/反例/API 测试和条件证明草图；55 项新增测试、当前工作树 Python 318 / H2 后端 19 项通过，前端构建成功。仅完成研究实施计划阶段 0–1；没有提升 V4 生产权重。下一步 P0 是可信独立数据与冻结消融，再做隔离统计校准；LLM/混合属于 P1/P2，许可和可靠基线是前置条件。见 [交付和阻塞](research/FIRST_BATCH_REPORT.md)。

> 2026-10-09 本轮增量：异步启动、有界工作池、时间预算、成功结果复用、失败历史与启动恢复已实现；IR-Plag 467 份源码/52 对复核材料与融合分解已完成。实际双人复核及新数据上的算法效果验证仍待完成。 依据与边界见 [前三项推进记录](proposal/NEXT_THREE_PROGRESS.md)。

> 2026-10-09：版本声明与解析限制、共同模板诊断、依据不足提示已实现，含 Java/Python/C/HTML 合成边界验证。跨版本安全结构对齐、真实独立参考池和自然相似误报校准仍待完成，见 [本轮边界](proposal/VERSION_AND_NATURAL_SIMILARITY.md)。

> 2026-10-09：3,865 条源码版本质量登记、1,174 对未标注队列、43 对首批盲审和连通分组提案已完成。ConPlag 单人公开标签探索方案已运行前冻结并上传，固定阈值/规范化/JPlag 的实际结果及图表见 [探索结果](proposal/CONPLAG_PILOT_RESULTS.md)；正式双人标签、可靠题目画像、自然相似负例和作者隔离仍待完成。入口见 [复核说明](proposal/DATA_REVIEW_WORKBENCH.md)。

> 2026-10-08 当前增量：[C、HTML 检测与多语言数据接收](proposal/MULTILANGUAGE_PROGRESS.md)已完成；新增 366 份官方来源源码/教学示例，执行逐文件完整性及解析审计，尚无本批可靠代码对标签。C 结构解析与保守规范化已实现，完整预处理和语言混杂复核仍待完成；HTML 校准、C/HTML 基线和正式独立测试尚未完成。以下历史路线图中的 C 增强目标仍包括这些未完成能力。

> 2026-10-08 增量：开题交流准备、数据/标注/分集规范及空白登记表已整理；公平评测runner已实现验证集选参、规范化消融、JPlag共同集合比较和分组统计；核心正确性修复见 [记录](proposal/CORE_REVIEW.md)。此前用合成开发数据跑通流程；真实公开数据已接收，正式复核、冻结测试和学校审批未完成。

> 本文件定义 CodeRisk / PICAS 项目的阶段路线图。路线图按“先闭环、再创新、再实验、再成果”的原则安排。任何阶段不得为了非核心功能牺牲算法正确性、实验可复现性和证据可解释性。

---

## 0. 当前实现状态

截至 2026-06-20，已完成 V2 主交付代码闭环，并建立 V3 最小可复现实验闭环：

```text
[x] Spring Boot 后端骨架、统一 ApiResponse、traceId、健康检查、语言支持接口
[x] JDBC/Flyway 持久化 Question、Submission、Task、ProblemFeature、Result、Metric、Threshold、Evidence、IdentifierMapping、Report
[x] MySQL 8 生产 profile 与初始化脚本；local/test 使用 H2 MySQL compatibility 验证同一迁移
[x] 代码上传接口，支持 Java/Python 稳定标记与 C/C++ experimental 标记
[x] DetectionTask 创建、启动、状态查询、近期任务、结果列表与结果汇总接口
[x] 保留 FastAPI mock 分析接口与后端 mock 结果保存能力，用于 V0 回归
[x] FastAPI `/internal/analyze/pair` 初版 token n-gram 相似度，Java/Python 注释处理与基础测试
[x] Java/Python 最小 AST 节点序列相似度，解析失败时降级并输出 PARSER_WARNING
[x] Python/Java scope-aware 标识符归一化，区分变量、参数、函数和类名
[x] canonical token similarity、mapping coverage / consistency 与 identifier mapping evidence
[x] variable rename / function rename / parameter rename 可执行 golden cases
[x] 规则版 DifficultyScore、SolutionSpaceScore、TemplateRiskScore、NaturalSimilarityRisk
[x] 按 FORMULA_SPEC_V1 计算有界 dynamicThreshold、riskMargin、calibratedRiskScore、exceedThreshold
[x] 结果页展示综合分、动态阈值、风险边际、题目画像和阈值分解
[x] 题目画像内部接口与后端 `/api/questions/{questionId}/features/*` 接口
[x] Spring Boot 任务启动默认调用真实 token 分析 endpoint，结果标记为 `isMock=false`
[x] token 相似片段定位、基础行号证据、`diff-view` 高亮数据接口
[x] FastAPI 分析服务骨架、健康检查、mock 分析接口、上传路径约束
[x] Vue 3 前端骨架、Dashboard、题目列表、题目创建、代码上传、任务列表、结果页面、结果证据详情页
[x] 本地 README、环境变量示例、MySQL/Redis docker-compose、golden cases 目录
[x] 后端测试、分析服务测试、前端 build 均已通过
[x] 已完成一次本地端到端联调：创建题目、上传两份代码、创建任务、启动任务、返回 token 分析结果
[x] HTML 相似风险报告生成、artifact 写入、SHA-256 元数据、下载接口与前端入口
[x] V3 36-case 合成数据，覆盖五类题型并按 problem-level validation/test 隔离
[x] E1-E4 对比/消融、E5 失败与边界案例输出，validation 仅选择固定阈值基线
[x] JPlag 运行入口、标准化导入 adapter、输入输出契约和测试骨架；未导入真实 JPlag 指标
[x] 实验记录 formulaVersion、algorithmVersion、datasetVersion、randomSeed、git/local version 和 machine info
[x] 轻量实验结果页读取真实 artifacts，不使用 mock 指标
```

当前尚未完成：

```text
[ ] 使用本机 MySQL 管理凭据完成一次真实 MySQL profile 启动验证
[ ] 复杂 AST 子树匹配，非 V1 必需
[ ] Monaco Editor 代码对比与点击证据定位
[ ] V3 正式规模数据集、真实 JPlag/Dolos 运行与统计显著性
```

因此当前版本可标记为 `V4 Ready candidate`。V3 输出来自 36 个 problem-level 分离的合成案例，仍不是正式大规模 benchmark；动态阈值相对固定 0.70 降低自然相似误报，但召回损失和其他固定阈值反例必须同时报告。

---

## 1. 总体路线

项目总路线：

```text
Phase 0：项目骨架与规范
Phase 1：基础业务闭环
Phase 2：代码预处理与基础相似度
Phase 3：置换不变规范化
Phase 4：题目复杂度评分与动态阈值
Phase 5：风险报告与证据输出
Phase 6：前端可解释展示
Phase 7：实验数据集与对比实验
Phase 8：跨语言 IR 与增强算法
Phase 9：论文、专利、软著材料整理
Phase 10：发布与答辩准备
```

总体优先级：

```text
V1 可运行闭环
→ V2 本科毕设创新闭环
→ V3 期刊实验增强
→ V4 研究扩展
```

---

## 2. 版本目标

### V1：基础可运行版

目标：让系统可以完成一次从题目创建到代码相似度结果展示的完整流程。

验收标准：

```text
[x] Spring Boot 主服务可启动
[x] Python 分析服务可启动
[x] 前端可启动
[x] 可创建题目
[x] 可上传 Java/Python 代码
[x] 可创建检测任务
[x] 可计算 token 相似度
[x] 可计算基础 AST 相似度
[x] 可展示风险结果列表
[x] 可查看代码对比页，轻量版
```

### V2：本科毕设版

目标：体现项目核心创新。

验收标准：

```text
[x] 实现标识符归一化
[x] 实现题目复杂度评分，规则版
[x] 实现模板化风险评分，规则版
[x] 实现自然相似风险评分，规则版
[x] 实现动态阈值初版
[x] 实现多维风险评分初版
[x] 实现结构化证据输出
[x] 实现 HTML 报告导出
[x] 完成 V3 minimal 基础实验对比
```

### V3：期刊增强版

目标：让项目具备投稿支撑。

验收标准：

```text
[ ] 构建 L0-L8 伪装数据集
[x] 完成固定阈值 vs 动态阈值最小对比
[x] 完成 token / AST / 本文方法最小对比
[x] 完成规范化模块最小消融
[x] 完成题目感知模块最小消融
[ ] 完成不同题目难度分组实验
[x] 完成失败与 borderline 案例文件输出
[ ] 输出论文图表
[ ] 输出实验报告
```

### V4：研究扩展版

目标：增强研究深度。

验收标准：

```text
[ ] 实现 Java-Python 初步语言无关 IR
[ ] 增强 C 语言解析
[ ] 增加控制流相似度
[ ] 增加数据依赖相似度
[ ] 支持 JPlag/Dolos 外部结果导入
[ ] 支持 AI 改写样本评测
[ ] 完成更大规模实验
```

---

## 3. Phase 0：项目骨架与规范

### 3.1 目标

建立稳定项目结构，避免后续返工。

### 3.2 任务

```text
TASK-0001 创建仓库目录结构
TASK-0002 创建 docs 文档目录
TASK-0003 创建 Spring Boot 后端骨架
TASK-0004 创建 FastAPI 分析服务骨架
TASK-0005 创建 Vue 3 前端骨架
TASK-0006 创建 docker-compose 基础环境
TASK-0007 配置 MySQL、Redis
TASK-0008 配置统一日志格式
TASK-0009 配置基础测试命令
TASK-0010 创建示例数据目录
```

### 3.3 推荐目录

```text
coderisk/
  backend-springboot/
  analysis-service-python/
  frontend-vue/
  experiment/
  docs/
  scripts/
  deploy/
  data/
  README.md
```

### 3.4 验收

```text
[ ] 后端健康检查接口可访问
[ ] 分析服务健康检查接口可访问
[ ] 前端首页可访问
[ ] docker-compose 可启动 MySQL/Redis
[ ] README 有本地启动说明
```

---

## 4. Phase 1：基础业务闭环

### 4.1 目标

完成题目、提交、任务、结果的基本业务闭环。

### 4.2 后端任务

```text
TASK-0101 实现 Question 实体与表结构
TASK-0102 实现 Submission 实体与表结构
TASK-0103 实现 DetectionTask 实体与表结构
TASK-0104 实现 AnalysisResult 实体与表结构
TASK-0105 实现 Evidence 实体与表结构
TASK-0106 实现题目 CRUD
TASK-0107 实现代码文件上传
TASK-0108 实现任务创建接口
TASK-0109 实现任务状态查询接口
TASK-0110 实现结果查询接口
```

### 4.3 分析服务任务

```text
TASK-0121 实现 /health
TASK-0122 实现 /analyze/pair mock 接口
TASK-0123 定义分析请求模型
TASK-0124 定义分析响应模型
```

### 4.4 前端任务

```text
TASK-0131 创建基础布局
TASK-0132 题目列表页
TASK-0133 题目创建页
TASK-0134 代码上传页
TASK-0135 任务列表页
TASK-0136 结果列表页
```

### 4.5 验收

```text
[x] 可以创建题目
[x] 可以上传代码
[x] 可以创建检测任务
[x] 可以调用分析服务返回结果
[x] 可以在前端看到风险结果
```

---

## 5. Phase 2：代码预处理与基础相似度

### 5.1 目标

实现最小可用算法：代码清洗、token 相似度、基础 AST 相似度。

### 5.2 任务

```text
TASK-0201 实现语言识别
TASK-0202 实现 Java 注释删除
TASK-0203 实现 Python 注释删除
TASK-0204 实现空白规范化
TASK-0205 实现 token 提取
TASK-0206 实现 token n-gram 指纹
TASK-0207 实现 token similarity
TASK-0208 接入 tree-sitter Java parser
TASK-0209 接入 tree-sitter Python parser
TASK-0210 提取 AST 节点类型序列
TASK-0211 实现 AST sequence similarity
TASK-0212 实现基础证据片段定位
TASK-0213 返回真实分析结果
```

### 5.3 算法底线

最少输出：

```text
token_similarity
ast_similarity
risk_score
risk_level
basic_evidence_list
```

### 5.4 验收

```text
[ ] 两份完全相同代码相似度接近 1
[ ] 只改注释后相似度保持较高
[ ] 只改格式后相似度保持较高
[ ] 完全不同代码相似度较低
[ ] 解析失败有明确错误
```

---

## 6. Phase 3：置换不变规范化

### 6.1 目标

增强系统对变量名、函数名、参数名替换的鲁棒性。

### 6.2 任务

```text
TASK-0301 实现变量名提取
TASK-0302 实现作用域内变量编号
TASK-0303 实现参数名归一化
TASK-0304 实现函数名归一化
TASK-0305 实现局部变量归一化
TASK-0306 实现常量抽象策略
TASK-0307 实现 canonical token sequence
TASK-0308 实现 canonical AST node sequence
TASK-0309 实现 identifier mapping evidence
TASK-0310 对比规范化前后相似度
```

### 6.3 规范化示例

原始：

```java
int sum = a + b;
```

规范化：

```text
TYPE VAR_1 = VAR_2 + VAR_3
```

### 6.4 验收

```text
[ ] 变量名全部替换后仍能识别高结构相似
[ ] 函数名替换后不显著降低相似度
[ ] 不同作用域变量不会错误合并
[ ] 能输出变量映射证据
[ ] 规范化前后对比结果可保存
```

---

## 7. Phase 4：题目复杂度评分与动态阈值

### 7.1 目标

实现项目第一核心创新：题目感知风险校准。

### 7.2 任务

```text
TASK-0401 提取题目描述长度特征
TASK-0402 提取输入输出格式复杂度
TASK-0403 提取约束条件数量
TASK-0404 提取模板关键词
TASK-0405 提取参考答案行数
TASK-0406 提取参考答案函数数量
TASK-0407 提取基础控制结构数量
TASK-0408 计算 DifficultyScore
TASK-0409 计算 SolutionSpaceScore
TASK-0410 计算 TemplateRiskScore
TASK-0411 计算 NaturalSimilarityRisk
TASK-0412 实现 DynamicThresholdCalculator
TASK-0413 输出动态阈值解释
```

### 7.3 初始阈值公式

可先实现配置化公式：

```text
DynamicThreshold =
  BaseThreshold
  + a * NaturalSimilarityRisk
  + b * TemplateRiskScore
  - c * DifficultyScore
  - d * SolutionSpaceScore
```

注意：所有参数必须配置化，不得硬编码在业务逻辑里。

### 7.4 验收

```text
[ ] 简单题阈值高于基础阈值
[ ] 模板题阈值高于基础阈值或降低模板结构权重
[ ] 复杂题阈值可低于基础阈值
[ ] 前端能展示阈值解释
[ ] 结果表保存动态阈值
```

---

## 8. Phase 5：风险报告与证据输出

### 8.1 目标

让结果从“一个分数”升级为“可复核证据链”。

### 8.2 任务

```text
TASK-0501 实现综合风险评分
TASK-0502 实现风险等级划分
TASK-0503 实现相似片段定位
TASK-0504 实现相似函数证据
TASK-0505 实现变量映射证据
TASK-0506 实现边界条件相似证据，增强项
TASK-0507 实现稀有片段证据，增强项
TASK-0508 实现人工复核建议生成
TASK-0509 实现 Markdown 报告导出
TASK-0510 实现前端证据详情接口
```

### 8.3 报告必须包含

```text
题目信息
题目特征分数
动态阈值
代码对信息
多维相似度
综合风险分数
风险等级
证据列表
人工复核建议
免责声明：系统仅辅助复核，不直接判定抄袭
```

### 8.4 验收

```text
[ ] 高风险代码对有至少一条证据
[ ] 证据能定位到代码行
[ ] 报告可导出
[ ] 报告不出现“确定抄袭”表述
[ ] 前端能查看证据详情
```

---

## 9. Phase 6：前端可解释展示

### 9.1 目标

前端把算法创新显性化。

### 9.2 页面任务

```text
TASK-0601 任务创建页优化
TASK-0602 题目复杂度分析页
TASK-0603 检测结果总览页
TASK-0604 代码对比页
TASK-0605 Monaco Editor 集成
TASK-0606 相似片段高亮
TASK-0607 动态阈值解释卡片
TASK-0608 多维相似度图表
TASK-0609 变量映射表
TASK-0610 实验结果看板
```

### 9.3 验收

```text
[ ] 评委一眼能看到动态阈值
[ ] 评委一眼能看到多维相似度
[ ] 评委一眼能看到证据链
[ ] 左右代码对比清晰
[ ] 页面不依赖假数据作为真实结果
```

---

## 10. Phase 7：实验数据集与对比实验

### 10.1 目标

支撑期刊论文。

### 10.2 数据集任务

```text
TASK-0701 收集公开算法题代码
TASK-0702 构造简单题、中等题、复杂题分组
TASK-0703 构造 L0 原始样本
TASK-0704 构造 L1 变量名修改样本
TASK-0705 构造 L2 函数名修改样本
TASK-0706 构造 L3 注释/格式修改样本
TASK-0707 构造 L4 局部语句换序样本
TASK-0708 构造 L5 函数拆分/合并样本
TASK-0709 构造 L6 等价表达式替换样本
TASK-0710 构造 L7 跨语言改写样本
TASK-0711 构造 L8 AI 辅助改写样本
```

### 10.3 实验任务

```text
TASK-0721 固定阈值 vs 动态阈值
TASK-0722 token vs AST vs canonical method
TASK-0723 无题目感知 vs 有题目感知
TASK-0724 无规范化 vs 有规范化
TASK-0725 简单题误报率分析
TASK-0726 复杂题召回率分析
TASK-0727 不同伪装等级鲁棒性分析
TASK-0728 失败案例分析
```

### 10.4 指标

```text
Precision
Recall
F1-score
False Positive Rate
False Negative Rate
Accuracy
Average Detection Time
Evidence Hit Rate，人工复核命中率，增强项
```

### 10.5 验收

```text
[ ] 实验脚本可重复运行
[ ] 实验结果保存为 CSV/JSON
[ ] 图表可由脚本生成
[ ] 消融实验结果真实存在
[ ] 失败案例被记录
```

---

## 11. Phase 8：跨语言 IR 与增强算法

### 11.1 目标

作为研究增强项，不影响 V1/V2 主线。

### 11.2 任务

```text
TASK-0801 定义 LanguageIndependentIR
TASK-0802 Java AST 映射到 IR
TASK-0803 Python AST 映射到 IR
TASK-0804 基础循环结构抽象
TASK-0805 基础条件结构抽象
TASK-0806 赋值与更新结构抽象
TASK-0807 函数调用类型抽象
TASK-0808 IR 序列相似度
TASK-0809 Java-Python 对比实验
TASK-0810 C 语言解析增强
```

### 11.3 验收

```text
[ ] 至少支持 Java-Python 的 for/if/assignment/return 抽象
[ ] 跨语言结果标注为 experimental
[ ] 不夸大为完整语义等价检测
[ ] 有失败案例说明
```

---

## 12. Phase 9：论文、专利、软著材料整理

### 12.1 论文任务

```text
TASK-0901 整理论文题目
TASK-0902 整理相关工作
TASK-0903 整理方法章节
TASK-0904 整理系统实现章节
TASK-0905 整理实验章节
TASK-0906 整理图表
TASK-0907 整理失败案例
TASK-0908 整理结论与展望
```

### 12.2 专利任务

```text
TASK-0911 技术领域
TASK-0912 背景技术
TASK-0913 现有技术缺陷
TASK-0914 技术方案
TASK-0915 有益效果
TASK-0916 流程图
TASK-0917 实施例
TASK-0918 权利要求草案
```

### 12.3 软著任务

```text
TASK-0921 软件说明书
TASK-0922 用户手册
TASK-0923 源代码整理
TASK-0924 页面截图
TASK-0925 版本说明
```

### 12.4 注意顺序

如果计划申请发明专利，建议：

```text
先提交专利申请
再公开论文/GitHub 完整细节
```

---

## 13. Phase 10：发布与答辩准备

### 13.1 任务

```text
TASK-1001 完成 README
TASK-1002 完成 Quick Start
TASK-1003 完成 Docker Compose
TASK-1004 完成演示数据
TASK-1005 完成演示脚本
TASK-1006 完成答辩 PPT
TASK-1007 完成实验报告
TASK-1008 创建 release/v1.0.0
TASK-1009 录制演示视频
TASK-1010 整理常见问答
```

### 13.2 答辩演示顺序

```text
创建题目
展示题目复杂度分析
上传代码
运行检测
查看结果总览
查看高风险代码对
展示动态阈值解释
展示证据链
展示实验看板
总结创新点
```

---

## 14. 开发节奏建议

### 14.1 最短可行节奏，6-8 周

```text
第 1 周：项目骨架 + 基础 CRUD
第 2 周：代码上传 + 分析服务联通
第 3 周：token/AST 相似度
第 4 周：规范化 + 证据输出
第 5 周：题目评分 + 动态阈值
第 6 周：前端展示 + 报告导出
第 7 周：实验脚本
第 8 周：文档与答辩材料
```

### 14.2 期刊增强节奏，12-16 周

```text
第 1-2 周：骨架与基础业务
第 3-4 周：基础相似度
第 5-6 周：规范化与动态阈值
第 7-8 周：证据报告与前端
第 9-10 周：实验数据集
第 11-12 周：对比实验与消融实验
第 13-14 周：跨语言 IR 增强
第 15-16 周：论文、专利、软著材料
```

---

## 15. 风险与调整策略

### 15.1 跨语言 IR 难度过高

调整：

```text
Java-Python 有限支持即可
C 作为增强
论文中标注为 exploratory module
```

### 15.2 实验数据不足

调整：

```text
优先构造人工伪装数据集
再补公开算法题
最后再考虑真实学生作业
```

### 15.3 前端开发拖慢进度

调整：

```text
优先完成结果总览和代码对比
实验看板可先展示静态 CSV 结果
不要做复杂后台
```

### 15.4 算法效果不稳定

调整：

```text
保留失败案例
不要伪造结果
通过消融分析解释局限
```

---

## 16. 每阶段完成定义

任一阶段完成必须满足：

```text
[ ] 代码已提交
[ ] 本地可运行
[ ] 基础测试通过
[ ] 文档已更新
[ ] 有示例输入输出
[ ] 无虚假结果
[ ] 不破坏主线
```

---

## 17. 当前推荐下一步

2026年10月8日数据进展：已从官方源下载并独立导入AD2022的1,526份真实课程解答、ConPlag v3的911对已发表Java标签对，保存来源许可和完整性证据。未混入合成seed、未计算检测指标。后续先审查[公开数据接收报告](proposal/PUBLIC_DATA_INTAKE.md)中的原划分重叠、同ID变体和标签边界，再分别设计外部基准与课程实验协议。

当前最推荐的执行顺序：

```text
1. 使用有效本机凭据完成 MySQL 8 profile 实库 E2E
2. 以当前 91-pair synthetic seed 为流程底座，补充至少 20 个 manual、8 个经验证 ai_assisted、8 个 external 样例，并重新通过 problem/source/code-hash 隔离校验
3. 使用既有 validation-only 校准工具在真实 validation 数据上重新选择参数，test 仅做一次最终评估
4. 使用 manifest-aligned JPlag 流程重跑真实同语言样例；Dolos 继续保持非阻塞预留
```

Research V4 数据工具链已完成 91-pair synthetic seed、统一 schema、录入辅助、隔离校验、validation-only 校准、dataset-aligned JPlag 和论文表格生成。数量门槛仅由 synthetic seed 达成，因此状态仍是 `Research V4 seed toolchain ready`，不是正式 Research V4 benchmark；只有替换/补充可追溯真实数据并重新评估后才能升级论文结论。

执行第 2-4 步时先按以下文档操作：

```text
coderisk/experiment/datasets/research-v4/DATA_COLLECTION_GUIDE.md
coderisk/experiment/RUN_RESEARCH_V4.md
coderisk/experiment/RESULT_INTERPRETATION_GUIDE.md
coderisk/experiment/PAPER_MATERIALS_GUIDE.md
coderisk/experiment/RESEARCH_V4_CHECKLIST.md
```
