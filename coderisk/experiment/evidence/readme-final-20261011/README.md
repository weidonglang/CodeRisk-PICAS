# README 最终整理与本地渲染检查

2026-10-11。保留封面、真实结果截图、工作流图、启动步骤、历史测试和 ConPlag 负结果；将旧日期流水移到数据与折叠研究记录，新增最新状态、阶段 4–5 入口、门禁、伦理及真实模型未验证说明。

## 检查范围

- `checks.json`：用 bundled Marked 17.0.5 与 Playwright/Chrome 本地渲染，不是线上 GitHub 页面，也不是业务端到端复测。76 个本地链接可达，4 图片加载；390px 视口/document 同为 390px，表格仅在内部横向滚动。
- `desktop.png` / `mobile.png` / `desktop-evidence.png`：实际渲染截图；仅验证文档排版，不代表新浏览器业务验证。
- `preservation.json`：759 个非本轮路径的 Git index 条目与阶段 4 前快照完全相同。共享文档用精确补丁提交，根 README 按用户要求整体整理；没有 reset、clean、push。
- FORMULA_SPEC、canonicalization.py、token_similarity.py 的 SHA-256 与阶段前完全相同；V4 权重/生产阈值/API/数据库未改。

四份已有说明在本地存在、可达，但在本次检查时尚未进入 HEAD：AI_REVIEW_HARDENING、LARGE_PUBLIC_PAIR_INTAKE、NONJAVA_PUBLIC_INTAKE、INTAKE_AND_FUSION_DIAGNOSTICS。保留 README 的来源/历史导航，没有擅自提交它们及相应其他任务源码。发布到 GitHub 前需一并处理这些已有 pending 文档，否则远端对应链接暂不可达。

本轮真实工程测试：全工作树 Python 431 项通过、后端 H2 19 项通过、前端类型检查/build 成功；阶段 4–5 隔离源码树 54 项通过，见 [验证证据](../hybrid-review-20261011/README.md)。新增网络调用/费用为 0；MySQL、真实 LLM 效果、真实混合效果未验证。

阶段提交：`efe84da` 离线 Direct LLM 协议，`a7c8ddf` 混合候选门禁。本目录与根 README 单独作为最终文档提交，不包括其他 pending 代码。
