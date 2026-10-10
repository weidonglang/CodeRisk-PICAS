# 群作用下的有限标识符规范化

日期：2026-10-10。对应 `canonicalization.py`、`experiment/identifier_renaming.py` 和三个新增测试文件。状态是**条件命题/证明草图 + 有限实现测试**，不是完整语言的机器证明。生产公式未修改。

## 1. 对象、群与作用

为避免把任意程序变换称为群，先固定以下条件：

- N 是一个有限、固定的合法 ASCII 标识符拼写域，可以包含尚未使用的名称；不含关键字、内置名称、导入名称、成员/API 名称和固定类/文件名。
- F 是必须固定的外部名称集合，N 与 F 不相交。任何 N 中的拼写出现，都必须已确认为可重命名的绑定声明、引用或已解析的直接调用参数标签，不能是未解析的自由名称。
- 程序集合 P 只包含下面限定语法、固定非名称 token 与固定词法绑定图下的程序及其允许变体；字符串、属性、导入和运行时动态名称访问不能被当作词法绑定。
- G = Sym(N)，即 N 到自身的全部双射，扩展为 F 上的恒等映射。`g·P` 同时替换所有选定绑定位置；具有相同拼写的内部绑定一起替换。因此保留原先名称相等/不等关系及遮蔽，避免与固定外部名称冲突。

这里采用的是**统一拼写置换的受限子群模型**，不涵盖所有逐绑定合法 alpha-renaming。任意一组局部重命名操作未必在固定程序域上对复合/逆封闭，不能直接称为置换群。字段和遮蔽局部变量分别改成不同名称的回归测试是附加绑定正确性检查，不是该统一 G 的实例。

恒等映射不改变源码；双射的逆可撤销改名；`h·(g·P) = (h∘g)·P`，其中 `(h∘g)(n)=h(g(n))`。这些结论依赖上述允许位置和程序集合对 G 封闭的条件，不是任意 Python/Java 程序的性质。

删除/插入语句、表达式交换、语句重排、函数拆分不属于 G。字符串中的名称不会随 g 改动；若程序以字符串查询名称，该输入不在该命题范围内。

## 2. C 和条件不变性命题

C(P) 是 `CanonicalAnalysis.tokens` 的**完整有序规范 token 序列**，不是 n-gram 集合指纹、映射分数或融合总分。实现按声明遍历顺序、角色计数器和结构作用域路径生成内部名称，通过原始 token 行列写入覆盖；保留非内部名称 token。源码行列、rawName 和映射 evidence 是原文复核元数据，不要求在改名后字节相等。

**条件命题**：如果索引器在 P 上正确识别全部选定绑定，作用域路径/角色/声明顺序与名称拼写无关，且 g 满足上述域、保护和捕获规避条件，则 `C(g·P)=C(P)`。

证明草图：g 不改变语法树的非名称部分和声明遍历顺序；双射及外部名称固定使解析的绑定图不变。依作用域遍历归纳，对应声明得到相同的角色编号和路径；声明、引用及直接调用标签因指向对应声明而写入相同内部 token。其余 token 原样保留，故有序序列逐项相同。

**尚未证明的实现义务**是整个语言子集上绑定索引器完全正确。当前证据验证有限 fixture，并不使 `scope-aware-python/java` 模式自动成为上述前提已满足的证书。生成器的位置准入使用了生产绑定索引，因此不是完全独立的符号解析 oracle；重写机制使用 Python tokenize，另外校验语法、逆与复合关系，Java 另做有限 javac 编译。

Python 的作用域与默认表达式/调用规则依据 [Python 3.12 execution model](https://docs.python.org/3.12/reference/executionmodel.html) 和 [calls](https://docs.python.org/3.12/reference/expressions.html#calls)；Java 的字段/局部作用域区分依据 [JLS 21 第 6 章](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html)。语言规范不替代本项目实现验证。

## 3. 支持与不支持边界

| 范围 | 本次实现与证据 | 不保证的情况 |
| --- | --- | --- |
| Python 内部函数、参数、局部及嵌套遮蔽 | 简单赋值/控制结构，默认值在外层解析，lambda 独立作用域；内部直接函数的普通/keyword-only 参数标签绑定到 callee 参数 | 运行时派发、隐式反射、任意外部代码行为、Unicode 兼容名称正规化未全面验证 |
| Python 关键字调用 | 可唯一解析的未装饰、未重定义/重绑定内部函数；延迟解析支持模块函数前向引用 | alias/attribute 调用、`**kwargs`/展开、装饰器、重复定义/重绑定、positional-only 名称当 keyword，返回 located warning 并 raw 回退 |
| Python 外部名称 | 固定内置/导入/属性名称；未知外部调用的参数标签保持 literal，不推断签名 | 不保证外部名称可改名；不能由 unknown signature 推断合法变换 |
| Python 动态名称 | globals/locals/eval/exec/vars/getattr 等已知名称及反射属性整文件回退，保存动态函数别名也拒绝 | 静态黑名单不能穷尽所有运行时动态访问；外部封装/间接动态访问仍是局限 |
| Java 探针子集 | 固定 Main 类；简单 primitive 方法/参数/局部、花括号 if 分支，保留 System.out.println | 重载、泛型、继承、反射、复杂限定成员、完整类型/符号解析没有保证 |
| Java 声明点 | 字段在局部声明之前可见；局部不得捕获其声明前引用，已有单独回归 | 无花括号 for/catch 作用域等尚不完整；生成器拒绝 for/catch/new/record/方法引用等，不代表算法已经逐项拒绝所有这些形式 |
| 失败回退 | Python unsupported/parse、Java 不平衡/空/未终止输入：raw tokens、空 identifiers、reason | Java 花括号检查不是完整语法解析；不能保证发现所有 Java 语法错误 |

已有 Python 推导式、global/nonlocal、模式/异常捕获、注解、类型参数等回退仍保留。C/HTML 既有实验支持未进入本群命题，也未被本次扩大或移除。API 的原文 warning/evidence 结构不变；有效基础 AST 可单独展示，但规范化不可用时不伪造 canonical 或 mapping evidence。

## 4. 具体验证和反例

测试路径均位于 `coderisk/analysis-service-python/tests/`：

1. `test_direct_function_keyword_labels_follow_parameter_bindings`：`combine(first=2, second=3)` 随定义一起改成 `merge(left=2, right=3)`。修复前 C 不同；修复后 C 相同，参数声明、体内引用和调用标签属于同一个 scopedCanonicalName。
2. `test_forward_and_nested_keyword_calls_have_structural_callee_bindings`：outer 内调用稍后定义的模块函数 inner，其 `item=` 标签随 callee 参数改名；修复后相同。
3. `test_java_field_reference_before_local_declaration_does_not_capture_future_local`：`int first=value; int value=2;` 中前后 value 对应不同绑定；修复后分别改成 field/local 的序列相同。
4. `test_dynamic_namespace_access_in_any_scope_is_explicitly_unavailable`：`globals()['value']` 的字符串查名、`eval('value')` 或 `ns=globals` 是反例/受限输入，不能假设词法替换保持行为；返回 `PYTHON_DYNAMIC_NAME_ACCESS_UNSUPPORTED`，不生成映射。
5. `test_unresolved_keyword_dispatch_does_not_guess_parameter_mapping`：alias、属性调用、装饰/重绑定、keyword 展开等明确回退。`test_generated_identifier_renaming.py` 拒绝非双射、越域、固定库名或自由名称进入域。
6. `test_insertion_is_not_a_rename_action_or_invariance_contract`：插入 unused 声明可改变 C；不是命题失败，因为不是 G 中的变换。
7. `test_production_score_is_not_claimed_invariant_when_raw_tokens_change`：canonical=1，但 raw 和 weighted 均小于 1。证明对象不是 PICAS 总分，更不是抄袭或完整语义关系。

## 5. 真实运行记录

[归档证据](../../coderisk/experiment/evidence/identifier-invariance-20261010/README.md)包含完整 fixtures、每个变体、源码/配置哈希、汇总及实际 JUnit：

- 首批修复前：18 项中 14 失败、4 通过，保留 corrected fixture 的 red-r2 JUnit；其后新增的 4 项保守回退测试不冒称修复前已运行。
- 新增三文件共 55 项通过；当前完整工作树 Python 318 项通过（其中也包含之前未提交的其他任务测试，不等同 clean HEAD 的测试数）。
- 6 个自有 synthetic correctness fixture，每例固定 6 个名称，seed=20261010，每例 48 个唯一置换，共 288/288 通过完整 C 序列比较。另有 576 次逆/复合源码相等检查通过；Java 的 96 个变体中抽取 12 个 javac 21.0.11 编译通过，未执行提交。
- 新 API 回归验证实际 warning、原文参数位置和原有权重，无 schema/database 修改。
- 后端 19 项 H2 测试通过，前端 vue-tsc/Vite build 通过；没有新浏览器全流程、MySQL 实库或 JPlag 重评。

这些 fixture 明确为 synthetic correctness probes、formalEligiblePairs=0，不是 benchmark、准确率、误报率或 AI 改写评测。完整规范化序列相同不等于抄袭，也不一定意味着语义等价；风险结果仅用于人工复核，不能直接处分学生。
