# C、HTML 功能扩展与新数据接收记录

记录日期：2026-10-08。本文记录已实现能力和本地实际检查；解析覆盖不等于检测效果。Java/Python 仍是本科论文主实验，C 与 HTML 当前为实验扩展。

## 已接通的功能

| 语言 | 文件 | 当前处理 | 边界 |
| --- | --- | --- | --- |
| Java | `.java` | 原有词法、简化结构解析、作用域规范化、题目动态阈值 | 不是完整 Java 编译器 |
| Python | `.py` | 原有 Python 3 AST、作用域规范化、题目动态阈值 | Python 2 源码可能降级 |
| C | `.c` | Tree-sitter C 语法树、词法指纹、局部绑定规范化、原有题目阈值规则 | 不预处理、编译或执行；阈值尚未在标注 C 数据上校准 |
| HTML | `.html`、`.htm` | 标签/属性结构序列、源码规范化、词法指纹、固定阈值 | 不渲染网页，不执行脚本；不是浏览器 DOM 或视觉相似度 |

上传识别、任务创建、分析接口、结果查询、片段证据、页面展示和报告导出已接通。新语言显示 `EXPERIMENTAL`。后缀不区分大小写；`.cpp` 现在单独登记为 `cpp`，仅保留原有词法降级，不冒充 C 解析。含 C 或 HTML 的任务必须全部为同一种语言，否则后端返回 `TASK_LANGUAGE_DOMAIN_MISMATCH`，分析接口返回 HTTP 400。跨语言 IR 的实际范围仍为有限 Java/Python。

使用时为 C、HTML 分别建题目或任务，在同一题目上传至少两份同语言源码，再选择标准检测。不要在同一上传列表混入其他语言。HTML 源码在界面和报告中转义为文本。

## 算法与证据

C 的规范化处理函数定义、参数、普通局部/全局变量、块作用域、for 初始化作用域及声明顺序。字段名、类型名、外部库函数名保留。宏定义、条件预处理、typedef、extern、嵌套函数声明器、旧式参数声明等超出绑定子集时，退回原始词法评分并展示原因；没有生成规范化或变量映射证据。普通 `#include` 可以解析，但不会读取或展开头文件。结构解析成功不代表能够编译或语义正确。

HTML 规范化比较标签、排序后的属性、实体解码后的文本和属性值；保留 class、id、URL 等值。普通文本连续空白折叠，但保留跨标签边界的空格；script/style/pre/textarea 内容保留空白，SVG/MathML 起始标签保留原始大小写。重复属性、无法可靠恢复的非可选闭合标签退回词法评分。CSS `white-space`、JavaScript 行为、资源内容及浏览器容错语义均未分析。

规范化可用时，HTML 综合分为 `0.25×Token + 0.30×标签树序列 + 0.45×Canonical`，标识符映射权重为 0。配置 `htmlThreshold` 默认 0.85，必须为有限的 `[0,1]` 数值。公式版本为 `HTML_STRUCTURE_FIXED_V1`，策略为 `FIXED_UNCALIBRATED`；它是可配置的演示阈值，不是实证最优阈值。不构造虚假的算法题复杂度画像。解析或规范化不可用时仅使用词法分数，不能把降级得分解释为完整结构检测。

C 暂用已有 PICAS 四维融合与算法题阈值规则，新增能力仍需 C 标注数据验证。空源码、仅注释源码的相似度为 0，修复了空集合可能被当作完全相同的问题。C/HTML 片段位置使用原始 UTF-8 源码转换后的字符列及起止行；删除注释不移动原始位置。

分析结果通过 Flyway V3 增加 `problem_profile_json` 快照，阈值策略从每条结果原有 JSON 读取。HTML 不写入算法题画像表。旧结果缺少画像快照时仍回退历史题目画像，无法恢复过去未保存的画像；新结果独立保存。前端和导出报告均明确显示 HTML 固定阈值尚待验证。

## 本次取得的数据

| 来源 | 本次实际接收 | 可用角色 | 许可 |
| --- | --- | --- | --- |
| IBM Project CodeNet 1.0.0 | Java 107、Python 102、上游 C 目录 111，共 320 份，10 道题及 10 份题面 | 有来源和哈希的真实在线评测源码；当前只做开发解析检查 | 数据集 CDLA-Permissive-2.0 |
| MDN learning-area | `html/` 下全部 46 份 HTML | 官方教学参考源码，覆盖表单、文本、表格、多媒体标记等 | CC0-1.0 |

此前已取得的 AD2022 1,526 份 Java/Python 课程解答、ConPlag 911 对 Java 已发表单人标注样本保留，见[原获取记录](PUBLIC_DATA_INTAKE.md)。不要把提交数、代码对数和参考示例数相加当作“标注样本总数”。

来源入口：[IBM 官方仓库](https://github.com/IBM/Project_CodeNet)、[作者论文完整版的 A.6/B.6](https://jiechenjiechen.github.io/pub/codenet.pdf)、[CDLA 许可正文](https://cdla.dev/permissive-2-0/)、[MDN 固定提交](https://github.com/mdn/learning-area/tree/d55e1c2e3ff401519811b64e5b2a7d3643b43d0f/html)、[MDN 同提交的 LICENSE](https://github.com/mdn/learning-area/blob/d55e1c2e3ff401519811b64e5b2a7d3643b43d0f/LICENSE)。CodeNet 仓库工具代码的 Apache-2.0 许可不能替代数据集许可。

CodeNet 完整归档服务器报告为 8,343,137,473 字节。本次仅接收 HTTP Range `0–16,777,215`，即 16 MiB 前缀，SHA-256 为 `07095b7ed9e0b542899ef6b9600f1bf5914d496ab3aabf065f4c0443d0233c50`。按归档顺序，每题每语言最多选择前 12 个完整、非空、UTF-8 成员；不解压整个目录，不记录截断文件。前缀 SHA-256 是本地快照校验，不能声称获得发布者完整归档校验或验证完整 gzip CRC。ETag 为多段上传标识，不能当作完整文件 MD5。当前选取有顺序偏差，不代表整个 CodeNet。

前缀中没有所选提交的判题状态、用户身份元数据。所有提交记录使用 `UNKNOWN_METADATA_NOT_IN_PREFIX`、`author_id_available=false`、`UNLABELLED`、`eligible_for_core_metrics=false`。同题、不同 submission ID 或文件不同均不能证明独立实现。MDN 示例也没有真实学生抄袭标签；它们不能被假定为正例或独立负例。下载的源码均未执行。

MDN 固定提交为 `d55e1c2e3ff401519811b64e5b2a7d3643b43d0f`；逐文件保存原始下载地址、字节数和 SHA-256。没有抓取关联图片、视频或其他媒体资源。

## 实际解析检查

| 上游语言 | 接收数 | 当前结构解析成功 | 结构解析失败 | 规范化可用 |
| --- | ---: | ---: | ---: | ---: |
| Java | 107 | 106 | 1 | 106 |
| Python | 102 | 84 | 18 | 84 |
| C | 111 | 72 | 39 | 39 |
| HTML | 46 | 46 | 0 | 46 |

“成功”仅表示当前解析器接受该源码；Java 使用简化解析器，Python 使用 Python 3 AST，不能将此表解释为编译通过率或检测准确率。C 解析成功但规范化不可用的 33 份继续保留词法降级。本轮未计算任意数据对的风险分数或 Precision/Recall/F1。

C 目录的 9 份源码含 `namespace/template/class/::` 词法提示，需要语言复核；这些提示不是完整语言分类器。例如 `s923074053.c` 原始内容出现 `using namespace std`、C++ 模板和 `cout`，确认目录后缀不足以证明是 C。其余解析失败也可能来自语法版本、宏、非法源码等，不统一归因。保留全部失败记录，正式 C 数据应先复核语言与功能正确性，不能偷偷剔除后报告全量效果。

检查产物位于 [evidence/multilang-20261008](../../coderisk/experiment/evidence/multilang-20261008/README.md)：来源配置、382 个接收文件的完整性清单、逐提交记录、366 条解析记录及运行版本/代码指纹。离线重新导入得到完全相同的文件清单，原目录 382 个文件哈希验证通过。

## 复现

在仓库根目录运行，使用已安装项目依赖的 Python：

```powershell
# 首次下载到新的目录；--offline 仅使用已下载且哈希一致的缓存
python coderisk/experiment/acquire_multilang_dataset.py --output coderisk/data/public-datasets/multilang-replay
python coderisk/experiment/acquire_multilang_dataset.py --verify-only --output coderisk/data/public-datasets/multilang-replay
python coderisk/experiment/audit_multilang_sources.py --intake coderisk/data/public-datasets/multilang-replay --evidence .tmp/multilang-parser-replay
```

导入和审计输出目录必须是新目录，避免覆盖证据。若网络源、Range 响应或许可证页面发生改变，哈希检查应失败，由人工核查新快照；不能自动更新固定哈希。源码与本地缓存不推送 GitHub，仅推送导入器、来源固定配置、检查清单及文档。

本轮验证：Python 97 项测试通过，后端 10 项 H2/Flyway 集成测试通过，Vue TypeScript 检查与 Vite 构建通过。后端分析调用在集成测试中使用明确的测试替身；真实 C/HTML 算法接口通过 FastAPI TestClient 验证，不把测试替身输出当作实验成绩。

在本机 Tree-sitter 0.26.0 的批量遍历中观察到 Windows 原生访问冲突，保留树/解析器引用仍未消除；固定 `tree-sitter==0.25.2` 后全量审计和测试通过。语法包为 C 0.24.2、HTML 0.23.2。这是本机复现事实，尚未证明上游通用根因。旧 `.venv` 指向不可启动的 Store Python，保留原环境并创建 `.venv-coderisk`；启动脚本优先使用 `CODERISK_PYTHON`，其次恢复环境，再使用原 `.venv`。

本机 Java 测试通过提前加载 Byte Buddy agent 绕过沙箱动态 attach 限制：`mvn '-DargLine=-javaagent:C:/Users/WDL/.m2/repository/net/bytebuddy/byte-buddy-agent/1.14.19/byte-buddy-agent-1.14.19.jar' test`。普通环境仍使用 `mvn test`。本轮新迁移在 H2 MySQL 兼容模式验证，尚未在实际 MySQL 实例重放。

## 下一步实验条件

1. 对 C 候选逐条复核真实语言、题意与功能状态；保留排除理由和原始来源。
2. C/HTML 建立可靠代码对关系标签，覆盖公共模板自然相似、同题独立实现和已知派生关系，执行双人标注。人工或规则改写要单独登记为合成派生样本。
3. 按题目、来源/作者与派生家族冻结分集，再去重；当前缺少作者信息的数据不能声称作者隔离。现在只作为开发池，不能再当未见保留测试集。
4. 扩展公平评测器的 C 同语言共同集合与基线适配；HTML 另设结构任务与兼容基线。当前 `run_fair_evaluation.py` 与 JPlag 正式共同集合仍为 Java/Python，不能声称 C/HTML 已完成基线对比。
5. 验证集校准 C 阈值、HTML 固定阈值和融合权重，冻结后只运行一次保留测试；之后才能写论文效果结论。
