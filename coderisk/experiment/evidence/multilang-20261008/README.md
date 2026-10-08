# 多语言数据接收与解析覆盖证据

实际接收和检查日期：2026-10-08。完整说明见 [多语言进展记录](../../../../coderisk_docs/proposal/MULTILANGUAGE_PROGRESS.md)。

- `source_registry.json`：官方 URL、许可证来源、CodeNet 部分归档范围与 SHA-256、MDN 固定提交及逐文件哈希。
- `intake_summary.json` / `file_inventory.json`：366 份源码、10 份题面及相关登记/许可文件；清单共 382 个文件。源码与缓存位于被 Git 忽略的 `coderisk/data/public-datasets/multilang-intake-20261008`。
- `codenet_submissions.jsonl` / `mdn_submissions.jsonl`：来源编号、原文件位置、原始字节/文本哈希、无标签及禁止进入核心指标的标记。
- `source_parse_audit.jsonl` / `source_parse_audit_summary.json`：逐源码解析状态、规范化模式、失败原因、上游 C 目录中的 C++ 词法提示、运行依赖与实现文件指纹。

Java 107、Python 102、上游 C 111、HTML 46。C 中只有 72 份通过当前 C 语法解析；9 份含 C++ 词法提示，需要人工语言复核。不得称这 111 份全部已验证为 C。MDN 是教学参考源码，不是真实学生抄袭标注集。

CodeNet 仅接收 16 MiB 固定前缀，保留完整成员，完整归档尚未下载或验证。官方来源可信与单条语言/判题状态可信是不同的问题。所有新记录未计算代码对分数、未执行源码、无正负例标签，均不能进入正式效果统计。
