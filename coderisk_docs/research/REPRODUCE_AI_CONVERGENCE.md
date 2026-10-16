# V0—V5 从零复现（Windows PowerShell）

无API token、无真实数据也能运行；不会网络生成、付费或执行代码。先装Python3.12、Java21、Node/Maven；生产启动沿用根README，离线实验不依赖HTTP服务。文件名、参数先`--help`，所有输出用新run ID，失败目录也保留。

## 安装与本轮可用环境

```powershell
# 项目根目录。新建环境，已存在时换名字，不覆盖用户旧环境。
python -m venv ./coderisk/analysis-service-python/.venv-ai-era
$Python = (Resolve-Path ./coderisk/analysis-service-python/.venv-ai-era/Scripts/python.exe).Path
New-Item -ItemType Directory -Force ./.tmp/ai-era-temp | Out-Null
$env:TEMP = (Resolve-Path ./.tmp/ai-era-temp).Path
$env:TMP = $env:TEMP
$env:PYTHONUTF8 = '1' # 避免Windows GBK解码中文Git文件名
$env:MPLCONFIGDIR = Join-Path $env:TEMP 'matplotlib'
& $Python -m pip install -e './coderisk/analysis-service-python[dev]'
& $Python -m pip install -r coderisk/experiment/requirements.txt
& $Python -m pytest -q -p no:cacheprovider
mvn -f coderisk/backend-springboot/pom.xml test
npm --prefix coderisk/frontend-vue ci
npm --prefix coderisk/frontend-vue run build
```

本机实际复用`.tmp/language-venv`的Python3.12.14，隔离PYTHONPATH指定Tree-sitter0.25.2；这是本机记录，不要求其他机器有同一路径。初跑中文Git状态GBK异常、修正UTF8后523基线通过，最终数值见测试摘要。

## 开发态完整管线

```powershell
$Run = 'ai-era-REPLACE-NEW-ID'
$Out = Join-Path './output' $Run
& $Python coderisk/experiment/ai_convergence/analyze.py --help
& $Python coderisk/experiment/ai_convergence/examples/make_seed.py --output "$Out/seed"
& $Python coderisk/experiment/ai_convergence/ingest.py `
  --input "$Out/seed/corpus.json" --output "$Out/intake" --no-network
# --dry-run / --validate-only 校验但不创建snapshot
& $Python coderisk/experiment/ai_convergence/validate.py `
  --input "$Out/intake/corpus.json" --output "$Out/validation.json" --no-network
& $Python coderisk/experiment/ai_convergence/analyze.py `
  --input "$Out/intake/corpus.json" --output "$Out/analysis" --no-network
& $Python coderisk/experiment/ai_convergence/jplag.py --help
# jar需你预先有权取得；工具不下载。没--execute只prepare，不冒称运行。
& $Python coderisk/experiment/ai_convergence/jplag.py `
  --dataset "$Out/analysis/dataset/dataset.json" --output "$Out/jplag" `
  --jar './coderisk/data/tools/jplag/jplag-6.2.0-jar-with-dependencies.jar' `
  --java "$env:JAVA_HOME/bin/java.exe" --execute --no-network
& $Python coderisk/experiment/ai_convergence/analyze.py `
  --input "$Out/intake/corpus.json" --output "$Out/analysis-aligned" `
  --jplag-dir "$Out/jplag" --no-network
& $Python coderisk/experiment/ai_convergence/prepare_review.py `
  --input "$Out/intake/corpus.json" --dataset "$Out/analysis-aligned/dataset/dataset.json" `
  --output "$Out/review"
& $Python coderisk/experiment/ai_convergence/export_public.py `
  --run-dir "$Out/analysis-aligned" --output "$Out/public-aggregates"
& $Python coderisk/experiment/ai_convergence/analyze.py `
  --input "$Out/intake/corpus.json" --output "$Out/formal" --formal --no-network
# 最后预期exit2/FORMAL_BLOCKED，metrics不生成；不是隐藏失败。
```

无JPlag时跳过两条相关命令，报告保留NOT_RUN；不要导入旧seed/ConPlag分数补新pair。实际本轮最终目录`output/ai-era-value-20261012/analysis-release`，此前analysis因直接入口模块与stdlib同名失败，原目录和红测保留，已修复并新增独立subprocess测试。

## 看哪些文件

`run_manifest/config/validation`核source/data/config hash、seed和0live calls；`scores`逐pair分量/完整C/指纹等同/缺失原因/耗时；`distributions`看题目/模型/prompt/长度/模板/功能分层的分母；`metrics/relation_metrics`当前null+NOT_ESTIMABLE，不是0准确率。`baseline_comparison_metrics`仅共同有效cohort，未匹配另列不补0。

`results.cluster`为test组件宏平均配对区间，少于6组件N/A；`failures`当前包括数据和功能未验证，不等于发生22次检测误判。`borderline`只能在有可用工作点时生成。`question_distributions.png`是描述性图；Full-fixed/Full-rule分数相同，阈值才不同。`context_evidence/submission_review/assignment_preflight`是只读原型，不是教师效益证据。

真实新集合按 [采集手册](LIVE_GENERATION_PLAYBOOK.md) 准備自己的corpus、许可/关系/功能/冻结config；当前schema/newadapter只支持同语言Java/Python，不接受跨语言IR替代当前比较。触发正式门禁以外错误退出非0须留日志、修复后换目录，不覆写。新开题及Go/No-Go见 [总决策](PICAS_GO_NO_GO_DECISION.md)。
