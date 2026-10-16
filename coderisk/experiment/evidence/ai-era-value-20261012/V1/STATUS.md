# V1 STATUS

DONE（离线）：分离questions/sessions/artifacts/provenance/pair relations/course policy；生成六schema；hash、越界、会话捕获、重复/未知、共享上游、family/parent/hash连通泄漏和private-output门禁；原loader桥接，不产生真人标签。

实际make_seed/ingest成功，13自编artifact、12mock capture全部synthetic，构对22。首次protocol红测10失败保留，CRLF按实际byte hash修正；后续schema/功能与来源分离契约进入最终全量。

BLOCKED：真实会话/许可/独立性，网络/live API不存在。模拟不能转成真实。字段与手工动作见 [采集手册](../../../../../coderisk_docs/research/LIVE_GENERATION_PLAYBOOK.md)。下一步已推进V2。
