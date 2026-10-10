# Python 与多语言公开数据接收

> 2026-10-11 统计修订：本轮新增 **60,893 行**不变；按当前六份实际 JSONL，此前登记为 **31,620**，当前累计 **92,513**，原文旧合计 92,527 多 14 行。仅修正文档汇总，不改数据/标签，不声称全球内容去重或正式 benchmark。见 [逐行计数与 hash](../../coderisk/experiment/evidence/readme-data-refresh-20261011/README.md)。

工作日期：2026-10-10。本轮只扩充数据与接收工具，不修改相似度算法、生产权重、阈值或语言支持范围。所有下载代码均未执行，没有生成 synthetic 样例，也没有运行检测分数。

## 实际接收规模

| 数据 | 数量 | 身份与限制 |
| --- | ---: | --- |
| PoolC Python 已选代码对 | 30,000 | 公开 similar=0/1 各 15,000；本地关系未复核，许可待澄清 |
| 所选 Python 不同源码文本 | 29,280 | 原始源码文本，含 Python 2 或当前解析器不支持的形式 |
| XLCoST 七语言程序记录 | 57,661 | **预分词表示，不是可直接上传、解析、编译的原始代码** |
| XLCoST 不同语言/文本哈希 | 57,216 | 多个记录可能共享源码内容，不能当作独立作者样本 |
| XLCoST 跨语言候选对 | 30,893 | 题目标题对齐，不是已核对官方 ID 的平行关系正例 |
| 上述候选完全不含 Java | 20,713 | JavaScript 不属于 Java；包含 Python/C/C++/C#/JavaScript/PHP 组合 |
| 本轮正式评测资格 / 人工双审 | 0 / 0 | 不能将规模增长解释为正式 benchmark 完成 |

本轮登记 60,893 对，必须区分 30,000 对公开标签 Python 数据与 30,893 对未标注跨语言候选。加上此前 31,634 条公开/候选关系登记，累计登记行数为 92,527；这是不同来源的登记口径，不声称全局独立、全局关系复核或 problem-disjoint 样本数。91 对 synthetic seed 和 16 对自有开发探针不计入上述公开数据。

### XLCoST 各语言数量

| 语言 | 固定镜像实际程序记录 |
| --- | ---: |
| C++ | 11,198 |
| C# | 10,735 |
| JavaScript | 9,951 |
| PHP | 3,553 |
| Python | 10,622 |
| C | 574 |
| Java（跨语言对照） | 11,028 |

实际镜像的 Python/C# 数量与作者 README 总表有差异；以上统计来自固定输入逐行读取，未用网页统计替代实际数量，也未猜测或交换语言标签。C 的数量仍偏少。**下载 C++、JavaScript、C#、PHP 数据不代表当前检测服务支持这些语言。** 生产主范围仍是 Java/Python，C/HTML 仍是有限同语言实验分支。

## 来源、表示与许可

### PoolC

[发布页面](https://huggingface.co/datasets/PoolC/1-fold-clone-detection-600k-5fold)，固定版本 `c90e5302f9a4d306bacf278c08c043d5d7fa3e81`。只下载 train 的第一分片及 dataset_infos.json，实际扫描 **598,736 行**，不将整个发布库的行数冒充本地接收量。Parquet 为 228,306,945 字节，核对发布 LFS SHA-256；说明文件核对 Git blob。

similar 是发布者字段。正标签不能自动解释成派生改写，负标签不能证明独立作者；同题自然相似仍需题目、来源和人工复核。code1_group/code2_group 只按不透明发布组保存，不伪造成真实题目 ID 或作者家族。题目 ID、作者家族均为 null；选取关系保持 `experiment_label=UNCERTAIN`。

固定说明文件的 license/citation/homepage 为空，发布页面没有可据以确认使用条件的数据卡。**本地隔离，许可澄清前不再分发、不纳入正式指标、不自动送入校准或论文 benchmark。** 模型代码 MIT 等外部声明不能替代数据许可。

### XLCoST

[作者仓库](https://github.com/reddy-lab-code-research/XLCoST)与[作者数据格式说明](https://github.com/reddy-lab-code-research/XLCoST/blob/3a7b3d242cea9afb8d621cdb835df3a23f988056/metadata/synthesis/README.md)说明程序、片段及官方 problem-map。此次实际接收的是[公开 text-to-code 镜像](https://huggingface.co/datasets/codeparrot/xlcost-text-to-code)，固定版本 `60c5c133f043a5cffe162f9de1c62b9d88f309cf`，七语言 program-level 的 train/valid/test 共 21 文件及 README，逐个核对固定大小、LFS SHA-256 或 Git blob。

镜像保留 text/code，但没有作者说明中的官方 problem-map。因此只抽取 text 首段的**精确标题**，按“每语言标题唯一、只取 train、不跨 split、排除相同内容”构建待核对候选，不声称官方平行关系或完整语义等价。相同标题也可能过于笼统，仍需人工检查。每语言组合最多取 2,000 对，不使用检测分数。保留程序原始预分词形式，例如 NEW_LINE/INDENT/DEDENT；不随意逆分词，也不写成假 .py/.cpp 文件。

镜像数据卡声明 CC-BY-SA-4.0；作者工具仓库 Apache-2.0 不自动许可全部原始 GeeksForGeeks 代码。保留声明和来源，实际原始权利与用途需核对；下载源码与完整索引均保持本地 Git 忽略。仓库证据目录只保存来源、摘要和验证结果，不复制原始代码。

## 质量核查

PoolC 按换行归一文本哈希建立无方向内容对，排除相同文本，隔离冲突标签；此分片选取审计未发现冲突标签。每标签选取按 `SHA256(seed:ordered_text_hashes)` 排序，seed=20261010，完全不依赖检测分数。本分片有 1 个源码文本出现在多个不透明组，已记录；未下载验证集，不能声称完整 validation/test hash 隔离。

所选源码中 27,961 份通过 Python 3.12.14 语法解析，1,319 份解析失败，可能涉及 Python 2 或不支持语法。只做语法检查，不执行源码、不做功能正确性判断、不把失败转换为 AST/IR 证据。

XLCoST 上游记录为 train 50,168 / valid 2,642 / test 4,851；发现 23 个语言/文本哈希跨 split 重复。构建候选排除 1,207 个同语言标题歧义组、25 个跨 split 标题组、3 个涉及跨 split 源码哈希的标题组，以及相同内容和重复内容对。保留全部原始记录以便核对，不改写上游划分，也不把标题检查包装成作者/source-family 隔离。

## 本地文件与运行

```text
E:\ms\coderisk\data\public-datasets\
  poolc-20261010\
  xlcost-20261010\
    upstream\                 固定原始文件和发布说明
    source_registry.jsonl     身份、哈希、语言、来源、表示和资格
    source_codes.jsonl        一行一份原始记录代码，不逆分词
    selected_pairs.jsonl      公开关系或待核对候选引用
    audit_summary.json        实际数量、排除项和解析受限统计
    manifest.json             固定版本、输入哈希、seed、边界
```

source_registry 的 code_path 指向 source_codes.jsonl，code_line 为 1 起始行号，storage_format=jsonl-row。读取该行 JSON 的 code 字段获得代码文本，并核对 source_id 和哈希；不能把整个 JSONL 当一份源码。原始行还可按 upstream_file/upstream_row 定位。PoolC 原始 pair 行在固定 Parquet 的 upstream_row（1 起始）中保留。

从 `E:\ms` PowerShell 执行；其他机器用已安装项目依赖的 Python 替代 `$PY`，不要依赖本机旧 Store Python venv：

```powershell
$PY = '.\.tmp\language-venv\Scripts\python.exe'
$env:TEMP = 'E:\ms\.tmp\intake-fusion-temp-20261010'
$env:TMP = $env:TEMP
& $PY -m pip install -r coderisk\experiment\requirements-intake.txt
& $PY coderisk\experiment\acquire_nonjava_datasets.py --help
# 已有数据只验证，不覆盖；离线逐项重建源码、关系和统计：
& $PY coderisk\experiment\acquire_nonjava_datasets.py poolc --verify-only
& $PY coderisk\experiment\acquire_nonjava_datasets.py xlcost --verify-only
# 可选：固定缓存离线重建到尚不存在的新目录：
& $PY coderisk\experiment\acquire_nonjava_datasets.py poolc --offline --pairs 30000 --seed 20261010 --output output\poolc-replay
& $PY coderisk\experiment\acquire_nonjava_datasets.py xlcost --offline --per-language-pair 2000 --seed 20261010 --output output\xlcost-replay
# 完整 Python 回归；每次更换 basetemp 和 XML 名称：
& $PY -m pytest -q -p no:cacheprovider --basetemp .tmp\nonjava-tests-local --tb=short --junitxml output\nonjava-tests-local.xml
```

采集脚本在新机器没有缓存时才下载；它不运行远程 dataset loader。现有输出目录不覆盖；网络中断允许重试，缓存校验失败不自动换版本。工具失败时检查输出是否缺少最终 manifest，不将不完整接收当作成功。Parquet 阅读依赖只在实验接收 requirements-intake.txt，不影响服务运行依赖。

本机两个接收目录分别约 287.90 MiB（301,887,055 字节）和 230.56 MiB（241,763,044 字节），包括原始文件、源码表、关系表；缓存另占空间。

## 验证与下一步

Python 全量回归 **263 项通过**，其中本轮新增 24 项自有小型 fixture 测试；一个既有第三方弃用警告，无失败或跳过。验证固定输入、反向/内容去重、冲突标签隔离、不足 quota 拒绝、Python 2 解析失败披露、标题歧义/split 泄漏排除、JavaScript 与 Java 区分、不可覆盖输出及篡改拒绝。两批真实数据都通过离线重建核查。

[验证证据](../../coderisk/experiment/evidence/nonjava-intake-20261010/verification.json)和[数量摘要](../../coderisk/experiment/evidence/nonjava-intake-20261010/collection_summary.json)保留实际运行记录。生产服务、前端、Maven/JPlag/MySQL 本轮未重跑；MySQL 仍待有效凭据，不将 H2 历史验证冒充 MySQL 验证。

下一步先澄清 PoolC 使用条件、恢复 XLCoST 官方 problem-map 和可验证原始源码，再挑选 Java/Python/C 题目样例补题目画像、来源/作者家族和双人复核。其他语言先作为数据储备；C 样本仍需增加。准入后才能按真实题目及 source-family 做 validation/test 隔离并运行现有实验工具。现有公开标签不能支撑“动态阈值降低自然相似误报”的正式结论，也不能声称确认抄袭、检测 AI 生成或完整语义等价。
