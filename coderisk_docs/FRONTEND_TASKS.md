# FRONTEND_TASKS.md

> 本文件为 Codex 前端开发任务清单。每个任务均包含目标、输入、输出、实现要求、禁止事项和验收标准。开发时应按任务编号推进，完成后更新任务状态。

---

## 0. 前端开发总规则

### 0.1 技术栈

```text
Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router + Axios + ECharts + Monaco Editor
```

### 0.2 统一要求

1. 所有页面必须使用 TypeScript；
2. 所有 API 请求必须通过统一 request 封装；
3. 所有核心类型必须写在 `src/types/`；
4. 所有图表组件必须封装；
5. 所有风险等级颜色必须统一；
6. 所有页面必须包含 loading、empty、error 状态；
7. 页面文案统一使用“相似风险”，不要使用“抄袭判定”；
8. 不允许在正式页面中散落硬编码假数据；
9. Mock 数据必须集中管理；
10. 首期以桌面端 1920x1080 展示为主。

---

## TASK-FE-001：初始化 Vue 3 前端项目

### 目标

搭建前端基础工程。

### 实现要求

```text
使用 Vite 创建 Vue 3 + TypeScript 项目
安装 Element Plus
安装 Vue Router
安装 Pinia
安装 Axios
安装 ECharts
安装 Monaco Editor
配置路径别名 @
配置基础 lint / format（可选）
```

### 输出

```text
frontend/package.json
frontend/src/main.ts
frontend/src/App.vue
frontend/src/router/index.ts
frontend/src/stores/
```

### 验收标准

```text
npm install 成功
npm run dev 成功
浏览器能打开首页
Element Plus 组件可正常显示
```

---

## TASK-FE-002：实现基础布局与路由

### 目标

实现系统主布局、侧边栏、顶部栏和路由结构。

### 页面

```text
/login
/dashboard
/questions
/questions/create
/questions/:questionId
/questions/:questionId/profile
/questions/:questionId/upload
/tasks
/tasks/create
/tasks/:taskId
/tasks/:taskId/results
/results/:resultId/evidence
/experiments
/experiments/:experimentId
/reports
/settings
```

### 实现要求

```text
MainLayout.vue
AuthLayout.vue
侧边栏菜单
顶部用户信息
算法服务状态占位
路由守卫
未登录跳转 /login
```

### 验收标准

```text
路由可跳转
刷新不丢路由
未登录访问业务页会跳转登录
侧边栏高亮当前页面
```

---

## TASK-FE-003：封装 API 请求与类型定义

### 目标

建立前后端接口调用基础。

### 实现要求

创建：

```text
src/utils/request.ts
src/api/auth.ts
src/api/question.ts
src/api/submission.ts
src/api/task.ts
src/api/result.ts
src/api/evidence.ts
src/api/experiment.ts
src/api/system.ts
```

创建类型：

```text
src/types/api.ts
src/types/question.ts
src/types/submission.ts
src/types/task.ts
src/types/result.ts
src/types/evidence.ts
src/types/experiment.ts
```

### 验收标准

```text
请求自动带 Token
401 自动跳转登录
错误统一提示
文件上传支持进度回调
类型无明显 any 滥用
```

---

## TASK-FE-004：实现登录页面

### 目标

完成基础登录流程。

### 实现要求

```text
账号输入
密码输入
登录按钮
演示账号提示
登录失败提示
Token 保存
登录成功跳转首页
```

### 验收标准

```text
空账号提示
空密码提示
登录成功进入 /dashboard
登录失败显示后端错误
刷新页面仍保持登录状态
```

---

## TASK-FE-005：实现首页仪表盘

### 目标

展示系统概览和最近任务。

### 实现内容

```text
统计卡片
最近任务表
风险等级分布图
语言分布图
系统健康状态
```

### API

```text
GET /api/dashboard/summary
GET /api/tasks/recent
GET /api/system/health
```

### 验收标准

```text
能显示题目数、提交数、任务数、高风险数量
能显示最近任务列表
能显示算法服务状态
图表加载正常
```

---

## TASK-FE-006：实现题目列表页

### 目标

完成题目管理入口。

### 实现内容

```text
题目表格
搜索框
标签筛选
新增题目按钮
查看详情
编辑入口
删除确认
```

### 表格字段

```text
题目标题
标签
提交数量
DifficultyScore
NaturalSimilarityRisk
创建时间
操作
```

### 验收标准

```text
能分页查询题目
能搜索题目
能进入题目详情
能显示题目画像摘要字段
```

---

## TASK-FE-007：实现题目创建与编辑页

### 目标

支持创建和编辑题目。

### 表单字段

```text
题目标题
题目描述
输入格式
输出格式
约束条件
样例输入
样例输出
题目标签
支持语言
参考答案
```

### 验收标准

```text
必填校验正常
能保存题目
保存成功跳转详情页
参考答案可粘贴或上传
```

---

## TASK-FE-008：实现题目详情页

### 目标

展示题目完整信息和操作入口。

### 实现内容

```text
题目信息卡片
题目描述展示
参考答案展示
题目画像摘要
提交列表
最近任务
上传代码按钮
查看画像按钮
创建任务按钮
```

### 验收标准

```text
能从题目详情进入上传代码
能从题目详情进入画像页面
能从题目详情创建任务
```

---

## TASK-FE-009：实现代码上传页

### 目标

支持批量上传代码。

### 实现内容

```text
拖拽上传
多文件上传
上传进度
语言识别结果
失败文件提示
上传成功列表
```

### 验收标准

```text
支持多文件上传
上传失败不影响其他文件
能展示文件名、大小、语言、状态
上传完成后题目详情能看到提交记录
```

---

## TASK-FE-010：实现检测任务创建页

### 目标

创建检测任务并选择检测模式。

### 实现内容

```text
选择题目
选择提交范围
选择语言范围
选择检测模式
启用动态阈值开关
启用置换不变规范化开关
启用跨语言 IR 开关
生成证据报告开关
```

### 检测模式

```text
BASIC
INVARIANT
PROBLEM_AWARE
CROSS_LANGUAGE
EXPERIMENT
```

### 验收标准

```text
至少选择两份代码才能提交
跨语言模式校验语言数量
创建成功跳转任务详情
```

---

## TASK-FE-011：实现任务详情与状态页

### 目标

展示任务运行状态和进度。

### 实现内容

```text
任务基本信息
状态标签
进度条
代码对总数
已完成数量
失败数量
任务日志
查看结果按钮
取消任务按钮
```

### 轮询要求

```text
任务未结束时每 2 秒刷新
任务结束后停止轮询
```

### 验收标准

```text
任务状态实时更新
任务成功后可进入结果页
任务失败显示错误原因
```

---

## TASK-FE-012：实现题目复杂度分析页

### 目标

展示项目第一创新点：题目感知与动态阈值。

### 实现内容

```text
DifficultyScore 卡片
SolutionSpaceScore 卡片
TemplateRiskScore 卡片
NaturalSimilarityRisk 卡片
dynamicThreshold 卡片
题目画像雷达图
阈值贡献条形图
历史提交相似度分布图
指标解释面板
```

### 验收标准

```text
能显示五个核心分数
能解释每个分数含义
能展示动态阈值组成
能说明为什么简单题阈值提高或复杂题阈值降低
```

---

## TASK-FE-013：实现检测结果总览页

### 目标

展示所有代码对的风险结果。

### 实现内容

```text
风险统计卡片
结果表格
风险等级筛选
语言组合筛选
是否超过阈值筛选
排序
查看证据按钮
导出结果按钮
```

### 表格字段

```text
代码 A
代码 B
语言组合
RiskScore
dynamicThreshold
ExceededThreshold
riskLevel
EvidenceCount
检测耗时
```

### 验收标准

```text
默认高风险排序
能筛选风险等级
能进入证据详情页
能导出结果表
```

---

## TASK-FE-014：封装代码对比组件 CodeDiffViewer

### 目标

实现左右代码展示和相似片段高亮。

### 技术要求

```text
使用 Monaco Editor
只读模式
双栏布局
行号显示
支持语言高亮
支持高亮 ranges
支持点击证据后滚动到指定行
```

### Props

```text
codeA
codeB
languageA
languageB
highlightRangesA
highlightRangesB
selectedEvidenceId
```

### 验收标准

```text
能显示两份代码
能根据证据高亮行
点击证据后能滚动定位
长代码不卡顿
```

---

## TASK-FE-015：实现证据列表组件 EvidenceList

### 目标

展示结构化证据并支持筛选。

### 实现内容

```text
证据类型标签
相似度
证据强度
代码行号范围
是否稀有
是否模板片段
说明文本
点击选择证据
```

### 筛选类型

```text
全部
AST
控制流
数据依赖
变量映射
稀有片段
跨语言 IR
错误模式
```

### 验收标准

```text
证据列表可筛选
点击证据能通知父组件
证据说明清晰
```

---

## TASK-FE-016：实现代码对比与证据页

### 目标

整合代码对比、证据列表、多维指标和复核建议。

### 页面内容

```text
风险摘要
动态阈值说明
左右代码对比
证据列表
多维相似度雷达图
变量映射表
人工复核建议
导出代码对报告按钮
```

### API

```text
GET /api/results/:resultId
GET /api/results/:resultId/code-pair
GET /api/results/:resultId/evidence
GET /api/results/:resultId/metrics
```

### 验收标准

```text
能展示完整代码对比
能高亮证据
能展示多维指标
能展示变量映射
能显示复核建议
```

---

## TASK-FE-017：实现图表组件

### 目标

封装项目核心图表。

### 组件

```text
ProblemRadarChart
ThresholdContributionChart
SimilarityRadarChart
RiskDistributionChart
ExperimentMetricBarChart
AttackLevelLineChart
AblationBarChart
```

### 验收标准

```text
每个图表可复用
无数据时显示 empty
图表尺寸自适应
图例和坐标清晰
```

---

## TASK-FE-018：实现实验列表与实验详情页

### 目标

支撑期刊实验结果展示。

### 实验列表

```text
实验名称
数据集
方法数量
状态
创建时间
操作
```

### 实验详情

```text
实验配置
指标总览
方法对比表
Precision/Recall/F1 图表
FPR/FNR 图表
伪装等级效果图
消融实验图
失败案例列表
```

### 验收标准

```text
能查看实验指标
能比较不同方法
能展示消融结果
能导出图表或结果表
```

---

## TASK-FE-019：实现报告导出页

### 目标

支持检测报告和实验报告导出。

### 实现内容

```text
选择报告类型
选择导出格式
选择是否匿名化
选择是否包含代码片段
选择是否包含图表
生成报告按钮
下载链接
```

### 验收标准

```text
至少支持 Markdown 或 HTML 导出
能导出任务检测报告
能导出代码对证据报告
能导出实验结果报告
```

---

## TASK-FE-020：实现系统配置页

### 目标

展示系统配置和算法服务状态。

### 实现内容

```text
后端服务状态
分析服务状态
基础阈值配置
上传限制配置
算法开关展示
测试连接按钮
```

### 验收标准

```text
能查看服务状态
能测试分析服务连接
管理员能修改安全配置
普通用户不能访问
```

---

## TASK-FE-021：实现风险等级工具函数

### 目标

统一风险等级显示逻辑。

### 文件

```text
src/utils/risk.ts
```

### 函数

```text
getriskLevelText(level)
getriskLevelColor(level)
formatScore(score)
formatThreshold(threshold)
getExceededText(riskScore, threshold)
```

### 验收标准

```text
所有页面风险颜色一致
所有分数格式一致
不会出现 0-1 和 0-100 混乱
```

---

## TASK-FE-022：实现统一空状态和错误状态

### 目标

提高系统稳定观感。

### 组件

```text
EmptyState.vue
ErrorState.vue
LoadingPanel.vue
```

### 验收标准

```text
列表无数据时不白屏
接口错误时有错误说明
加载中显示骨架或 loading
```

---

## TASK-FE-023：实现 Mock 数据层

### 目标

在后端未完全完成时支持前端演示。

### 实现要求

```text
mock/dashboard.ts
mock/questions.ts
mock/tasks.ts
mock/results.ts
mock/evidence.ts
mock/experiments.ts
```

### 注意事项

Mock 数据必须可一键关闭，不能和正式接口混在一起。

### 验收标准

```text
无后端时前端能展示主要页面
连接后端时使用真实接口
```

---

## TASK-FE-024：实现导出与截图友好优化

### 目标

方便软著、答辩和论文截图。

### 实现内容

```text
核心页面排版适配 1920x1080
隐藏调试信息
报告页支持打印样式
图表支持导出 PNG
表格支持导出 CSV
```

### 验收标准

```text
题目画像页截图清晰
证据页截图清晰
实验看板截图清晰
导出图表无明显截断
```

---

## TASK-FE-025：前端最终联调与验收

### 目标

完成完整流程验证。

### 验收流程

```text
登录
创建题目
上传代码
创建检测任务
查看任务状态
查看题目画像
查看结果总览
查看证据详情
导出报告
查看实验看板
导出实验结果
```

### 验收标准

```text
完整流程无阻断
页面无明显白屏
核心接口错误有提示
所有核心图表正常显示
所有核心页面可截图
```

---

## 26. 开发优先级

### P0 必做

```text
TASK-FE-001 到 TASK-FE-016
```

### P1 期刊增强

```text
TASK-FE-017 到 TASK-FE-019
```

### P2 体验与软著增强

```text
TASK-FE-020 到 TASK-FE-024
```

### P3 最终联调

```text
TASK-FE-025
```

---

## 27. 完成后需要更新的文件

每完成一批前端任务，Codex 应更新：

```text
README.md
FRONTEND_SPEC.md（如实际页面变化）
API_SPEC.md（如接口变化）
TEST_PLAN.md（补充前端测试结果）
```

---

## 28. 前端完成定义

前端不能只算“页面能打开”，必须满足：

```text
1. 业务流程能走通；
2. 算法创新点能展示；
3. 证据链能复核；
4. 实验结果能可视化；
5. 报告能导出；
6. 软著截图可用；
7. 答辩演示稳定。
```


## 字段和能力展示补充约束

外部 API 和前端状态字段必须使用 camelCase，例如 `weightedSimilarityScore`、`dynamicThreshold`、`riskMargin`、`calibratedRiskScore`、`exceedThreshold`、`marginScale`。C 语言必须显示为实验性支持，`PICAS_CROSSLANG` 必须显示为实验性能力，不得宣传为完整跨语言语义等价检测。
