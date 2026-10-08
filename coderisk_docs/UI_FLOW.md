# UI_FLOW.md

## 2026-10-09 已实现增量

题目创建（可选共同模板与来源）→ 上传代码（可选语言版本）→ 创建任务 → 结果详情（版本、模板与依据不足提示）→ 导出报告。新增字段均有后端校验，复核上下文随结果保存和导出；提示不能替代来源核验或人工关系标注。具体范围见 [实现边界](proposal/VERSION_AND_NATURAL_SIMILARITY.md)。

> 本文件定义 CodeRisk / PICAS 前端的完整用户流程、页面跳转、状态变化、异常分支和演示路线。Codex 开发前端时应按本文件保证流程闭环，不应只做孤立页面。

---

## 1. 用户流程总览

CodeRisk / PICAS 的完整用户路径分为三条主线：

```text
A. 标准查重流程：题目 -> 上传代码 -> 创建任务 -> 查看结果 -> 查看证据 -> 导出报告
B. 题目感知流程：题目画像 -> 动态阈值解释 -> 风险校准结果
C. 期刊实验流程：导入实验 -> 运行基线 -> 查看指标 -> 导出实验结果
```

前端所有页面必须服务这三条主线。

---

## 2. 路由规划

推荐路由：

```text
/login
/dashboard
/questions
/questions/create
/questions/:questionId
/questions/:questionId/profile
/questions/:questionId/submissions
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

---

## 3. 标准检测流程

### 3.1 流程图

```text
登录
  -> 首页
  -> 题目管理
  -> 新增题目
  -> 上传代码
  -> 创建检测任务
  -> 查看任务状态
  -> 查看结果总览
  -> 查看证据详情
  -> 导出报告
```

### 3.2 Step 1：登录

页面：

```text
/login
```

用户操作：

```text
输入账号
输入密码
点击登录
```

系统响应：

```text
登录成功：跳转 /dashboard
登录失败：显示错误信息
```

异常分支：

```text
账号为空：提示请输入账号
密码为空：提示请输入密码
接口超时：提示服务暂不可用
```

---

## 4. 首页流程

页面：

```text
/dashboard
```

### 4.1 页面进入后加载

调用：

```text
GET /api/dashboard/summary
GET /api/tasks/recent
GET /api/system/health
```

### 4.2 用户可执行操作

```text
点击“新建题目” -> /questions/create
点击“创建检测任务” -> /tasks/create
点击最近任务 -> /tasks/:taskId
点击高风险代码对 -> /tasks/:taskId/results
```

### 4.3 展示重点

首页必须让用户一眼看到：

```text
这是代码相似风险系统
不是普通学生作业管理系统
核心结果包括风险等级和证据分析
```

---

## 5. 题目创建流程

页面：

```text
/questions/create
```

### 5.1 表单字段

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

### 5.2 用户操作

```text
填写题目信息
上传参考答案或粘贴参考答案
点击保存
```

### 5.3 系统响应

```text
保存成功 -> 跳转 /questions/:questionId
保存失败 -> 显示字段错误
```

### 5.4 自动分析触发

题目保存后可触发题目画像初步分析：

```text
POST /api/questions/:questionId/profile/analyze
```

若参考答案为空，则仅进行文本级题目画像分析。

---

## 6. 题目详情流程

页面：

```text
/questions/:questionId
```

### 6.1 页面区域

```text
题目基本信息
题目描述
参考答案
题目画像摘要
提交列表
最近检测任务
操作按钮
```

### 6.2 操作按钮

```text
上传代码
查看题目画像
创建检测任务
编辑题目
导出题目资料
```

### 6.3 跳转关系

```text
上传代码 -> /questions/:questionId/upload
查看题目画像 -> /questions/:questionId/profile
创建检测任务 -> /tasks/create?questionId=xxx
```

---

## 7. 代码上传流程

页面：

```text
/questions/:questionId/upload
```

### 7.1 用户操作

```text
拖拽或选择代码文件
确认文件列表
填写学生编号或提交者信息
点击上传
```

### 7.2 系统响应

```text
显示上传进度
显示语言识别结果
显示成功/失败状态
上传完成后可返回题目详情
```

### 7.3 状态说明

```text
WAITING：等待上传
UPLOADING：上传中
SUCCESS：上传成功
FAILED：上传失败
SKIPPED：跳过
```

### 7.4 异常分支

```text
文件类型不支持 -> 标记失败，不影响其他文件
文件过大 -> 拒绝上传
网络失败 -> 支持重试
语言识别失败 -> 用户手动选择语言
```

---

## 8. 检测任务创建流程

页面：

```text
/tasks/create
```

### 8.1 进入方式

```text
从题目详情进入：自动带 questionId
从任务列表进入：需要手动选择题目
```

### 8.2 用户操作

```text
选择题目
选择提交范围
选择检测模式
确认参数
点击创建任务
```

### 8.3 检测模式选择逻辑

```text
BASIC_TOKEN：适合 Token 基础功能验证
TOKEN_AST：适合 Token + AST 基础检测
PICAS_INVARIANT：适合变量名、函数名、参数名替换检测
PICAS_STANDARD：适合正式检测和论文主实验
PICAS_CROSSLANG：实验性跨语言 IR 检测，不代表完整语义等价
PICAS_EXPERIMENTAL：适合论文实验和消融批量运行
```

### 8.4 提交前校验

```text
题目不能为空
至少选择两份代码
如果选择 CROSS_LANGUAGE，必须存在至少两种语言
如果选择 EXPERIMENT，必须绑定实验配置
```

### 8.5 创建成功

```text
POST /api/tasks
成功后跳转 /tasks/:taskId
```

---

## 9. 任务状态流程

页面：

```text
/tasks/:taskId
```

### 9.1 状态流转图

```text
CREATED
  -> QUEUED
  -> RUNNING
  -> SUCCESS
```

异常：

```text
RUNNING -> PARTIAL_SUCCESS
RUNNING -> FAILED
QUEUED -> CANCELLED
```

### 9.2 页面刷新

首期采用轮询：

```text
任务未结束：每 2 秒调用 GET /api/tasks/:taskId
任务结束：停止轮询
```

### 9.3 用户操作

```text
查看任务日志
取消任务
查看结果
重新运行
导出任务配置
```

### 9.4 任务完成后跳转

```text
点击“查看结果” -> /tasks/:taskId/results
```

---

## 10. 题目复杂度分析流程

页面：

```text
/questions/:questionId/profile
```

### 10.1 页面进入后加载

调用：

```text
GET /api/questions/:questionId/profile
```

如果未分析：

```text
显示“开始分析”按钮
```

### 10.2 用户操作

```text
点击重新分析
查看各指标解释
查看动态阈值贡献
查看历史提交分布
导出题目画像
```

### 10.3 指标解释流程

用户点击某个指标，右侧显示：

```text
指标定义
计算依据
当前分数
风险等级
对动态阈值的影响
```

### 10.4 动态阈值展示流程

显示：

```text
BaseThreshold
自然相似调整
模板风险调整
题目难度调整
解法空间调整
历史分布调整
FinaldynamicThreshold
```

### 10.5 跳转关系

```text
返回题目详情 -> /questions/:questionId
创建检测任务 -> /tasks/create?questionId=xxx
查看结果 -> /tasks/:taskId/results
```

---

## 11. 结果总览流程

页面：

```text
/tasks/:taskId/results
```

### 11.1 页面进入后加载

调用：

```text
GET /api/tasks/:taskId/results/summary
GET /api/tasks/:taskId/results?page=1&pageSize=20
```

### 11.2 用户操作

```text
按风险等级筛选
按语言组合筛选
按超过阈值筛选
按相似度排序
搜索文件名或学生编号
点击查看证据
导出结果表
```

### 11.3 高风险优先逻辑

默认显示：

```text
高风险在前
超过动态阈值在前
证据强度高在前
```

### 11.4 跳转关系

```text
查看证据 -> /results/:resultId/evidence
查看题目画像 -> /questions/:questionId/profile
导出报告 -> /reports?taskId=xxx
```

---

## 12. 代码对比与证据流程

页面：

```text
/results/:resultId/evidence
```

### 12.1 页面进入后加载

调用：

```text
GET /api/results/:resultId
GET /api/results/:resultId/code-pair
GET /api/results/:resultId/evidence
GET /api/results/:resultId/metrics
```

### 12.2 默认布局

```text
上方：风险摘要
中间：左右代码对比
右侧：证据列表
下方：指标图表与复核建议
```

### 12.3 用户点击证据

流程：

```text
点击证据项
  -> 设置 selectedEvidenceId
  -> Monaco Editor 高亮对应行
  -> 滚动到代码位置
  -> 展示证据详情
```

### 12.4 用户切换证据类型

筛选：

```text
全部证据
AST 证据
控制流证据
数据依赖证据
变量映射证据
稀有片段证据
跨语言 IR 证据
```

### 12.5 人工复核流程

用户可选择：

```text
标记为已复核
添加复核备注
导出该代码对报告
返回结果总览
```

首期可只做前端展示，不做复杂审核流。

---

## 13. 实验评测流程

页面：

```text
/experiments
/experiments/:experimentId
```

### 13.1 实验列表页

展示：

```text
实验名称
数据集
对比方法
状态
创建时间
完成时间
操作
```

用户操作：

```text
新建实验
查看实验
导出结果
```

### 13.2 新建实验流程

```text
选择实验类型
选择数据集
选择基线方法
选择伪装等级
选择评价指标
点击运行
```

### 13.3 实验详情页

展示：

```text
实验配置
指标总览
方法对比表
图表
失败案例
消融结果
导出按钮
```

### 13.4 实验状态

```text
CREATED
RUNNING
SUCCESS
FAILED
```

### 13.5 论文图表导出

用户可导出：

```text
PNG 图表
CSV 指标表
Markdown 实验摘要
JSON 原始结果
```

---

## 14. 报告导出流程

页面：

```text
/reports
```

### 14.1 进入方式

```text
从任务结果页进入
从证据详情页进入
从实验详情页进入
```

### 14.2 用户选择

```text
报告类型
报告格式
是否包含代码片段
是否包含题目画像
是否包含实验指标
是否匿名化学生信息
```

### 14.3 生成流程

```text
点击生成
  -> 调用报告接口
  -> 显示生成中
  -> 生成成功后显示下载链接
```

### 14.4 异常分支

```text
生成失败 -> 显示错误原因
文件过大 -> 提示改用 HTML/Markdown
权限不足 -> 提示无权导出
```

---

## 15. 系统配置流程

页面：

```text
/settings
```

### 15.1 配置类别

```text
系统基础配置
算法服务配置
上传限制配置
阈值范围配置
实验配置
```

### 15.2 用户操作

```text
查看配置
修改允许修改的配置
保存配置
恢复默认值
测试算法服务连接
```

### 15.3 安全限制

普通用户不可访问系统配置页。管理员修改配置必须显示确认提示。

---

## 16. 异常流程总览

### 16.1 后端服务不可用

前端显示：

```text
后端服务暂不可用，请检查服务状态或稍后重试。
```

### 16.2 分析服务不可用

前端显示：

```text
算法分析服务暂不可用，已创建的任务不会丢失。
```

### 16.3 任务失败

显示：

```text
失败阶段
错误原因
可重试操作
日志摘要
```

### 16.4 解析失败

显示：

```text
部分代码解析失败，系统已降级使用基础 token 检测。
```

### 16.5 无权限

显示：

```text
当前账号无权访问该资源。
```

---

## 17. 答辩演示流程

### 17.1 推荐演示脚本

```text
1. 打开首页，展示系统定位和统计数据
2. 打开题目详情，说明题目上下文
3. 打开题目复杂度分析页，展示动态阈值来源
4. 上传多份代码，说明支持多语言
5. 创建题目感知检测任务
6. 查看结果总览，展示风险矩阵
7. 打开高风险代码对，展示证据链
8. 打开实验看板，展示本文方法优于基线
9. 导出检测报告
```

### 17.2 必须强调的话术

```text
系统不是直接判定抄袭，而是输出相似风险和证据，辅助人工复核。
```

```text
系统根据题目复杂度和自然相似风险动态调整阈值，避免简单题误报。
```

```text
系统通过置换不变结构表示增强对改名伪装的识别能力。
```

---

## 18. 软著截图流程

推荐截图顺序：

```text
1. 登录页
2. 首页仪表盘
3. 题目管理页
4. 题目详情页
5. 代码上传页
6. 检测任务创建页
7. 任务状态页
8. 题目复杂度分析页
9. 结果总览页
10. 代码对比与证据页
11. 实验看板页
12. 报告导出页
```

每张截图应避免出现真实学生隐私信息。

---

## 19. 前端流程验收

完整验收标准：

```text
从登录到报告导出可完整走通
从题目详情可进入题目画像
从结果总览可进入证据详情
从证据项可定位代码行
从实验列表可进入实验详情
接口失败时不白屏
刷新页面保持路由和登录状态
核心页面适合 1920x1080 展示
```

---

## 20. Codex 实现注意事项

1. 路由必须与本文件一致；
2. 页面跳转必须形成闭环；
3. 不允许只做静态页面；
4. 表格、图表、代码对比必须接真实接口或统一 mock 层；
5. 所有页面必须有 loading、empty、error 三种状态；
6. 代码对比页必须支持证据点击定位；
7. 任务状态页必须支持轮询；
8. 实验看板必须支持导出结果；
9. 报告导出必须至少支持 Markdown 或 HTML；
10. 所有文案统一使用“相似风险”，不用“抄袭判定”。
