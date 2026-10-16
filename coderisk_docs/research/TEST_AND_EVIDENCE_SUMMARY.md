# V0—V5 实际测试与证据摘要 · 2026-10-12

这是本轮运行，不引用旧523/19/build冒充本轮。main/HEAD `892e7ef4a0d2f016cc8b0713fc7b347bd9e1717f`，开始时197个修改/未跟踪文件；129生产文件、1492历史文件已记录SHA。没有commit/push、API、DB或生产源码修改，最终保护检查在新evidence/verification.json。

## 实际命令与结果

Python使用`E:/ms/.tmp/language-venv/Scripts/python.exe`（3.12.14），`PYTHONPATH=E:/ms/.tmp/opening-tree-sitter-0252-20261011`锁定0.25.2，workspace TEMP/TMP，`PYTHONUTF8=1`、matplotlib Agg。每次pytest另用basetemp和JUnit输出，以下共同前缀为`output/ai-era-value-20261012/baseline/`。

| 命令/记录 | 真实stdout摘要 | exit | 范围 |
| --- | --- | --- | --- |
| `python -m pytest -q -p no:cacheprovider` → python.log/xml | 522passed/1failed/2warnings，32.07s；Git中文状态GBK解码线程失败 | 1 | 本轮初始既有基线 |
| 同命令，UTF8 → python-r2.log/xml | 523passed/1warning，30.74s | 0 | 当前基线，不改旧工具 |
| 新protocol测试 → protocol-red.* | 26passed/10failed，3.70s；Windows字节hash/CRLF及尚未完善边界 | 1 | 新代码开发失败，不是10个生产缺陷 |
| protocol-green.* | 36passed，5.08s | 0 | 初版协议；后续扩展在全量验收 |
| 新两文件 → analysis-tests.* | 50passed/2failed，16.55s；mode映射/具体告警缺失 | 1 | 已修正离线adapter |
| analysis-tests-r2.* | 52passed，9.34s | 0 | 中间版本 |
| 直接CLI analyze → analyze.log、cli-red.* | stdlib statistics被同名模块遮蔽；subprocess红测1failed，2.57s | 1 | 模块更名descriptive_stats并添加干净入口测试 |
| privacy-red.* | 未拒绝真实raw工作台写入公开/任意目录，1failed，2.15s | 1 | UNIT_TEST_ONLY隐私模拟，已共享private-output门禁 |
| python-final.* | 588passed/1warning，47.71s | 0 | 中间版本 |
| python-final-r2.* | 589passed/1warning，48.78s | 0 | 后加隐私契约版本 |
| python-release.* | **590passed/1warning，46.24s**，JUnit与原始log一致 | 0 | 关机前版本，相对523基线新增67项契约 |
| resume-validation/python.* | 589passed/1failed/1warning，63.25s；隐私测试将allowed output里的basetemp误当非法目录 | 1 | 测试夹具位置依赖，不是生产门禁绕过 |
| resume-validation/privacy-green.* | 2passed，1.32s | 0 | 隔离测试根，并新增允许/解析逃逸检查，门禁源码不改 |
| resume-validation/python-final.* | **591passed/1warning，61.37s** | 0 | 恢复后最终工作树，相对523基线新增68项 |
| `mvn test` → maven.log | H2 19tests/0fail/error/skip，BUILD SUCCESS，总16.356s，测试8.883s | 0 | Java21/Maven3.9.10，非MySQL |
| `npm --prefix coderisk/frontend-vue run build` → frontend.log | vue-tsc/Vite成功，1699modules，5.11s；旧PURE/chunk warnings保留 | 0 | 不等于浏览器E2E |

完整pytest参数可按 [复现手册](REPRODUCE_AI_CONVERGENCE.md) 加`--junitxml`与新`--basetemp`；原日志/JUnit及实际操作清单在本轮归档。Starlette/httpx既有warning不隐瞒。Maven日志的timeout/retry ERROR/WARN是已有恢复测试，不是失败；Mockito/H2警告保留。第一次本地jar manifest按UTF8读取失败，版本字段按ASCII兼容读取实际为6.2.0，没有假报其他版本。

## 实验命令（根目录；本机$Python指向上述环境）

```powershell
& $Python coderisk/experiment/ai_convergence/examples/make_seed.py --output output/ai-era-value-20261012/seed
& $Python coderisk/experiment/ai_convergence/ingest.py --input output/ai-era-value-20261012/seed/corpus.json --output output/ai-era-value-20261012/intake --no-network
& $Python coderisk/experiment/ai_convergence/jplag.py --dataset output/ai-era-value-20261012/analysis-r2/dataset/dataset.json --output output/ai-era-value-20261012/jplag --execute --no-network
& $Python coderisk/experiment/ai_convergence/analyze.py --input output/ai-era-value-20261012/intake/corpus.json --output output/ai-era-value-20261012/analysis-release --jplag-dir output/ai-era-value-20261012/jplag --no-network
& $Python coderisk/experiment/ai_convergence/analyze.py --input output/ai-era-value-20261012/intake/corpus.json --output output/ai-era-value-20261012/formal --formal --no-network
& $Python coderisk/experiment/group_action_properties.py --output output/ai-era-value-20261012/properties --seeds 20261011 73 901 --variants 48 --javac D:/DevEnvManager/envs/jdks/temurin-21/bin/javac.exe
& $Python coderisk/experiment/diagnose_fusion.py --output output/ai-era-value-20261012/conplag-readonly
```

已有目录不能重跑覆盖，以上是**执行记录**，复制复现时替换run ID；最初非对齐analysis直接入口失败，中间r2/aligned/final及最终release分开保存。当前13自有artifact/12mock会话/22pairs都是DEVELOPMENT_ONLY；native19匹配、共同14，准确率N/A。正式exit2为预期阻塞；review真实参与者/审核0。group properties再次1728/1728，其他10种状态不计成功，6次javac不执行；旧ConPlag读取两view各911、0重评分/拟合，负结果保留。

## NOT_RUN 与不能推论

真实模型/API调用、真实学生新增、真人双审、教师效益研究、功能执行、MySQL实库、当前浏览器E2E、Dolos均NOT_RUN。Python模块没有live网络实现；native为本地静态CLI，未做网络抓包/OS层隔离认证，不将0显式调用当全系统网络证明。所有模型mock是手写fixtures，不是生成成绩；仅合成图已实际查看，不能叫真实多模型趋同。

代码/hash/配置/split通过只说明声明一致，不认证授权/身份/独立性。formalEligible=0、不够cluster的CI=null、FPR/F1/AP=null都是正确失败处理，不该改成0或漂亮百分比。最终路线是INSUFFICIENT_EVIDENCE及条件PIVOT建议，不给GO。
