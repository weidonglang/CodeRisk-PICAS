# Statistical visualization and owner credit · 2026-10-16

本轮是展示与工程验证，不是新的相似度算法、正式benchmark或科研效果结论。项目原创版权署名 **魏语石 (weidonglang)**，MIT许可正文保持原样；第三方数据和组件保留独立许可，不添加软著登记号。

## 本轮内容

任务结果的分析分支：直方计数/占比、Raw/Canonical散点与变化比例、热力图/min-max须线箱线图；实验页同run方法图；SVG/CSV/数值明细、缺失/小样本空态、query直达、失败保留数据并刷新恢复。ECharts6.1.0按需分包，普通列表不请求其运行时。

所有评分/阈值/分类仍读原API。描述性统计在浏览器进行，分位数明确线性插值；缺失不补0、占比分母是有效n、代码对不假设独立。n≥4绘箱是UI保守策略，不是研究充分性声明。

## 真实验证

| 检查 | 实际结果 |
| --- | --- |
| Python | 591 passed，1既有warning，20.50s |
| Maven | H2，19 tests，0失败/错误/跳过；总14.313s |
| 前端单测 | 28通过，新增10项分位数/分箱/缺失/比例/CSV/HTML语义口径 |
| 类型检查/生产构建 | 2313模块，通过；各次耗时见日志，旧PURE及大chunk警告保留 |
| 浏览器原链路回归 | 41通过，创建→上传→任务→证据→HTML |
| 浏览器旧状态 | 7通过，临时拦截，不写库 |
| 统计/导出/四种宽度/署名 | 51通过，含HTML数值表语义，临时固定UI夹具，不写库 |
| 实际六源码/15对联调 | 9通过，自编静态UI样例，不执行源码 |
| 直达/真实证据/实验图 | 13通过，真实自有跳转与临时实验夹具分别说明 |
| 模块失败/恢复 | 4通过，保留数值并刷新恢复分析链接 |

浏览器共125检查不是125独立程序或研究代码对。标准CSV解析器另核对12行临时导出：公式前缀转义、真实0保留、缺失为空、当前页scope及formula_version保留。

真实截图来自隔离H2第7号任务的六份自编样例及15对实际静态分析。不同聚合操作不声明功能等价，没有关系标签，不计入公开登记量或核心实验。原链路回归新增第8号自有题/两提交/一对结果。没有真实学生、执行源码、收费调用或MySQL实库操作。

## 命令与输出

```powershell
npm --prefix coderisk/frontend-vue test
npm --prefix coderisk/frontend-vue run build
python -m pytest -q -p no:cacheprovider --junitxml output/python.xml
mvn --batch-mode -f coderisk/backend-springboot/pom.xml test
npm --prefix coderisk/frontend-vue audit --omit=dev --json
```

替换成本机可用Python/JDK，从仓库根执行。Playwright CLI脚本在 `coderisk/frontend-vue/tests/`；执行前看`--help`并准备脚本对应输出目录，只对自有隔离库运行真实写入脚本，同会话串行执行。原日志在 `output/statistical-views-20261016/`，截图/CSV/SVG在 `output/playwright/statistical-views-20261016/`；本目录保存精选日志、检查JSON及哈希。

## 不隐瞒失败

- 首轮新依赖图表等待超时，未据此断言具体根因；后续实际绘制/加载失败恢复与重跑通过。
- 图表SVG与按钮SVG选择混淆；热力图CSS hex与实际RGB序列化不同；中心文字挡住路径测试点击，改按真实色块区域验证跳转。
- 测试在下拉离场动画尚未结束时测到临时页面宽度，等待浮层隐藏和ResizeObserver后四种宽度通过；图表容器也保持宽度裁剪，不掩盖数据。
- 新query保留视图后，测试仍假定刷新回分布；明确选择分布后重跑缺失空态通过。
- HTML分支结构分被通用AST标签误称，图表及数值明细表分别先复现红测，再统一采用HTML结构标签，CSV保留公式版本上下文；不修改后端字段或分数。
- 依赖公告首次TLS失败，重试得旧包6项记录；兼容范围更新后生产audit0项。完整audit仍有TLS失败，不宣称全依赖安全。原始网络错误保存在本地输出，公开记录不含杀毒注入的完整URL/会话参数。

本机系统防护注入了浏览器额外请求；未关闭防护，只区分其计数与应用外联。图表组件自身没有CDN/模型服务外传。公告0、自动化检查、SVG图形均不是完备安全证明、效果证明或合法关系结论。

## 依赖与版权

ECharts6.1.0固定引入。原有兼容范围更新为Vue3.5.44、Axios1.20.0、PostCSS8.5.30、nanoid3.3.20、source-map-js1.2.2，完整版本锁在package-lock；未使用force或主版本升级。运行时分包约584KB/199KB gzip，仅在统计/实验图需要时加载。

[统计口径](../../../../coderisk_docs/STATISTICAL_VISUALIZATION.md) · [第三方许可](../../../frontend-vue/THIRD_PARTY_NOTICES.md) · [项目MIT](../../../../LICENSE) · [测试报告](../../../TEST_REPORT.md)。MySQL、真实模型、真人关系标注和教师效益未因本轮完成；历史研究证据保持原字节及日期。
