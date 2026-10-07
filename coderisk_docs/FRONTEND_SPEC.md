# FRONTEND_SPEC.md

> 本文件定义 CodeRisk / PICAS 前端系统的定位、页面、组件、交互、数据展示和验收标准。前端不承担算法创新，但必须把题目复杂度、动态阈值、多维相似度和结构化证据清晰展示出来，使系统区别于普通代码查重平台。

---

## 1. 前端定位

### 1.1 核心定位

前端是 CodeRisk / PICAS 的研究成果展示层，目标不是做复杂商业 SaaS，而是将后端算法结果转化为可理解、可复核、可答辩、可截图、可写入软著材料的界面。

前端必须突出以下主线：

```text
题目感知
动态阈值
置换不变结构表示
多维相似度
结构化证据链
实验对比
人工复核辅助
```

### 1.2 不做什么

首期前端不做：

```text
复杂社交功能
在线多人协作
复杂消息中心
低代码流程编排
3D 可视化
过度动画
复杂主题市场
商业计费系统
复杂组织架构审批
```

### 1.3 前端在项目中的价值

前端价值包括：

1. 支撑毕业设计系统演示；
2. 支撑软著截图；
3. 支撑论文案例图；
4. 支撑答辩时展示算法创新点；
5. 支撑教师人工复核流程；
6. 支撑实验结果可视化。

---

## 2. 技术栈

### 2.1 推荐技术栈

```text
Vue 3
Vite
TypeScript
Vue Router
Pinia
Element Plus
Axios
ECharts
Monaco Editor
Markdown 渲染组件
```

### 2.2 可选增强

```text
VueUse
FileSaver.js
html2pdf.js / 浏览器打印导出
diff-match-patch
xlsx 导出
```

### 2.3 不建议首期使用

```text
Nuxt
复杂 SSR
Three.js
大型低代码框架
复杂微前端
```

原因：这些技术不服务核心论文与系统演示，会增加开发复杂度。

---

## 3. 前端目录结构

推荐目录结构：

```text
frontend/
  src/
    api/
      auth.ts
      question.ts
      submission.ts
      task.ts
      result.ts
      evidence.ts
      experiment.ts
      system.ts
    assets/
    components/
      charts/
      code/
      evidence/
      layout/
      problem/
      result/
      upload/
    layouts/
      MainLayout.vue
      AuthLayout.vue
    router/
      index.ts
    stores/
      authStore.ts
      taskStore.ts
      resultStore.ts
      systemStore.ts
    types/
      api.ts
      question.ts
      submission.ts
      result.ts
      evidence.ts
      experiment.ts
    utils/
      request.ts
      format.ts
      risk.ts
      chart.ts
      download.ts
    views/
      LoginView.vue
      DashboardView.vue
      QuestionListView.vue
      QuestionDetailView.vue
      SubmissionUploadView.vue
      TaskCreateView.vue
      TaskDetailView.vue
      ProblemProfileView.vue
      ResultOverviewView.vue
      EvidenceCompareView.vue
      ExperimentDashboardView.vue
      ReportExportView.vue
      SettingsView.vue
```

---

## 4. 页面总览

首期必须完成以下页面：

```text
1. 登录页
2. 首页仪表盘
3. 题目列表页
4. 题目详情页
5. 代码上传页
6. 检测任务创建页
7. 任务详情与状态页
8. 题目复杂度分析页
9. 检测结果总览页
10. 代码对比与证据页
11. 实验结果看板
12. 报告导出页
13. 系统配置页
```

其中最重要的是：

```text
题目复杂度分析页
检测结果总览页
代码对比与证据页
实验结果看板
```

---

## 5. 全局布局设计

### 5.1 布局结构

```text
顶部栏：系统名称、当前用户、算法服务状态、退出按钮
侧边栏：导航菜单
主内容区：页面内容
底部状态栏：版本号、后端状态、分析服务状态
```

### 5.2 菜单结构

```text
首页概览
题目管理
代码提交
检测任务
结果分析
实验评测
报告导出
系统配置
```

### 5.3 系统名称显示

页面左上角显示：

```text
CodeRisk / PICAS
题目感知型代码相似风险检测系统
```

---

## 6. 登录页

### 6.1 页面目标

完成基础身份识别，不需要复杂注册体系。首期可使用内置演示账号。

### 6.2 页面元素

```text
系统 Logo / 名称
账号输入框
密码输入框
登录按钮
演示账号提示
错误提示
```

### 6.3 验收标准

```text
能输入账号密码
能调用登录接口
登录成功后进入首页
登录失败显示错误
Token 能保存到本地
刷新后能保持登录状态
```

---

## 7. 首页仪表盘

### 7.1 页面目标

展示系统整体状态，让评委或用户快速理解系统用途。

### 7.2 指标卡片

```text
题目数量
代码提交数量
检测任务数量
高风险代码对数量
平均检测耗时
算法服务状态
```

### 7.3 图表

```text
最近 7 天任务数量折线图
风险等级分布饼图
语言分布柱状图
```

### 7.4 最近任务表

字段：

```text
任务名称
题目名称
提交数量
状态
创建时间
完成时间
操作
```

---

## 8. 题目列表页

### 8.1 页面目标

管理检测题目，为后续代码上传和任务创建提供题目上下文。

### 8.2 功能

```text
题目列表
按标题搜索
按标签筛选
新增题目
编辑题目
删除题目
查看详情
```

### 8.3 表格字段

```text
题目 ID
题目标题
标签
语言范围
提交数量
DifficultyScore
NaturalSimilarityRisk
创建时间
操作
```

### 8.4 交互要求

题目列表不能只展示基本信息，还要展示题目画像核心指标，使用户知道系统是题目感知型。

---

## 9. 题目详情页

### 9.1 页面目标

集中展示题目信息、参考答案、复杂度分析、提交列表和任务入口。

### 9.2 页面区域

```text
题目基本信息
题目描述
输入输出格式
约束条件
参考答案
题目画像摘要
提交代码列表
创建检测任务按钮
```

### 9.3 题目画像摘要

展示：

```text
DifficultyScore
SolutionSpaceScore
TemplateRiskScore
NaturalSimilarityRisk
dynamicThreshold
```

---

## 10. 代码上传页

### 10.1 页面目标

支持批量上传学生代码，并显示语言识别结果。

### 10.2 上传区域

功能：

```text
拖拽上传
多文件选择
文件大小限制提示
支持语言提示
上传进度
上传结果列表
```

### 10.3 上传结果表

字段：

```text
文件名
学生编号/提交者
识别语言
文件大小
代码行数
上传状态
错误信息
```

### 10.4 验收标准

```text
支持至少 20 个文件批量上传
能够展示上传成功和失败文件
失败文件不影响成功文件保存
上传后可在提交列表看到记录
```

---

## 11. 检测任务创建页

### 11.1 页面目标

创建检测任务，选择检测模式和检测参数。

### 11.2 任务配置项

```text
任务名称
目标题目
提交范围
语言范围
检测模式
是否启用题目复杂度自适应
是否启用置换不变规范化
是否启用跨语言 IR
是否生成证据报告
是否保存中间产物
```

### 11.3 检测模式

```text
BASIC_TOKEN：只做 Token 基础检测
TOKEN_AST：Token + 基础 AST 检测
PICAS_INVARIANT：置换不变规范化检测
PICAS_STANDARD：题目感知 + 动态阈值 + 多维融合
PICAS_CROSSLANG：跨语言 IR 检测（实验性）
PICAS_EXPERIMENTAL：实验、消融、批处理
```

### 11.4 页面提示

每个检测模式旁边要有说明文字，例如：

```text
题目感知模式会根据题目复杂度和自然相似风险动态调整阈值，适合论文主实验。
```

---

## 12. 任务详情与状态页

### 12.1 页面目标

展示检测任务运行过程和状态。

### 12.2 状态流转

```text
CREATED
QUEUED
RUNNING
PARTIAL_SUCCESS
SUCCESS
FAILED
CANCELLED
```

### 12.3 展示内容

```text
任务名称
题目名称
提交数量
代码对数量
当前状态
进度条
已完成代码对数量
失败代码对数量
开始时间
结束时间
错误日志
```

### 12.4 实时刷新

首期可以使用轮询：

```text
每 2-3 秒刷新一次任务状态
```

后续可扩展 WebSocket。

---

## 13. 题目复杂度分析页

### 13.1 页面目标

这是前端最重要的创新展示页面之一，必须明确展示系统如何从题目出发调整查重策略。

### 13.2 核心指标卡片

```text
DifficultyScore
SolutionSpaceScore
TemplateRiskScore
NaturalSimilarityRisk
dynamicThreshold
```

每个指标必须有：

```text
分数
等级
一句解释
影响方向
```

例如：

```text
NaturalSimilarityRisk：0.82，高
解释：该题输入输出简单、参考答案较短，独立提交之间自然相似概率较高。
影响：系统将提高动态阈值，降低简单题误报。
```

### 13.3 图表

```text
题目画像雷达图
动态阈值贡献条形图
历史提交相似度分布直方图
```

### 13.4 动态阈值解释面板

展示：

```text
BaseThreshold
+ NaturalSimilarityAdjustment
+ TemplateRiskAdjustment
- DifficultyAdjustment
- SolutionSpaceAdjustment
+ HistoricalDistributionAdjustment
= dynamicThreshold
```

### 13.5 验收标准

```text
用户能理解动态阈值为什么变化
能显示题目画像五个核心指标
能展示每个指标对阈值的影响
能导出题目画像摘要
```

---

## 14. 检测结果总览页

### 14.1 页面目标

展示检测任务所有代码对风险情况，提供排序、筛选和进入证据页的入口。

### 14.2 顶部统计

```text
代码对总数
低风险数量
中风险数量
较高风险数量
高风险数量
平均风险分数
动态阈值
```

### 14.3 结果表格字段

```text
代码 A
代码 B
语言组合
RiskScore
dynamicThreshold
ExceededThreshold
riskLevel
TokenSimilarity
ASTSimilarity
IRSimilarity
EvidenceCount
检测耗时
操作
```

### 14.4 筛选条件

```text
按风险等级筛选
按语言组合筛选
按是否超过阈值筛选
按证据类型筛选
按相似度区间筛选
```

### 14.5 排序

默认按：

```text
RiskScore 降序
EvidenceStrength 降序
```

---

## 15. 代码对比与证据页

### 15.1 页面目标

这是系统最重要的前端页面，用于支撑答辩、软著截图、论文案例和人工复核。

### 15.2 页面布局

```text
顶部：代码对基本信息 + 风险等级 + 动态阈值
左侧：代码 A Monaco Editor
右侧：代码 B Monaco Editor
下方：多维相似度图表 + 证据列表
侧栏：变量映射、函数匹配、复核建议
```

### 15.3 代码展示

使用 Monaco Editor，要求：

```text
语法高亮
行号
只读模式
相似片段高亮
点击证据跳转代码行
支持折叠长代码
```

### 15.4 证据列表

证据类型：

```text
TOKEN_FRAGMENT
AST_SUBTREE
CONTROL_FLOW
DATA_DEPENDENCY
OPERATION_SEQUENCE
IDENTIFIER_MAPPING
RARE_FRAGMENT
BUG_PATTERN
IO_PATTERN
CROSS_LANGUAGE_IR
```

证据字段：

```text
证据类型
代码 A 行号范围
代码 B 行号范围
相似度
证据强度
是否稀有
是否模板片段
说明文本
```

### 15.5 多维相似度图表

展示：

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
CrossLanguageIRSimilarity
```

推荐图表：

```text
雷达图
条形图
指标详情表
```

### 15.6 人工复核建议

系统生成建议，例如：

```text
该代码对综合风险高于动态阈值 7.3%，且存在稳定变量映射和相同边界处理逻辑，建议人工复核。
```

### 15.7 验收标准

```text
能左右展示代码
能高亮相似片段
点击证据能定位代码行
能展示多维相似度
能展示动态阈值解释
能展示人工复核建议
```

---

## 16. 实验结果看板

### 16.1 页面目标

用于支撑期刊实验和答辩展示，不是普通业务统计页。

### 16.2 实验类型

```text
固定阈值 vs 动态阈值
规范化前 vs 规范化后
Token / AST / IR / PICAS 对比
JPlag / Dolos / MOSS / PICAS 对比
伪装等级 L0-L8 检测效果
消融实验
```

### 16.3 图表

```text
Precision/Recall/F1 柱状图
FPR/FNR 对比图
不同伪装等级召回率折线图
消融实验贡献柱状图
检测耗时箱线图或柱状图
```

### 16.4 结果表

字段：

```text
实验名称
方法名称
数据集
Precision
Recall
F1
FPR
FNR
Accuracy
平均耗时
运行时间
```

---

## 17. 报告导出页

### 17.1 页面目标

导出检测报告、题目画像报告和实验报告。

### 17.2 报告类型

```text
任务检测报告
代码对证据报告
题目画像报告
实验结果报告
软著截图报告
```

### 17.3 导出格式

```text
PDF
HTML
Markdown
CSV
JSON
```

---

## 18. 系统配置页

### 18.1 页面目标

展示和调整部分安全的检测参数。首期只允许管理员访问。

### 18.2 配置项

```text
BaseThreshold
MinThreshold
MaxThreshold
是否启用动态阈值
是否启用跨语言 IR
是否启用证据保存
最大上传文件大小
最大任务代码数量
算法服务地址
```

### 18.3 注意事项

核心算法权重不建议在普通 UI 中随意开放修改。实验权重应通过实验配置文件管理。

---

## 19. 组件设计

### 19.1 ProblemScoreCard

用途：展示单个题目画像分数。

Props：

```text
scoreName
scoreValue
level
explanation
impactDirection
```

### 19.2 dynamicThresholdPanel

用途：展示动态阈值组成。

Props：

```text
baseThreshold
adjustments[]
finalThreshold
explanation
```

### 19.3 SimilarityRadarChart

用途：展示多维相似度。

Props：

```text
metrics[]
```

### 19.4 CodeDiffViewer

用途：左右代码对比与高亮。

Props：

```text
codeA
codeB
languageA
languageB
highlightRangesA
highlightRangesB
```

### 19.5 EvidenceList

用途：展示证据列表。

Props：

```text
evidenceItems[]
selectedEvidenceId
```

### 19.6 IdentifierMappingTable

用途：展示变量/函数映射关系。

Props：

```text
mappings[]
```

### 19.7 RiskBadge

用途：风险等级标签。

Props：

```text
riskLevel
riskScore
threshold
```

---

## 20. 前端类型定义建议

### 20.1 riskLevel

```ts
export type riskLevel = 'LOW' | 'MEDIUM' | 'ELEVATED' | 'HIGH'
```

### 20.2 SimilarityMetric

```ts
export interface SimilarityMetric {
  name: string
  value: number
  weight?: number
  description?: string
}
```

### 20.3 EvidenceItem

```ts
export interface EvidenceItem {
  id: number
  evidenceType: string
  codeAStartLine: number
  codeAEndLine: number
  codeBStartLine: number
  codeBEndLine: number
  similarityScore: number
  evidenceStrength: number
  description: string
  isRare?: boolean
  isTemplate?: boolean
}
```

### 20.4 ProblemProfile

```ts
export interface ProblemProfile {
  difficultyScore: number
  solutionSpaceScore: number
  templateRiskScore: number
  naturalSimilarityRisk: number
  dynamicThreshold: number
  explanation: string
}
```

---

## 21. 视觉风格

### 21.1 总体风格

```text
研究型
清晰
专业
信息密度适中
不花哨
适合截图进论文/软著/答辩 PPT
```

### 21.2 颜色语义

```text
低风险：绿色
中风险：蓝色或黄色
较高风险：橙色
高风险：红色
不可用/失败：灰色
```

### 21.3 图表原则

1. 不使用过度复杂的 3D 图；
2. 图表标题必须说明含义；
3. 坐标轴和图例必须清晰；
4. 所有百分比统一显示 0-100%；
5. 分数内部可用 0-1，但 UI 显示为百分比。

---

## 22. API 接入原则

### 22.1 Axios 封装

所有请求通过 `src/utils/request.ts` 统一封装。

必须支持：

```text
baseURL
Token 注入
错误处理
超时处理
401 自动跳转登录
文件上传进度
```

### 22.2 错误提示

后端返回错误时前端显示：

```text
简短错误标题
详细错误原因
可操作建议
```

例如：

```text
代码解析失败：该文件存在语法错误，系统已降级使用 token 检测。
```

---

## 23. 前端验收清单

```text
能登录并进入系统
能创建题目
能上传代码
能创建检测任务
能查看任务状态
能查看题目复杂度画像
能查看结果总览
能进入代码对比页
能高亮相似片段
能展示变量映射
能展示多维相似度图表
能展示动态阈值解释
能展示实验结果图表
能导出至少一种报告格式
刷新页面不丢失登录状态
接口异常时有提示
```

---

## 24. Codex 前端开发约束

1. 不允许硬编码大量假数据到业务页面；
2. Demo 数据必须放在 `mock/` 或开发模式下；
3. 所有接口类型必须写 TypeScript interface；
4. 风险等级颜色必须统一由 `risk.ts` 管理；
5. 图表配置必须封装，避免每页重复；
6. Monaco Editor 必须只读展示，不允许误编辑原始代码；
7. 页面必须适合 1920x1080 答辩投影；
8. 不做移动端优先，首期以桌面端为主；
9. 所有核心页面必须支持截图展示；
10. 前端展示文字必须避免直接写“抄袭”，统一使用“相似风险”。

---

## 25. 最小可交付前端范围

如果时间有限，最小交付范围为：

```text
登录页
首页仪表盘
题目管理
代码上传
任务创建
结果总览
代码对比与证据页
题目复杂度分析页
报告导出
```

期刊增强必须补充：

```text
实验结果看板
消融实验图表
基线对比图表
```


## 字段和能力展示补充约束

外部 API 和前端状态字段必须使用 camelCase，例如 `weightedSimilarityScore`、`dynamicThreshold`、`riskMargin`、`calibratedRiskScore`、`exceedThreshold`、`marginScale`。C 语言必须显示为实验性支持，`PICAS_CROSSLANG` 必须显示为实验性能力，不得宣传为完整跨语言语义等价检测。
