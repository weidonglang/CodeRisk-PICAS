# V1—V2 离线跨模型协议 v1

这是研究扩展，不是新生产评分。RQ1/RQ2仍是主线；跨模型趋同为可选RQ3。当前新数据只有自编模拟，正式资格0。

## 三种对象不能合并

样本 `origin_type/ai_assistance_type` 记录生成过程；pair 的 `claimed_relation/resolved_relation` 记录关系证据；question 的 `course_ai_policy` 记录课程规则。分数不填写任何这些字段。六类关系由协议枚举，不包含违规标签。不同供应商、同题不同提交、相同代码和功能正确都不能单独证明独立。

可执行模型在 `ai_convergence/protocol.py`；六份 JSON Schema 由它生成，校验以模型和文件关联检查为准，schema文字本身不检查文件或哈希。输入包含 questions、sessions、artifacts、pair_relations、provenance。全部必填字段/nullable约束见 [schema](../../coderisk/experiment/ai_convergence/schema/corpus.schema.json)。

## 文件与事实链

题面、模板、提示、代码、原始输出、会话capture、许可/功能/标签证据都使用输入根下的相对文件引用。拒绝绝对/UNC/反斜杠/URL/..越界和解析后的symlink越界；hash是实际字节 SHA-256。评分使用已有loader的文本hash，二者分别记录，不将CRLF变化悄悄当来源相同。导入复制原字节；schema禁止未知密钥字段，错误不回显其值。

每个capture至少记录generation_session_id、problem_id、model_id、prompt_sha256、raw_output_sha256。独立session ID不够：重复capture被拒绝，声明与capture须一致。失败/截断记录attempt_status和证据ref，可没有最终artifact，仍统计分母。工具不认证供应商、独立性、许可或真人身份。

## 来源关系与正式资格

没有关系记录/完整真人双审时为UNCERTAIN。AI独立关系至少需要分离session/family、无父版本、真实过程证据；model key=(provider,model_id,snapshot)，不同snapshot不叫同模型同配置。共享upstream按实际内容hash核对，只有已登记并审过的共同模板可被明确限定；不是以不同模型默认负例。

已知派生须有实际父子记录和匹配的辅助方式。功能失败不更改来源事实；当前**主正式评测**仍复用旧协议功能PASSED门禁，不满足者保留在描述性/失败分层，其关系和排除理由分开保存。不能因语法/功能失败删除难例，也不能假称功能测试已经执行。

原 `RESEARCH_V4_PAIRS_JSON` 是唯一评分输入桥梁；`build_pairs.py` 生成新的dataset.json/pairs.json，不动旧seed。标签只从关系证据映射，非正式run再统一屏蔽二元标签，所以模拟F1/FPR/PR-AUC为null，不显示“正式模型成绩”。

## 冻结、连通隔离及公平对照

样本按problem、problem family、题面hash、source family、parent、session、字节/文本hash连通分组；组件不可跨validation/test。相同输出的不同会话不去重删除，但作为相关观测；重复prompt family/model snapshot跨split只报告敏感性，不能宣称model-disjoint。

配置冻结六方法：Raw、基础AST、Canonical、NoCanon固定、PICAS固定、原规则动态。NoCanon=.5raw+.5AST，Full读生产结果。阈值网格/方法/seed/cluster数量/JPlag版本与min-tokens同时冻结；每方法只在共同支持validation选自己的阈值，再比较同一test cohort。原规则与额外offset不能混同，本配置不搜索offset。生产公式、风险等级、V4权重不动。

本地JPlag6.2.0是真实静态基线，但本轮输入synthetic。新native CSV必须对应当前pair/source/dataset hash及冻结参数；缺失不补0。同源码不同会话使用不同native submission ID。无模板扣除版本与PICAS原score同样保留模板；不能据此假称已比较JPlag模板排除方案，后者需要单独预注册公平组。

分布按题目、模型组合、prompt family、长度、模板、功能、语法分层，报告available/requested和线性分位数。C全序列和ngram集合等同性分开，失败缺失=null，**不从相等推断轨道或来源关系**；轨道性质另复用手标gold runner。

固定FPR工作点/非插值AP/共同与available覆盖复用旧消融。`FPR_independent_AI=FP/(FP+TN)`仅对可信AI独立关系且分母>0定义，描述风险候选率，不是AI使用/违规错误率。无标签或组数不足为NOT_ESTIMABLE。test的connected-component宏平均配对bootstrap使用固定seed；每组件一个均值，不对n(n−1)/2代码对bootstrap，不把区间解释为因果或代表总体。

正式入口额外检查注册hash、两类关系及真人/功能等既有门禁。不合格输出FORMAL_BLOCKED/exit2；目前3道mock题、13artifact、12mock会话、22对、test组件2，正式资格0，不是新保留集。

操作见 [真实采集](LIVE_GENERATION_PLAYBOOK.md)、[复现](REPRODUCE_AI_CONVERGENCE.md)，当前结论见 [Go/No-Go](PICAS_GO_NO_GO_DECISION.md)。
