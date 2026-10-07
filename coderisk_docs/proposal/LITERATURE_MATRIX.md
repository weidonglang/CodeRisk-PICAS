# CodeRisk 首批文献矩阵

检索日期：2026年10月8日。检索入口包括出版社、作者所在机构、作者论文页面、arXiv 和工具官方文档。

## 阅读状态与用途

本轮为开题范围内的首批检索，不是穷尽性系统综述。表中“摘要”表示只核查元数据及摘要；“节选”表示核查正文中的相关段落，不等于通读；“文档”表示核查工具功能，不能替代学术论文。精读、复现实验和最新文献扩展仍需继续。

R 编号固定用于追溯材料，最终参考文献编号按正文首次出现顺序重新生成。外文预印本按已读取的预印本版本记录，不猜测其正式发表卷期。经典文献用于说明技术来源，不能独自证明截至2026年的全部研究现状。

## 已核查来源

| ID | 文献及已核实信息 | 阅读状态 | 可支持的内容 | 对本课题的作用与限制 |
| --- | --- | --- | --- | --- |
| R01 | 孙祥杰、魏强、王奕森、杜江，代码相似性检测技术综述，计算机应用，2024，44(4)：1248—1258；DOI 10.11772/j.issn.1001-9081.2023040551 | 期刊页面、摘要和技术分类节选 | 源码/二进制及不同表示路线的技术分类 | 中文现状入口；范围比本课题广，不能直接作为教学场景阈值有效性的证据 |
| R02 | Roy C K, Cordy J R, Koschke R，Comparison and evaluation of code clone detection techniques and tools: A qualitative approach，Science of Computer Programming，2009，74(7)：470—495；DOI 10.1016/j.scico.2009.02.007 | 出版方题录与摘要 | 克隆类型、编辑场景与技术比较框架 | 帮助设计变换类别；全文方法细节待精读，不沿用历史结论评价所有新工具 |
| R03 | Prechelt L, Malpohl G, Philippsen M，Finding Plagiarisms among a Set of Programs with JPlag，Journal of Universal Computer Science，2002，8(11)：1016—1038；DOI 10.3217/jucs-008-11-1016 | 期刊页面、PDF 方法节选 | 程序作业相似分析、Token 表示与匹配 | 基线理论背景；2002论文不能替代本项目使用的6.2.0版本配置说明 |
| R04 | Schleimer S, Wilkerson D S, Aiken A，Winnowing: Local Algorithms for Document Fingerprinting，SIGMOD，2003 | 作者发布 PDF 的摘要、引言与指纹选择段落 | k-gram 与局部指纹选择的区别及检测保证 | 相关技术背景；本项目未实现 Winnowing，不承接其理论保证；未核准的 DOI 和页码暂不填写 |
| R05 | Jiang L, Misherghi G, Su Z, Glondu S，DECKARD: Scalable and Accurate Tree-based Detection of Code Clones，ICSE，2007；DOI 10.1109/ICSE.2007.30 | 作者 PDF 方法概述与机构题录 | AST 子树向量与聚类检测路线 | 解释结构方法；本项目只有节点类型 n-gram，不等同于 DECKARD 或子树匹配 |
| R06 | Sajnani H, Saini V, Svajlenko J, Roy C K, Lopes C V，SourcererCC: Scaling Code Clone Detection to Big Code，ICSE，2016；DOI 10.1145/2884781.2884877；读取预印本 arXiv:1512.06448 | 作者预印本页面、摘要 | Token 检测、倒排索引与过滤的扩展性路线 | 可讨论两两比较的规模限制；非教学作业基准，不能直接移植性能数值 |
| R07 | Svajlenko J, Roy C K，Evaluating Clone Detection Tools with BigCloneBench，ICSME，2015 | 作者机构 PDF 摘要与引言 | 按克隆类型与语法相似程度分组评估 | 支持分层评估思路；工业 Java 克隆关系不等于同题独立解答/改写关系 |
| R08 | Svajlenko J, Roy C K，A Survey on the Evaluation of Clone Detection Performance and Benchmarking，arXiv:2006.15682，2020 | 作者预印本元数据与摘要 | 检测工具的 precision、recall、时间、扩展性评估 | 支持多维评测；不能据摘要复述完整统计结果 |
| R09 | Cheers H, Lin Y, Smith S P，Evaluating the robustness of source code plagiarism detection tools to pervasive plagiarism-hiding modifications，arXiv:2102.03997，2021 | 作者页面、PDF 摘要及引言 | 改写鲁棒性与判别准确性是不同性质 | 规范化实验必须同时看负例；只用改名高相似不能证明低误报；本轮按预印本引用 |
| R10 | Maertens R, Van Petegem C, Strijbol N, Baeyens T, Jacobs A, Dawyndt P, Mesuere B，Dolos: Language-agnostic plagiarism detection in source code，Journal of Computer Assisted Learning，2022，38(4)：1046—1061；DOI 10.1111/jcal.12662 | 机构题录与摘要 | 教学场景中的工具集成与交互式相似展示 | 不声称现有工具缺少证据界面；language-agnostic 不等于完整跨语言语义等价 |
| R11 | Zakeri-Nasrabadi M, Parsa S, Ramezani M, Roy C, Ekhtiarzadeh M，A systematic literature review on source code similarity measurement and clone detection: techniques, applications, and challenges，arXiv:2306.16171，2023 | 作者页面、PDF 摘要与引言 | 相似来源多样，可靠数据与评估存在挑战 | 支持数据与标签的谨慎设计；期刊版本另有 DOI 10.1016/j.jss.2023.111796，最终需核查正式题录再切换 |
| D01 | JPlag 官方仓库及使用说明 | 文档节选 | 基础代码排除、工具配置及版本入口 | 外部基线必须记录参数；不能把旧论文与当前版本性能混为一谈 |
| D02 | Dolos 官方 Running Dolos CLI 文档 | 文档节选 | 模板文件排除与运行方式 | 说明已有共同代码处理方案；是当前功能说明，不是本课题效果实验 |

## 来源链接

- R01：[期刊官方页面](https://www.joca.cn/EN/10.11772/j.issn.1001-9081.2023040551)。中文入口一度访问失败，使用同一论文英文页面核查中英文题名、作者及卷页。
- R02：[出版方页面](https://www.sciencedirect.com/science/article/pii/S0167642309000367)。检索结果返回题录与摘要，后续直接打开失败；本轮不标为全文已读。
- R03：[期刊题录](https://www.jucs.org/jucs_8_11/finding_plagiarisms_among_a/Prechelt_L.html)、[期刊 PDF](https://www.jucs.org/jucs_8_11/finding_plagiarisms_among_a/Prechelt_L.pdf)。
- R04：[作者发布的 PDF](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf)。
- R05：[作者 PDF](https://web.cs.ucdavis.edu/~su/publications/icse07.pdf)、[机构题录](https://ink.library.smu.edu.sg/researchdata/2/)。
- R06：[作者预印本](https://arxiv.org/abs/1512.06448)。
- R07：[作者机构 PDF](https://clones.usask.ca/pubfiles/articles/SvajlenkoEvaluatingToolsICSME2015.pdf)。
- R08：[作者预印本](https://arxiv.org/abs/2006.15682)。
- R09：[作者预印本](https://arxiv.org/abs/2102.03997)、[PDF](https://arxiv.org/pdf/2102.03997)。
- R10：[根特大学题录与摘要](https://biblio.ugent.be/publication/8744589)。
- R11：[作者预印本](https://arxiv.org/abs/2306.16171)、[PDF](https://arxiv.org/pdf/2306.16171)。
- D01：[JPlag 官方仓库](https://github.com/ls1intum/jplag)。
- D02：[Dolos 官方文档](https://dolos.ugent.be/docs/running.html)。

## 候选与元数据陷阱

1. 陈秋远、李善平、鄢萌、夏鑫：《代码克隆检测研究进展》。已读取[作者稿](https://yanmeng.github.io/papers/rjxb18Qiuyuan.pdf)的摘要和分类说明，但稿中存在 DOI、日期与页码占位字段。检索指向2019年软件学报正式版本，直接访问官方全文未成功；本轮不将作者稿中的占位信息复制进正式题录。下一轮从学校图书馆或期刊正式记录核准。
2. Kamiya、Kusumoto、Inoue 的 CCFinder 论文：已核实[作者机构题录](https://sel.ist.osaka-u.ac.jp/lab-db/betuzuri/contents.en/387.html)，2002年、28(7)：654—670；尚未读到正文，列为精读候选，不根据题名推导详细算法。

## 首轮综合判断

上述来源覆盖了词法、指纹、树结构、教学工具和评估方法。共同代码处理、规范化和交互展示已有研究与产品基础，因此不能将其概括为现有工具的普遍缺失。

本课题的可执行切入点是：在受限同题作业场景中，评估题目画像阈值与作用域规范化的组合，并保持证据可追溯。这是项目研究问题的选择，不是“文献中尚无人研究”的证明。题目画像系数是否合理、是否超越更简单的固定阈值方案，需用本项目数据检验。

## 下一轮精读任务

1. 先读 R03、R09 的方法与实验设置，整理改名、结构改写及共同模板的处理差异。
2. 读 R01 与 R11 的分类、数据和局限部分，补齐相关工作段落的具体出处。
3. 读 R08 的评估设计，确定样本覆盖、基线参数、无效样本和置信区间的报告方式。
4. 扩展2024—2026年教学作业评测与题目条件相关文献，核验本课题差异；不能用本轮经典来源宣称掌握最新全部进展。
5. 最终选用前逐项核实全文、作者顺序、正式发表版本和 DOI，按学校要求确定中文与外文比例。
