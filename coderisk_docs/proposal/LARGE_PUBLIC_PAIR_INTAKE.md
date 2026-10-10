# 大规模公开代码对接收记录

> 2026-10-11 统计修订：按当前实际 JSONL，早期公开/候选登记是 `911 ConPlag + 460 IR-Plag + 249 AD2022 = 1,620`，加本批 30,000 为 **31,620**，不是原文旧汇总 31,634。再加 PoolC/XLCoST，当前合计 **92,513 行**。源清单及标签未改；下方旧总量保留为历史记录，不再用于当前展示。逐行计数、文件 hash 和边界见 [当前核对](../../coderisk/experiment/evidence/readme-data-refresh-20261011/README.md)。

工作日期：2026-10-10。本轮响应“不少于两万对代码”目标，实际从固定的 Microsoft CodeXGLUE BigCloneBench 发布文件中接收并登记 **30,000 个互不重复的源码内容对**。没有组合已有源码凑数，没有生成新改写样例，没有运行相似度评分或下载的代码。

## 已落地的数据

| 口径 | 本轮实际数量 |
| --- | ---: |
| 下载并核对的原始公开代码对行 | 1,731,860 |
| 原始函数记录 | 9,126 |
| 不同函数字节/文本哈希 | 8,063 |
| 排除相同文本、去重后的跨 split 内容对 | 1,357,419 |
| 选取并登记的互异内容对 | 30,000 |
| 所选公开 label=1 / label=0 | 15,000 / 15,000 |
| 所选代码对引用的函数 ID | 7,276 |
| 本地真人双人复核 / 正式研究资格 | 0 / 0 |

30,000 对共享部分函数，不能理解为 60,000 份不同代码或 30,000 个独立题目。相同 ID、反向代码对和相同源码内容不重复计入所选数据。上游 1/0 是克隆任务的公开关系标签，不自动映射成“派生改写”“独立创作”或“自然相似”；本地 `experiment_label=UNCERTAIN`、`eligible_for_core_metrics=false`。

与此前 3,865 条公开源码版本登记及 467 条 IR-Plag 登记核对，本批源码字节哈希交集均为 0。公开池总计 13,458 条代码版本记录，按字节哈希去重为 12,163 份。显式登记的候选/公开关系代码对合计 31,634 对（此前 1,634 + 本批 30,000）；91 对 seed 与 16 对开发探针单独管理，未加入真实公开池统计。

本批本地接收目录全部文件合计约 103.8 MiB（108,888,570 字节）；缓存和其他数据集不计入该数字。大约 46 MiB 的固定输入下载同时保留函数表和代码对引用，因此无需下载重复嵌入源码的多 GB 镜像。

## 来源与许可记录

- [官方任务说明](https://github.com/microsoft/CodeXGLUE/blob/ac74a62802a0dd159b3258c78a2df8ad36cdf2b9/Code-Code/Clone-detection-BigCloneBench/README.md)：`data.jsonl` 包含 Java 函数，`train/valid/test.txt` 包含函数索引及二元标签。
- 固定提交：`ac74a62802a0dd159b3258c78a2df8ad36cdf2b9`。八个输入逐文件核对 Git blob SHA-1 和固定字节数，并保存实际 SHA-256。
- 官方仓库 README 声明数据采用 C-UDA、代码采用 MIT。固定版本的 `Data_LICENCE` 实际包含协议仓库的 CC0 文本；不将该文件或工具代码 MIT 自动解释为所有原始源码的再分发许可。固定原文和声明都在本地 `upstream/` 保留。
- 原始代码、下载缓存与完整代码对清单保持本地 Git 忽略；仓库证据目录只保存来源固定、统计与说明。

这是一批公开 Java 函数克隆数据，不是学生作业抄袭事实，也没有本项目验证过的完整语义等价结论。

## 质量审计与选择规则

上游 Train/Valid/Test 实际行数为 901,028 / 415,416 / 415,416。先扫描完整三份文件，核对每个函数引用，按换行归一后的文本哈希形成无方向代码对。

- 排除两侧相同源码内容，避免大量近乎恒等样例充数。
- **117 个内容对的公开标签冲突**在扫描中识别并从选取范围隔离。保留原始文件与统计，不修改上游标签。
- **1,723 个内容对跨上游 split 重复**；函数 ID 跨集合交集为 0，但 Train/Valid、Train/Test、Valid/Test 的文本哈希交集分别为 94 / 76 / 26。因此不能声称原始划分完全 hash-disjoint。
- 所选 30,000 对全部来自上游 train，每个公开标签取 15,000 对。候选按 `SHA256(seed:ordered_text_hashes)` 排序选最小值，seed=20261010，不使用检测分数。
- 数据登记为 `dataset_split=development`，不新造 validation/test。题目、作者和项目家族在该发布文件中不可恢复，记 unknown/null，不编造 ID。
- 平衡选取是开发采样策略，不代表真实教学中的正负比例；不能据此直接推断实际部署 Precision。

源码是函数片段，未加包装、未编译、未执行。Java 完整文件上传、规范化和 JPlag 的片段处理需要独立适配；本轮没有把函数片段静默包成完整程序，也没有将其送入默认生产评分。

## 本地文件和复现

代码入口：`coderisk/experiment/acquire_codexglue_bcb.py`。

```text
coderisk/data/public-datasets/codexglue-bcb-20261010/
  upstream/                固定函数表、代码对行、说明和许可原文
  sources/<idx>.java       原始 Java 函数片段
  source_registry.jsonl    源码身份、路径、字节及文本哈希
  selected_pairs.jsonl     30,000 对的身份、引用、公开标签及资格
  audit_summary.json       去重、标签冲突、split 重叠和选择统计
  manifest.json            来源版本、输入哈希、采样参数、边界
```

从仓库根目录 `E:\ms` 执行，先确认有效的 Python。下列 `.tmp` 解释器是本机已有测试环境，其他机器用已安装项目依赖的解释器替换：

```powershell
$PY = '.\.tmp\language-venv\Scripts\python.exe'
& $PY coderisk\experiment\acquire_codexglue_bcb.py --help
# 已有目录只验证，不覆盖：
& $PY coderisk\experiment\acquire_codexglue_bcb.py --verify-only
# 使用固定缓存离线重建到不存在的新目录：
& $PY coderisk\experiment\acquire_codexglue_bcb.py --offline --pairs 30000 --seed 20261010 --output output\bcb-offline-replay
```

校验会核对固定输入，重建全部选取关系和元数据，逐份核对实际源码。下载和导入要求新输出目录；缓存哈希变化必须报错，不自动更新版本。

统计快照：[manifest](../../coderisk/experiment/evidence/codexglue-bcb-intake-20261010/manifest.json) · [审计](../../coderisk/experiment/evidence/codexglue-bcb-intake-20261010/audit_summary.json) · [验证记录](../../coderisk/experiment/evidence/codexglue-bcb-intake-20261010/verification.json)。完整代码对清单在本机忽略目录，不复制进仓库。

实际离线重建验证通过；Python 全量回归 239 项通过，包含 15 项新增接收测试，保留一个既有第三方弃用警告。后端/前端/MySQL/浏览器链路本轮未复测，生产算法没有修改。

## 其他候选来源

| 来源 | 当前状态 | 适用性与待核对事项 |
| --- | --- | --- |
| [XLCoST 作者仓库](https://github.com/reddy-lab-code-research/XLCoST) | 后续增量已接收七语言 program-level 镜像 | 预分词表示、标题候选和官方 problem-map 缺失必须区分，见 [非 Java 接收记录](NONJAVA_PUBLIC_INTAKE.md)；不计入本次 BCB 数量 |
| [xCodeEval 作者仓库](https://github.com/ntunlp/xCodeEval) | 已查到，未下载登记 | 多语言题目数据；公开说明数据 CC BY-NC 4.0，不能用工具 MIT 替代数据条件；需控制下载规模并核实实际任务及判题元数据 |
| [CodeXGLUE POJ-104](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Clone-detection-POJ-104) | 已查到，未下载登记 | C/C++ 题目检索数据，不将同题自动当抄袭关系，也不将 C++ 当现有 C 子集支持 |

这些其他来源未加入本次 BCB 数量；后续 PoolC/XLCoST 接收单独统计。下一步优先补 Java/Python 编程作业题目、自然相似参考池及可追溯派生样例；BCB 规模可以支持外部克隆诊断，但缺少题目画像，不能用于证明 RQ1 动态阈值降低自然相似误报。
