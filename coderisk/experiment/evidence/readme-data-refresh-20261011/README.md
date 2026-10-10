# README 数据与版式核对 · 2026-10-11

本记录只核对当前接收清单、README 表述和本地渲染，不是新的检测准确率实验。未执行第三方源码、修改关系标签、上传代码或调用付费模型。

## 当前登记量

| 当前清单 | 登记行 | 正式核心资格为 true |
| --- | ---: | ---: |
| CodeXGLUE / BCB selected_pairs | 30,000 | 0 |
| PoolC selected_pairs | 30,000 | 0 |
| XLCoST selected_pairs | 30,893 | 0 |
| IR-Plag published_pairs | 460 | 0 |
| ConPlag v3 published_pairs | 911 | 0 |
| AD2022 candidate_pairs | 249 | 0 |
| **合计** | **92,513** | **0** |

逐行解析六份 JSONL，各清单内部 pair_id 均无重复，文件路径与 SHA-256 见 [data_inventory.json](data_inventory.json)。仅选择每个来源的当前清单，不重复累计旧接收、重建快照或同一对的去模板视图；没有宣称跨来源源码去重、统计独立或 problem-disjoint。

旧总计 92,527 多计 14 行，旧 Java 加早期来源小计 31,634 应为 31,620。这里只更正汇总，未改源文件。原接收文档和历史证据保留，其页首新增当前口径提示。

- 大规模已选 Java / Python 共 60,000 对；发布标签不等于本地核实关系，PoolC 许可仍待澄清。
- XLCoST 是 30,893 对标题对齐候选、57,661 条七语言预分词程序记录，不是原始源码或已核验平行解答；语言数量沿用本地接收审计，不执行逆分词。
- 91 对 synthetic seed、16 对开发探针和 1,225 对合成性能联调不计入公开池。1,225 来自 50 份提交的两两枚举，并不是整个项目的数据规模。
- 92,513 是登记行总量，不是可信关系 benchmark 或已运行实验量。最新 README 单独列出 ConPlag 911 对探索与 synthetic seed 实跑。

## 复现计数

从仓库根目录执行，先准备 Node.js。第三方下载数据不随仓库发布；缺少清单时会明确报错。输出目录必须不存在。

```powershell
node ./coderisk/experiment/evidence/readme-data-refresh-20261011/audit_data.mjs ./output/readme-inventory-new
Get-Content ./output/readme-inventory-new/data_inventory.json
```

脚本是这次六份固定清单的日期快照核对器，不会自动扫描其他版本；未来增加来源或替换清单应更新统计范围并创建新的日期记录。当前合计不同或发现重复 ID 时返回非零退出码，不能把旧数字继续当最新结果。

## 文档与渲染检查

根 README 提前展示数据规模，保留截图、启动步骤、研究方法、消融不利结果与局限；将接收数据、代码素材、上游审计量、实际实验分开呈现。同步子项目 README、文档导航与两份接收说明的当前口径。

本地预览使用 Marked 与 Chrome / Playwright，在桌面 1440px、窄屏 390px 检查图片、链接和页面横向溢出。它不是 GitHub 线上页面，也不是业务浏览器端到端。检查结果见 [preview_checks.json](preview_checks.json)，截图见 [桌面](desktop.png)、[窄屏](mobile.png)、[数据概览](desktop-data.png)。宽表格在窄屏内横向滚动，不扩大整页宽度。

本次仅文档、统计辅助与证据变更，未重跑 pytest / Maven / Vite 或大规模检测。README 中 Python 431、H2 19、前端 build 通过是最近开发轮的已有记录，不冒充本次新测试；MySQL 实库仍未验证。生产公式、算法、API、数据库与 experimental 权重未改。没有自动推送远端。
