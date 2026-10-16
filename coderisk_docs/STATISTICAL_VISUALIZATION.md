# 描述性统计可视化与版权署名

更新：2026-10-16。项目原创代码/文档署名 **魏语石（weidonglang）**，MIT正文不变；LICENSE、README、桌面/手机页脚已同步。不填写或暗示软件著作权登记编号，第三方组件/数据仍按各自许可处理。

## 选型与边界

核对了 [Apache ECharts](https://github.com/apache/echarts)、[AntV G2](https://github.com/antvis/G2) 的官方仓库。本项目采用固定版本 **ECharts 6.1.0**，沿用Vue/Element Plus，不引入第二套界面框架。参考官方[按需引入](https://echarts.apache.org/handbook/en/basics/import/)、[尺寸与销毁](https://echarts.apache.org/handbook/en/concepts/chart-size/)、[可访问性](https://echarts.apache.org/handbook/en/best-practices/aria/)说明。

只注册Bar/Scatter/Heatmap/Boxplot、坐标/提示/色阶/参考线/Aria及SVGRenderer。统计分析面板和渲染模块分两层动态加载，普通结果列表不先请求ECharts运行时。库仍增加约584KB minified /199KB gzip的独立延迟分包；不是“零体积”或已解决旧主包体积问题。

所有新统计只在浏览器读取API返回值，不修改生产评分、动态阈值、风险分类、数据库或experimental权重。没有上传代码、CDN运行时请求、LLM调用或新核心检测算法。

## 分析口径

入口为任务结果的“分析”。`?view=analysis&plot=dimensions`或`plot=normalization`保留视图并支持刷新。图表对应**当前页筛选结果**，同时显示本页加载数和任务总结果数；如果当前页恰好覆盖全部已生成结果，会明确说明，仍不把代码对视为独立样本。失败/待处理代码对不是已生成观测。

| 图表 | 定义 | 不能推断 |
| --- | --- | --- |
| 综合分直方图 | 5/10个等宽区间；左闭右开，末组包含1；计数或占比；占比分母是有效综合分n | 不是密度拟合、时间趋势或来源概率 |
| Raw/Canonical散点 | x=Raw，y=Canonical，固定0–100%；虚线y=x；点可定位证据；重合点不抖动 | 参考线不是回归线，相关外观不证明改名关系 |
| 变化比例 | Canonical更高/基本相同/更低的共同有效代码对数；差值单位pp | 不是识别成功率，不加入风险分 |
| 多维热力图 | 每行一对代码，每列一个原分量；有效0绘制、缺失不绘制；点击色块查看证据 | 色阶不是相关系数，没有构建提交关系网络 |
| 分量箱线图 | 每分量独立有效n；箱体Q1到Q3，中线中位数，须线min/max | 不做1.5IQR异常判定，不假设分量独立 |
| 实验方法柱状图 | 原run的E1/E3/E4方法与F1/Recall/Precision/FPR/NaturalSimilar FPR；n同时显示，N/A不补0 | 同run不自动保证共同支持集合或正式标签资格 |

分数有效条件为有限number且在[0,1]；字符串、NaN、null、缺失和越界值不转换成0。各分量保留各自分母。HTML固定分支的结构分标为“HTML结构”，不冒充编程语言AST；CSV保留formula_version以区分API的astSimilarity字段语义。图表不把Raw/AST/Canonical/Mapping当作总和100%的“贡献饼图”。

## 分位数

有效分数先升序排列。对概率p，令h=(n−1)p、i=floor(h)，采用 `Q(p)=x[i]+(h-i)(x[ceil(h)]-x[i])` 的线性插值（R7口径，索引从0开始）。空集合返回缺失；单样本的描述值可以相同，但不构造虚假的离散性。

箱线图的n≥4是本界面的保守绘制门槛，不代表4个样本足以科研推断，也不声称更小集合不存在分位数。没有计算置信区间、显著性、因果或正式效果；代码对可共享同一提交，不能直接作为独立统计单位。

## 导出与异常

- 每张图可导出SVG；当前页原始分量可导出UTF-8 CSV，列名保留0–1单位及CURRENT_PAGE_FILTERED范围。
- CSV数值保持数值，缺失为空；不可信文件名以公式字符开头时加文本前缀，且正确转义逗号/引号。已用标准CSV解析器核对下载内容。
- 数值明细作为图表的可访问替代，包含各分量n/缺失/min/Q1/median/Q3/max及原始代码对。
- ResizeObserver处理容器变化，卸载时释放图表和observer。图表加载失败仍保留数值；显式刷新可恢复并保留分析直达链接。
- 实验数据未提供时保持空态，不填充漂亮的假柱状图。

## 验证与依赖

本轮Python591通过（1既有warning）、H2后端19通过、前端28单测（含10项新统计/语义口径）通过。HTML图表及数值表标签先红测再修正，保留失败记录。浏览器本轮125检查：原流程41、旧状态7、统计51、6份自编静态样例/15实际分析对9、直达/证据/实验图13、模块加载失败恢复4。拦截数据均为浏览器临时UI夹具，不写实验数据库，不计入benchmark；六份UI源码也不执行、不证明功能或来源关系。

运行时依赖公告初次命中6项旧包记录；在现有兼容范围更新Vue3.5.44、Axios1.20.0及相关传递包后，`npm audit --omit=dev`返回0项。完整audit多次TLS失败，不宣称全依赖安全审计通过；npm公告0也不是安全证明。旧PURE及主包/延迟包体积警告保留。

Windows测试浏览器观察到系统杀毒软件注入的额外请求；没有关闭防护，也不把这部分流量算成应用/CDN请求。测试仅记录数量，不公开请求完整URL/会话参数。本项目图表组件自身未发出外部数据请求。

本轮日志/失败、版本与截图见[统计可视化证据](../coderisk/experiment/evidence/statistical-views-20261016/README.md)。此前[第二轮结果证据](../coderisk/experiment/evidence/result-review-20261016/README.md)保留原日期，不重复累计为新增研究样本。依赖许可见[第三方说明](../coderisk/frontend-vue/THIRD_PARTY_NOTICES.md)，项目版权见[LICENSE](../LICENSE)。
