# S3 不变性与判别力双维诊断

日期：2026-10-11。分层报告 **SYNTHETIC_DEVELOPMENT / PUBLIC_PILOT / FORMAL_BLOCKED**。不把三类结果混合为一张性能榜，不用 seed 改生产公式。

## 1. 本轮运行及可复现输入

所有新产物在 `output/opening-research-20261011/`；精选可公开的自有/数值证据在 `coderisk/experiment/evidence/opening-research-20261011/`。新输出不覆盖旧目录。

| 入口 | 输入及配置 | 本轮目录 | 结论资格 |
| --- | --- | --- | --- |
| group_action_properties.py | 12自有手标gold，seed 20261011/73/901，各48置换 | properties-final | 有限性质/机制，不是benchmark |
| similarity_ablation.py | 原91 seed，冻结similarity_ablation_v1.json | ablation | 开发探索，正式资格0 |
| diagnose_fusion.py | 历史ConPlag两view的分数及验证阈值，仅读取 | conplag-readonly-r2 | 已观察test的描述诊断，不新训练/重评分 |
| natural_similarity_calibration.py | natural_calibration_v1.json，可信参考0 | natural | 全部规则回退，不是统计校准收益 |
| check_formal_readiness.py | 原manifest/schema及冻结/证据前检 | readiness | FORMAL_BLOCKED，操作清单而非结果补造 |

properties/properties-r2 为扩充或补统计前的自有探针运行，保留而不伪装为最终版本。早期 conplag-readonly 缺 matplotlib，已有部分CSV但无完整manifest，不算成功；失败与环境安装重试在 S0 记录。最终完整只读诊断 `new_detector_runs=0`、`new_parameter_fitting=false`。

## 2. 独立性质证据

生产索引不参与手标 oracle 的准入。9 Python /3 Java fixture，完整声明/引用坐标和预期规范身份手写；stdlib AST/symtable 交叉检查部分符号属性。采样同时置换用独立 tokenizer/scanner，另一 marker 渲染路径核查对应位置；只复用旧工具的随机排列函数。**人工gold仍可能漏标，symtable不单独证明所有reference/keyword；这是相对独立，不是全语言形式认证。**

| 状态 | 次数 | 含义 |
| --- | ---: | --- |
| ACCEPTED_VALID | 1,728，通过1,728 | 12×3×48有限置换；完整C、gold绑定、恒等/逆/复合通过 |
| REJECTED_UNSUPPORTED | 5 | 已知dynamic、alias、comprehension、nonlocal、Java header shadow |
| PARSER_FAILURE | 2 | Python语法失败、Java未闭合；空identifier+raw |
| INVALID_CAPTURE | 1 | 非双射映射，被拒绝 |
| ORACLE_UNCERTAIN | 2 | opaque外部查名封装、Java重载；不计成功 |
| 总尝试 | 1,738 | 分母不隐藏不支持/不确定 |

另完成6次自有 Java gold/变体 javac，均通过，未执行源码。其用途仅为源码语法/类型可接受性，非语义或binding证明。`fixture_summary.csv` 给出各fixture的唯一置换、唯一源码、理论有限轨道大小；多seed重复和未使用名稳定子不会被算作独立作者。`rename_sensitivity.csv` 是216个自有成对评分探针；不同fixture/seed的复用仍不独立，耗时仅该次环境观察。

## 3. 判别机制及负结果

| 自有机制 | 完整C相等 | Canonical分 | 融合分 | 可解释内容 |
| --- | --- | ---: | ---: | --- |
| 同名双作用域分别改left/right | 是 | 1 | 0.84 | α-相关但不在统一拼写同轨道；C不是G轨道单射特征 |
| 两/三次重复增量语句 | 否 | 1 | 1 | n-gram集合丢失次数；raw/AST/mapping也全部1 |
| +改- | 否 | 0.6 | 0.66 | 普通符号变化不在G，mapping仍1不证明功能相同 |
| 插入print语句 | 否 | 0.461538 | 0.525 | 插语句不受改名定理约束 |

受控机制组由研究者专门构造，用来说明可能的信息损失，**不是独立创作负例、真实FPR、完整语义判断或AI检测**。不得用“4个机制中的高分比例”预测实际误报。C相同不等于关系成立；指纹相同还比C相同更弱。

## 4. 14方法消融：SYNTHETIC_DEVELOPMENT

原输入91；同语言Java/Python被分析75，其余16按现有准入排除。所有14方法共同有效支持68，validation32/test36；canonical/mapping不可用7对仍在 AVAILABLE/降级记录，不偷偷填0或将raw说成canonical。主要比较共同test36（21正/15负；NaturalSimilar负例7），不是全部91或公开池92,513。selection只读validation，test未用于选参。

| 方法 | Precision | Recall | F1 | FPR | NaturalSimilar FPR | PR面积(AP score) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RAW_ONLY | .5833 | 1.0000 | .7368 | 1.0000 | 1.0000 | .6134 |
| AST_ONLY | .8000 | .9524 | .8696 | .3333 | .7143 | .8736 |
| CANONICAL_ONLY | .9444 | .8095 | .8718 | .0667 | .1429 | .8996 |
| MAPPING_ONLY | .5833 | 1.0000 | .7368 | 1.0000 | 1.0000 | .6679 |
| AST_CANONICAL_EQUAL | .9444 | .8095 | .8718 | .0667 | .1429 | .9054 |
| ALL_EQUAL | .7143 | .9524 | .8163 | .5333 | 1.0000 | .7328 |
| PICAS_FIXED | .6667 | .9524 | .7843 | .6667 | 1.0000 | .7454 |
| PICAS_RULE_DYNAMIC | .7647 | .6190 | .6842 | .2667 | .5714 | .7454 |
| PICAS_DYNAMIC_OFFSET | .8182 | .8571 | .8372 | .2667 | .5714 | .7454 |

余下所有两两组合见 `ablation/metrics.csv` 和 `REPORT.md`，不只保留最佳行。AP按并列score成组的非插值Average Precision计算，非梯形PR-AUC；跨方法阈值的rank含义不同，margin AP另列。固定FPR下Recall见COMMON_LOW_FPR行：只限制validation达到目标，必须同时报告test实际FPR，不能保证总体误报上限。Recall@K因完整标注候选池不足为N/A，不能从随机pair计算检索召回。

观察：规则动态阈值在该synthetic小集合中FPR低于validation选定的固定阈值方案，但Recall .9524→.6190、F1 .7843→.6842；规范化方法也有召回代价。**不是“证明动态阈值有总体收益”**。没有真实独立标签，不能外推教学效果。完整融合不是最优，保留负结果。

## 5. PUBLIC_PILOT只读贡献诊断

保留两套历史view各911，validation284/test627，不认为两view合计1,822独立pair。代数式：

`Full-NoCanon=.45*(canonical-.5*(raw+AST))+.15*(mapping-.5*(raw+AST))`。

只逐行校验已有分数，容差2e-6；不拟合权重/阈值，不重跑当前分析器。version_1未排共同模板，version_2采用历史模板排除背景，两者分表。

| 既有test627 | Full F1 | NoCanon F1 | Full FPR | NoCanon FPR |
| --- | ---: | ---: | ---: | ---: |
| version_1 | .5543 | .5985 | .0626 | .0605 |
| version_2 | .6974 | .7352 | .0734 | .0842 |

version_1的463公开负例中，融合抬高13、降低450；164正例中抬高11、降低118。canonical平均贡献负例−.07648、正例−.06093，mapping平均贡献也负。version_2负例canonical平均−.07616、mapping+.01235；正例canonical−.06390、mapping+.00866。不能简化成“canonical只让无关程序都变高”；冻结阈值不同、结构错位/短代码/共享模板/改写类型及解析覆盖共同影响决定。version_2负例FPR较低却召回更低，F1仍逊于NoCanon。

`changed_decision_cases.jsonl` 列具体公开pair与变化；`component_contributions.png` 是描述图，不因果推断。旧JPlag比较仍参考原共同支持（version_2为625而非627）：Full .6997/NoCanon .7375/JPlag .7550。**本轮没有重新运行JPlag，不拼接新scores与旧JPlag成绩。**

## 6. 统计校准与正式效果受阻

自然校准的新运行是same-query ALL_TEST_POLICY40，不等于上面的COMMON36。可信独立reference0、q可计算query0，STATISTICAL_WITH_RULE_FALLBACK与RULE_DYNAMIC完全相同。该相同是规则回退事实，**不能证明q有效**。正式检查是`FORMAL_BLOCKED`与`BLOCKED_INSUFFICIENT_INDEPENDENT_REFERENCES`；生产动态阈值继续原样。

主实验默认problem-disjoint新题冷启动。要评估同题q，需另做预登记context panel，参考代码/作者/家族/hash与query隔离，同题面板不能冒称reference/test题目隔离。参见 [公平协议V2](FAIR_EVALUATION_PROTOCOL_V2.md)。

## 7. 可写及不可写

可写：定义、条件证明、有限测试和实测工程状态；自有机制揭示信息损失；明确限定的合成预实验与公开pilot负结果。正式推论待有授权、独立标注、冻结测试、统计区间后作出，不保证显著性。不得写“普遍降低误报”“全面优于JPlag/AI”“九万真实正式benchmark”“完整语义等价/确认抄袭”。

后续P0：真人授权/双审/独立来源，导师核验理论及文献；P1：在新冻结数据运行可信比较/失败分析；P2：再考虑实验性权重或新表示提案，当前不改生产。
