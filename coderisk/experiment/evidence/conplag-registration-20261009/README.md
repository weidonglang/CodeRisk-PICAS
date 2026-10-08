# ConPlag 公开标签探索性评测：运行前冻结

客户端工作日期为 2026-10-09，实际冻结时间以 `protocol.json` 的 UTC 时间为准。本目录在取得本次数据集分数前生成，使用公开单人标注，不能替代正式毕设双人标注或学校认可的预注册。

- 911 对 Java；沿用接收阶段 seed=20261008 的题目分组：验证 284 对，测试 627 对。
- 原始源码与发布者去模板源码作为同一批样本的两个视图，不累加样本量。
- 固定融合、移除规范化和映射、原始 Token、规范化单指标、JPlag 6.2.0；各方法仅按验证集选择阈值。
- 题目、已知提交家族、两个视图的文本哈希跨集合重叠均为零；作者身份未知，不能声称按作者隔离。
- 分别报告 PICAS 全集合和 JPlag 原生输出共同集合；缺失分数不补零，报告排除原因。
- 测试集按题目进行 1,000 次 bootstrap。该区间只描述本批公开题目的变化，不能消除单人标签偏差。
- 缺少题目画像和自然相似标签，本次不评价动态阈值，也不评价自然相似子集误报率。
- `protocol.json` 固定了程序、依赖、JPlag、样本与划分哈希。改动注册内容或实现会被运行器拒绝。

在仓库根目录运行（依赖安装及原始公开数据接收步骤见项目文档）：

```powershell
python coderisk/experiment/run_published_conplag.py --registration coderisk/experiment/evidence/conplag-registration-20261009 --output coderisk/data/public-datasets/conplag-pilot-20261009
```

Java 可执行文件默认使用当前 Windows 环境路径，可通过 `--java` 指定 Java 21。下载源码、JPlag 输入及含源码的报告均留在被忽略的目录；这里仅保存元数据。执行的是分析器和 JPlag，不编译或运行下载的作业代码。
