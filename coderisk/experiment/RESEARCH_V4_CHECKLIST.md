# Research V4 Checklist

## 数据补充前检查

- [ ] 已阅读 `experiment/datasets/research-v4/DATA_COLLECTION_GUIDE.md`。
- [ ] 已确认新增数据不是 synthetic seed 的重命名包装。
- [ ] 已决定每道题进入 `validation` 还是 `test`，且 split 在分析前预注册。
- [ ] 已为每道题分配唯一 `problem_id`。
- [ ] 已为同一原始代码家族分配同一个 `source_id`。
- [ ] 已确认代码来源、授权、许可证或自建说明。
- [ ] 已确认 AI-assisted rewrite 不是 placeholder，或明确标为 placeholder 且不进核心指标。
- [ ] 已确认不会把真实学生代码无授权放入仓库。

## 数据补充后检查

- [ ] 代码文件放在 `experiment/datasets/research-v4/samples/` 下。
- [ ] 使用 `add_research_v4_case.py` 预览过 manifest entry。
- [ ] `pending_confirmation_fields` 为空后才使用 `--append`。
- [ ] 新增条目已写入 `pairs/manual_pairs.json`。
- [ ] `eligible_for_core_metrics` 与 `source_type` 一致。
- [ ] placeholder 没有进入核心指标。
- [ ] AI_REWRITE 有 model、prompt、generation_time、manual check、functional check。
- [ ] external 有来源、许可证、链接或本地来源说明。
- [ ] 运行 validator 后 `valid=true`。
- [ ] problem/source/exact-code overlap 都为 0。

## 运行实验前检查

- [ ] `$PY` 指向可用 Python 解释器。
- [ ] Java 21 路径可用。
- [ ] `configs/experiments/research_v4.json` 指向正确 manifest。
- [ ] 如需 JPlag，对齐 baseline 已准备或配置仍指向可解释旧产物。
- [ ] run id 是新的不可变名称。
- [ ] 没有根据 test 结果修改阈值、标签或 split。
- [ ] 明确本轮是否只是 seed/pre-experiment。

## 运行实验后检查

- [ ] `run_manifest.json` 存在。
- [ ] `metrics_summary.json` 存在。
- [ ] `research_report.md` 存在。
- [ ] `dataset_validation/validation_report.json` 中 `valid=true`。
- [ ] `productionFormulaChanged=false`。
- [ ] `experimentalMetricsProductionWeight=0.0`。
- [ ] `calibrationTestUsedForSelection=false`。
- [ ] `paper_tables/` 表格已生成。
- [ ] `case_analysis/` 包含 failure、borderline、common_structure、unsupported_syntax 文件。
- [ ] JPlag 排除原因已记录。
- [ ] 失败案例没有被删除或隐藏。

## 论文写作前检查

- [ ] 已区分 seed 结果、exploratory observation 和正式 test 结果。
- [ ] 未把 synthetic seed 写成真实 benchmark。
- [ ] 未把 placeholder AI_REWRITE 写成 verified AI-assisted 数据。
- [ ] 已报告 dynamic threshold 的 recall trade-off。
- [ ] 已报告 common_structure 误报和 unsupported_syntax 漏报。
- [ ] 已写 threat to validity。
- [ ] 已写 limitations。
- [ ] 每个结论都能追溯到 CSV/JSON/Markdown 文件。
- [ ] 未使用“确认抄袭”“证明作弊”“完整语义等价”“AI 代码检测”等越界表述。

## 答辩演示前检查

- [ ] 后端、分析服务、前端健康检查通过。
- [ ] V0-V3 主链路可演示：题目创建、上传、任务启动、结果、证据、报告。
- [ ] Research V4 实验页或结果目录可打开。
- [ ] 展示的是相似风险和人工复核建议，不是抄袭判定。
- [ ] 准备好解释 seed 数据和真实数据缺口。
- [ ] 准备好解释为什么 V4 experimental 不进入 PICAS_STANDARD。
- [ ] 准备好展示 failure/borderline case。

## 软著材料准备检查

- [ ] 软件名称、版本、运行环境已整理。
- [ ] README 和启动说明完整。
- [ ] 核心功能截图覆盖题目、上传、任务、结果、证据、报告。
- [ ] 数据库表和 API 能对应系统功能。
- [ ] 不把实验性跨语言 IR 写成稳定产品能力。
- [ ] 不在软著材料中出现学术不当结论。
- [ ] 源代码整理不包含未授权真实学生数据。
