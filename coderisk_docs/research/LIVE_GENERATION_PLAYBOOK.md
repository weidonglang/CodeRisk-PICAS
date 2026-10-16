# V4：真实采集、许可、双审与教师试点操作手册

**本程序没有live生成接口。** 不提供账号密码，不粘贴API key，不由Codex登录、调用收费API或向第三方发送题目/代码。本轮真实模型调用、学生数据及教师受试者均0。

## 1. 先由你和导师确定事实

确认拟题仍以规范化/题目感知为主，RQ3仅探索。向导师/课程负责人说明用途、数据项、保管期限、访问者和退出方式，取得适用学校程序/同意。题面、模板、学生代码、过程记录、模型提交权限和公开再分发权限分别确认，不能一个MIT文件覆盖全部数据。

授权说明可写：“拟用指定题目与匿名程序研究相似信号和复核限制，不作学生处分/AI归因；原文仅本地受限使用，拟公开范围为匿名汇总，模型提交范围为另经批准的题面/模板。”由真正有权限的人确认，不将这段建议当现有许可。

## 2. 规划小而可核查的试点

4—8题分简单IO、模板/短题、循环数组、较开放题。选择2—3个你实际获权使用的模型，先核准导出/数据使用规则，不推荐或假定某模型价格/可用性。2套prompt族先冻结，每配置3个干净独立会话；6×3×2×3=108尝试是计划，不是已有数据。

每次另开无先前源码的独立会话，不共享先前答案；记录是否存在共同公开模板/上游。来自同一父源码的改写应单独进入已知派生组，不能作为负例。留失败、截断、重试和revision_count，禁止挑只通过的结果。不同模型可能有共同训练/库影响，“独立”只限定已核查的会话流程，不承诺无任何共享上游。

## 3. 建本地目录与元数据

新建 `output/ai-convergence-real-NEW/source/`，使用 `questions/`、`templates/`、`prompts/`、`code/`、`raw/`、`sessions/`、`authorization/`、`functional/`、`reviews/`。真实原文不进公开evidence目录。复制获授权文件，不修改原始字节。

Gitignore不是访问控制或加密。请和学校管理员通过文件夹“属性→安全”限制到获准研究/复核账户，身份映射另行受限保存；使用学校批准的存储和保管期限，不与未获权账户分享。工具限制真实raw输出路径，但不冒称已设置Windows ACL。

填写全量 `corpus.json`，按 [schema](../../coderisk/experiment/ai_convergence/schema/corpus.schema.json)，不要把mock文件改个synthetic=false就叫真实。样本/题目/session ID用匿名稳定ID，真实姓名映射单独受限保存。许可ref只能引用根目录内的真实文件；私有用LOCAL_RESTRICTED，redistribution_allowed如实填写。

题目填写problem/family、language、代理难度/解法空间（不懂写UNKNOWN）、模板、hidden_test_policy、课程政策、保密等级、split。session记录provider/model/snapshot（界面未显示精确版则明确UNKNOWN）、access_mode、UTC时间、完整prompt及hash、参数（不支持或不可见用null）、修订、人改和上游；不要猜供应商参数语义。artifact记录来源/辅助方式、真实parent、原始输出、语言/代码hash、语法/功能状态、许可/隐私。pair分开写关系、依据、两位真人、审核hash/date/冲突。provenance先UNREGISTERED，不提前填FROZEN。

每份capture.json至少含generation_session_id、problem_id、model_id、prompt_sha256、raw_output_sha256，来源于实际导出。AI回答原文和提取的代码分别留，原始输出hash对应raw文件，不是手动伪造模型响应。

```powershell
# 文件内容不得改变后仍沿用旧hash；不需要执行代码。
(Get-FileHash -LiteralPath './output/ai-convergence-real-NEW/source/code/S-001.py' -Algorithm SHA256).Hash.ToLowerInvariant()
[DateTime]::UtcNow.ToString('o') # 实际记录操作时间；不能代替过去生成时间
# 提示/题面/raw同样Get-FileHash，64位小写，不加sha256:前缀。
```

## 4. 功能和来源审核分开

默认syntax/functional NOT_RUN。确需验证代码，另取得执行许可，使用隔离、资源限制、无网络环境，由你记录测试套件hash、命令、退出码和原始日志。本轮工具只解析文本，不执行导入代码；编译/功能正确不能证明来源。

真人关系审核至少两位不同匿名ID，独立填写HUMAN类型、依据、UTC时间及对应字节hash，先不看检测分数/对方标签。代码工作台不能单独证明独立性：审查过程记录另提供给有权限复核者，冲突留CONFLICT或UNCERTAIN，经真实仲裁再AGREED，不用两个AI评分替代。

新工具 `prepare_review.py` 复用旧HTML工作台/双审格式。旧合并入口 `prepare_annotation_workbench.py --help` 有merge模式；先合并实际导出，核对source bytes再人工转填pair关系，不自动填来源真值。单独复制功能失败/未知关系的排除理由，不删除这些样例。

## 5. 分组、冻结和比较

按problem/source family/session/parent/hash连通隔离validation/test，碰到跨split重复输出，把整个组件重新规划到一边并版本化，不只删不利pair。共同prompt族/model snapshot跨split是敏感性限制，不能称完全model-disjoint。先读 [公平协议](AI_CONVERGENCE_PROTOCOL.md)。

冻结题目/会话计划、数据文件hash、config（包括JPlag参数）、阈值候选、split及时间登记ref，经导师确认再写FROZEN/config_sha256/split_preregistered。尚未评分前保留冻结记录；test不用于挑prompt、样本或调参数。正式命令不满足条件会exit2，不加“开发豁免”冒充正式结果。

## 6. 费用和授权控制

[预算模板](../../coderisk/experiment/ai_convergence/budget.template.csv)价格留空，由你从当时合同/官方计费记录填币种、单位价格、日期、访问方式、输出/重试上限。108次初始尝试若最多2次revision，调用上限可为324次；这不是成本估算。界面订阅、批处理、按token收费不直接混算；未知价格显示N/A，先获批准再真实调用。程序没有支付、live SDK或自动上传。

## 7. 教师走查不冒充效率研究

先有知情同意和预定义任务/评分rubric：识别共同模板、定位匹配、识别来源不足、是否过度确信。合理对照JPlag+原文、PICAS旧报告、新上下文；承认JPlag已有匹配/可视化。预排counterbalanced顺序/分配，避免重复看同case的学习效应；与来源审核分开，评测者先不知标签。

`usability_record_template.csv`只留空记录，工具不模拟人类用时/答案。小规模走查仅发现可用性问题，不能据此声称更快/更准。若拟做效率检验，先定义样本/参与者、问题×参与者依赖、盲法和统计方案，再实际招募。没有参与者就NOT_RUN。

## 8. 公开前与常见错误

`export_public.py`只输出匿名聚合，真实数据默认抑制小cell，不含原文、prompt、session/reviewer IDs或私有路径；仍需你人工核准发表权限。schema失败看缺字段，不降低门禁；hash失败检查CRLF/原始bytes，保留旧版本；capture重复回查是否确实复制了同会话；泄漏重排整个组件；无参考/无标签/组数少接受N/A；FROZEN hash不符说明配置或数据变更，重新登记且不能再叫原test未见。
