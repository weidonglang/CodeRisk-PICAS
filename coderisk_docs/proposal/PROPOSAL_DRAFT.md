# 毕业设计开题报告内容初稿

## 拟定题目

基于题目感知与标识符规范化的编程作业代码相似风险检测系统设计与实现。

本文为2026年10月8日形成的开题内容稿，未填写学校、学号、导师等未知信息。文献编号采用文献矩阵的稳定 ID；学校模板与正式参考编号确定后再排版。

同日进度补充：已增加 [数据规范](DATA_PROTOCOL.md)、[公平评测流程](FAIR_EVALUATION.md) 和 [核心修复记录](CORE_REVIEW.md)，新的评测入口已在合成开发数据实际运行。以下正式研究安排仍以新来源数据与冻结测试为目标。

2026-10-09 前期工作补充：已完成 C/HTML 同语言实验检测、版本/共同模板复核上下文和 ConPlag 911 对公开单人标签探索评测；最近工程验证为 Python 126 项、后端 12 项、前端与 CI 通过。完整融合未在该次探索比较中取得最高 F1，动态阈值减少自然相似误报仍待新数据验证。具体依据见 [探索结果](CONPLAG_PILOT_RESULTS.md)、[版本与模板范围](VERSION_AND_NATURAL_SIMILARITY.md) 和 [毕设准备核查](../GRADUATION_READINESS_REVIEW.md)。以下研究目标保持为待验证问题。

## 1. 选题背景与意义

源代码相似性分析通过比较程序的词法、语法或其他表示，为代码复用、克隆分析和教学作业检查提供技术支持。不同应用对“相似”的解释并不相同：软件维护关注重复片段，编程作业复核则需要考虑题目要求、共同模板和提交来源。[R01](https://www.joca.cn/EN/10.11772/j.issn.1001-9081.2023040551)，[R11](https://arxiv.org/abs/2306.16171)

在同题作业中，学生共享输入输出约定，部分题目的实现路径也较集中。因此，本课题将自然相似作为需要在数据中考察的现象，而不是预先认定所有高相似代码都具有不当复制关系。已有工具通过排除共同模板处理部分共享代码，这说明教学条件应参与结果解释，但不能直接证明题目画像阈值优于现有方案。[D02](https://dolos.ugent.be/docs/running.html)

另一方面，变量、参数、函数改名和格式变化会改变程序的表面表示。检测方法需要考察对这些变化的鲁棒性，同时防止规范化消除过多区分信息。已有改写评估研究区分了鲁棒性和准确性：保留相关程序的高相似信号，与区分无关程序是两项需要共同评价的能力。[R09](https://arxiv.org/abs/2102.03997)

本课题拟在已有系统原型上，研究题目画像驱动的阈值调整与作用域标识符规范化，将相似度、阈值、风险边际和源代码证据统一展示。其工程意义是形成可追溯的作业复核流程；其研究意义是检验题目条件、规范化与误报/漏报之间的关系。系统定位为辅助复核工具，最终学术评价仍需结合具体教学材料。

## 2. 国内外研究现状

### 2.1 表示与匹配方法

代码克隆检测已形成文本、Token、树结构及其他表示路线。Roy 等建立了技术分类和编辑场景比较框架；国内代码相似性综述进一步整理了源码、二进制及跨语言技术路线。[R02](https://www.sciencedirect.com/science/article/pii/S0167642309000367)，[R01](https://www.joca.cn/EN/10.11772/j.issn.1001-9081.2023040551)

JPlag 研究面向程序集合采用 Token 表示与匹配，是教学作业比较的重要参照。Winnowing 研究的是局部文档指纹选择，不能将所有使用 n-gram 的方法等同于该算法。DECKARD 采用树结构特征路线，SourcererCC 则通过索引与过滤关注大规模 Token 比较。[R03](https://www.jucs.org/jucs_8_11/finding_plagiarisms_among_a/Prechelt_L.pdf)，[R04](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf)，[R05](https://web.cs.ucdavis.edu/~su/publications/icse07.pdf)，[R06](https://arxiv.org/abs/1512.06448)

本系统目前使用原始 Token 和节点类型 n-gram 的集合重合，而不是树编辑距离、子树匹配或倒排索引。因此，相关方法为设计参照，不能把其理论保证和扩展性结果转移到本系统。

### 2.2 教学工具与改写鲁棒性

Dolos 将相似分析与交互展示集成到教学环境，表明已有工具并非只有单一百分比分数。改写鲁棒性研究则提示，需要分别考察改名和结构变化等不同类型。[R10](https://biblio.ugent.be/publication/8744589)，[R09](https://arxiv.org/abs/2102.03997)

本课题不宣称首次使用规范化或证据可视化，而是针对同题作业将题目画像、相似信号和阈值解释组织为统一流程。跨语言语义与复杂结构变换超出本科主实验范围。

### 2.3 数据与评价

BigCloneBench 研究强调不同克隆类型和相似程度下的工具评估；评测综述关注精确率、召回率、时间和扩展性。近期系统综述也将可靠数据与实证评价列为需要关注的问题。[R07](https://clones.usask.ca/pubfiles/articles/SvajlenkoEvaluatingToolsICSME2015.pdf)，[R08](https://arxiv.org/abs/2006.15682)，[R11](https://arxiv.org/abs/2306.16171)

工业项目中的克隆基准与同题作业关系标签不同，不能直接用前者替代后者。课题需要区分独立来源、已知改写与不确定关系，并控制同题和同源样本在不同集合之间的泄漏。

### 2.4 本课题的研究定位

目前文献足以支持方法分类、改写评估和可信数据建设，但尚不足以证明“题目感知阈值是无人研究的新问题”。本课题将其作为场景化设计与待验证机制，继续核查相关工作，并通过固定阈值、规范化消融和外部基线检验收益及代价。此现状稿基于首批核查材料，后续还需精读和补充近年研究。

## 3. 研究目标与主要内容

总体目标是完善 Java/Python 同语言作业相似风险系统，在不执行上传代码的前提下，输出可追溯的指标、阈值与复核证据，并在独立数据上验证其适用条件。

研究内容包括：

1. 对题目、提交、任务、结果、指标、证据和报告进行一致性管理，完善从上传到复核的流程。
2. 对代码进行词法处理和作用域标识符规范化，区分变量、参数、函数与类名，评价改名鲁棒性和复杂语法边界。
3. 从题面、输入输出、约束与关键词建立规则画像，生成有界阈值，验证其对自然相似误报和召回的影响。
4. 融合稳定的相似信号，输出相似片段、映射、阈值分解与解析告警，核查行号和指标的一致性。
5. 构建可追溯样本，开展阈值对比、规范化对比、消融、JPlag 对齐和失败案例分析。

预期形成系统设计与实现、可复现实验材料和研究结论。效果结论取决于实际结果，不预设某一指标达到固定数值。

## 4. 拟采用的方法与技术路线

### 4.1 系统架构

采用 Vue 3 前端、Spring Boot 业务服务与 FastAPI 分析服务。业务服务负责存储、任务编排和查询，分析服务负责代码表示、评分和证据提取；实验脚本独立运行。数据库采用 JDBC/Flyway 管理，已有 H2 验证基础，MySQL 实库验证待有效凭据下完成。

技术路线如下：

```text
题目及代码输入
  → 存储、校验与来源登记
  → 词法处理 / 基础结构提取 / 作用域规范化
  → 原始 Token、结构、规范化 Token、映射信号
  → 多维综合相似度

题目文本 → 规则画像 → 有界动态阈值

综合相似度与动态阈值
  → 风险边际与风险等级
  → 片段、映射、告警与阈值解释
  → 前端复核和 HTML 报告

独立样本与冻结配置
  → 对比、消融、基线对齐、失败分析
  → 回答研究问题
```

### 4.2 代码表示与规范化

原始 Token 相似度基于 n-gram 集合的 Jaccard 重合率。基础结构指标先获得节点类型序列，再构造 n-gram 集合；Python 使用原生 AST，Java 使用简化结构解析。规范化在支持范围内将作用域符号映射到规范名称，生成规范化 Token，并通过对齐符号的覆盖与一致性构建映射信号。

Jaccard 集合会丢失重复出现次数及部分全局顺序信息；Java 简化解析不是完整语法校验。它们是需要在失败案例中考察的限制，不在本稿中称为完整结构或语义表示。

### 4.3 综合分与题目阈值

当前正常解析路径使用四项融合：

```text
S = 0.20 × rawToken + 0.20 × basicStructure
  + 0.45 × canonicalToken + 0.15 × identifierMapping
```

解析或规范化不可用时，当前综合分降级为原始 Token 分数，并输出相关告警。正式实验应记录降级情况，不仅报告成功解析子集。

当前生产阈值规则为：

```text
T = clamp(0.68 - 0.06D - 0.04U + 0.08P + 0.12N, 0.50, 0.95)
m = S - T
displayScore = clamp(0.5 + m / 0.40, 0, 1)
```

D、U、P、N 分别为难度、解法空间、模板风险和自然相似风险的规则估计。它们不是人工标注的真实难度或风险概率。历史提交分布当前不参与调整，不能声称已经实现统计学习校准。

当前等级按 m 划分：小于−0.10为 LOW，−0.10至0为 MEDIUM，0至0.10为 ELEVATED，达到0.10为 HIGH。展示分数是风险边际的归一化映射，不是抄袭概率。实验分类采用 S≥T 的二元决策，与四级展示区分。

### 4.4 证据与复核

证据包括 Token 重合片段、基础结构片段、规范化信号、标识符映射、阈值分解及解析告警。核查证据是否定位到原代码、是否与结果一致、是否包含充分的解析边界说明。未开展受控用户研究前，不声称提高教师复核效率或解释质量。

## 5. 实验设计与验证方案

### 5.1 样本与标签

优先收集经授权、脱敏的独立解答、可追溯人工改写及公开许可样本。正例为具有已知派生关系、需要检测的变换代码对；负例为有独立来源依据的代码对。自然模板相似作为负例子集。无法确认关系的样本仅用于失败分析，不能依据分数倒推标签。

按题目和来源家族划分验证集与测试集，核对代码哈希交叉。现有已检查过的91对合成样本用作开发与回归基础，不能作为未来改进方法的全新独立测试证据。新样本的划分在分析前登记，正式样本量由实际可获得题目与来源独立性决定，不仅追求代码对数量。

AI 辅助改写只作为可选样本类型，必须记录模型、提示、生成时间、人工审核与功能检查。功能检查使用独立受控流程或已有测试记录，业务上传分析继续不执行代码。

### 5.2 方法比较与参数控制

| 实验 | 控制方式 | 评价重点 |
| --- | --- | --- |
| 固定与动态阈值 | 相同综合分、相同样本；固定阈值从验证集选择 | 自然相似 FPR、总体 FPR、Recall、F1 |
| 原始与规范化 Token | 同一代码对与相同表示参数，分开评价改名和格式变化 | 分数保留、变换子集 Recall 与负例误报 |
| 规范化消融 | 明确移除哪些信号；剩余权重按预注册方式重新归一化 | 指标贡献及误报/漏报变化 |
| 外部基线 | JPlag 与 PICAS 使用共同有效子集，记录版本、阈值、最小匹配长度和模板设置 | 可比集合上的 Precision、Recall、F1、FPR |
| 运行与失败分析 | 同硬件记录代码长度、提交数、解析状态和耗时 | 规模代价、解析降级、模板误报与复杂改写漏报 |

历史 E3/E4 脚本包含固定阈值和特定重加权方式，不能直接当作所有拟定公平实验的实现。新增入口已补齐统一选择规则：各方法只在验证集选择阈值；原始生产规则与校准后方法分别报告。后续在新数据冻结后执行正式实验。JPlag 原始相似度与 PICAS 综合分含义不同，不强行要求阈值数值相同。

若比较模板排除，应采用双方可对齐的同一模板信息；默认模式与模板排除模式分表报告，不能只选有利配置。Dolos 当前未运行，不列为已完成基线。

### 5.3 指标、冻结与结果解释

报告 TP、FP、TN、FN、Precision、Recall、F1、FPR，并注明分母与子集样本数。若分母为零，使用明确的未定义或约定标记，不能解释为效果完美。派生改写对存在相关性，统计区间需要按题目/来源家族处理。

正式测试前冻结数据、标签、表示、权重与阈值选择规则。修改生产公式与实验 offset 分开记录；生产公式不因种子结果自动改变。测试结果只用于报告，若继续据此改进，需重新保留独立测试数据并说明探索过程。

解释重点是题目感知是否带来有意义的误报—召回取舍，以及规范化在哪些场景有效。若外部基线更好或某项改进无效，应保留负结果并分析原因，不删去不利样本。

## 6. 可能的设计特色与预期成果

设计特色包括题目画像驱动的风险阈值、作用域规范化与映射证据、以及结果—阈值—片段的统一可追溯输出。它们属于拟验证的场景化组合，不作为未经文献与实验核准的首创声明。

预期成果为：完善的系统原型；经授权的研究数据卡与清单；冻结配置下的对比、消融和失败报告；本科论文、演示脚本与答辩材料。代码能力和实验结论分别验收，不要求所有指标都优于外部工具。

## 7. 前期基础与可行性

已有三层工程、统一接口、持久化与报告流程，为后续研究减少了基础开发工作。2026年10月8日验证记录为 Python 38 项通过、后端8项通过及前端构建通过；GitHub Actions 三项检查通过。这些验证支持工程回归状态，不等于真实教学效果或 MySQL 实库验证。

已有数据校验和实验脚本可以支持研究流程，但真实数据仍是主要不确定条件。研究不依赖训练大型模型；单对代码分析具有较低环境门槛，但全部提交两两比较需要 n(n−1)/2 对分析，规模性能需实测。

若无法及时取得真实作业，可使用有授权的独立人工解答开展受控小样本实验，并限定结论范围；不能将生成改写样本称为真实学生数据，也不能保证获得足够统计证据。

## 8. 进度安排

| 相对周次 | 任务与产出 |
| --- | --- |
| W1 | 确认题目、整理前期工作、完成首批文献矩阵与现状初稿 |
| W2 | 按学校要求修订开题；制定标注规则并试跑小规模真实样本 |
| W3—W4 | 扩充样本、核查来源与隔离、修复核心算法边界、补公平评测设置 |
| W5 | 冻结配置、正式对比与消融、运行并对齐 JPlag |
| W6 | 分析失败案例、验证新环境演示、完善系统测试材料 |
| W7 | 完成论文初稿，核对引文、图表和技术主张 |
| W8 | 导师修改、学校模板排版、答辩演练和归档 |

时间安排是工作估计，尚未对应学校正式日期。研究、系统修复和论文写作并行进行。

## 9. 主要风险及对策

数据不足时缩小结论范围；阈值损失召回时同时报告代价；Java 解析不完整时记录降级和支持范围；课题范围过大时移出跨语言和高级图分析。没有用户研究时仅评价证据追溯性，不声称复核效率提升。

正式报告需按学校要求补齐封面、任务书、文献数量和具体日期。所有文献题录、引用位置与全文依据在提交前再次核实；个人应能够独立解释方法和结果，并按学校要求说明 AI 辅助。

## 10. 首批参考来源

以下为工作题录，阅读状态见 [文献矩阵](LITERATURE_MATRIX.md)。正式顺序编码、期刊与预印本版本选择和学校要求的参考数量在提交前统一处理。尚未核准的会议页码暂不填写；未完整核准的候选不进入本稿论证。

- R01：孙祥杰，魏强，王奕森，杜江. 代码相似性检测技术综述. 计算机应用，2024，44(4)：1248—1258. DOI：[10.11772/j.issn.1001-9081.2023040551](https://www.joca.cn/EN/10.11772/j.issn.1001-9081.2023040551).
- R02：ROY C K, CORDY J R, KOSCHKE R. Comparison and evaluation of code clone detection techniques and tools: A qualitative approach. Science of Computer Programming, 2009, 74(7): 470—495. DOI：[10.1016/j.scico.2009.02.007](https://www.sciencedirect.com/science/article/pii/S0167642309000367).
- R03：PRECHELT L, MALPOHL G, PHILIPPSEN M. Finding Plagiarisms among a Set of Programs with JPlag. Journal of Universal Computer Science, 2002, 8(11): 1016—1038. DOI：[10.3217/jucs-008-11-1016](https://www.jucs.org/jucs_8_11/finding_plagiarisms_among_a/Prechelt_L.html).
- R04：SCHLEIMER S, WILKERSON D S, AIKEN A. Winnowing: Local Algorithms for Document Fingerprinting. SIGMOD, 2003. [作者 PDF](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf).
- R05：JIANG L, MISHERGHI G, SU Z, GLONDU S. DECKARD: Scalable and Accurate Tree-based Detection of Code Clones. ICSE, 2007. DOI：10.1109/ICSE.2007.30. [作者 PDF](https://web.cs.ucdavis.edu/~su/publications/icse07.pdf).
- R06：SAJNANI H, SAINI V, SVAJLENKO J, et al. SourcererCC: Scaling Code Clone Detection to Big Code. ICSE, 2016. DOI：10.1145/2884781.2884877. [已读取的作者预印本](https://arxiv.org/abs/1512.06448).
- R07：SVAJLENKO J, ROY C K. Evaluating Clone Detection Tools with BigCloneBench. ICSME, 2015. [作者机构 PDF](https://clones.usask.ca/pubfiles/articles/SvajlenkoEvaluatingToolsICSME2015.pdf).
- R08：SVAJLENKO J, ROY C K. A Survey on the Evaluation of Clone Detection Performance and Benchmarking. arXiv:2006.15682, 2020. [预印本](https://arxiv.org/abs/2006.15682).
- R09：CHEERS H, LIN Y, SMITH S P. Evaluating the robustness of source code plagiarism detection tools to pervasive plagiarism-hiding modifications. arXiv:2102.03997, 2021. [预印本](https://arxiv.org/abs/2102.03997).
- R10：MAERTENS R, VAN PETEGEM C, STRIJBOL N, et al. Dolos: Language-agnostic plagiarism detection in source code. Journal of Computer Assisted Learning, 2022, 38(4): 1046—1061. DOI：[10.1111/jcal.12662](https://biblio.ugent.be/publication/8744589).
- R11：ZAKERI-NASRABADI M, PARSA S, RAMEZANI M, et al. A systematic literature review on source code similarity measurement and clone detection: techniques, applications, and challenges. arXiv:2306.16171, 2023. [预印本](https://arxiv.org/abs/2306.16171).
- D02：Dolos. Running Dolos CLI. [官方工具文档](https://dolos.ugent.be/docs/running.html)，核查日期：2026年10月8日。
