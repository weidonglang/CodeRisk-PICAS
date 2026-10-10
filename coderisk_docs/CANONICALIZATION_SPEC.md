# CANONICALIZATION_SPEC.md

> 2026-10-10 实现状态核对：普通 canonical 只实现有限作用域 token 绑定替换，不实现本文后续 Level 2–5 中的交换/重排/CanonicalAST/拆分合并。新增直接函数 keyword 参数绑定、动态名称访问 raw 回退及 Java 局部声明点修复；作用域模式不是任意改名的保证。固定 ASCII 名称域上的条件命题、例外和 288 个 synthetic 正确性探针见 [群作用与有限不变性](research/GROUP_ACTION_INVARIANCE.md)，测试/版本见 [第一批交付](research/FIRST_BATCH_REPORT.md)。不得将 canonical 序列不变扩大到整个加权分或语义等价。

> 2026-10-08 C 新增 `scope-aware-c-subset`，HTML 新增 `html-structure-canonical`；解析失败或绑定超出子集返回 `lexical-fallback`，不产生伪造映射。HTML 保留 class/id/URL，不把属性值作为变量名重写。二者均保留原始行列证据。详细支持语法、降级原因和实际覆盖见 [多语言进展](proposal/MULTILANGUAGE_PROGRESS.md)。

> 本文件定义 CodeRisk / PICAS 的置换不变代码规范化方案。它是项目的第二核心创新文件，直接服务于算法实现、实验消融、论文方法章节和专利交底。任何标识符归一化、AST 规范化、局部重排、跨语言结构抽象都必须遵守本文件。

---

## 1. 模块定位

### 1.1 模块名称

```text
Permutation-Invariant Canonicalization Module
```

中文名称：

```text
置换不变代码结构规范化模块
```

### 1.2 核心目标

本模块用于削弱不影响核心算法逻辑的表层差异，使系统能够识别以下伪装方式：

```text
变量名替换
函数名替换
参数名替换
注释删除
格式调整
局部变量声明顺序变化
可交换表达式左右项交换
部分无依赖语句换序
简单函数拆分或合并
```

### 1.3 边界声明

本模块不是程序等价性证明器，也不保证所有语义等价变换都能识别。它的定位是：

```text
为代码相似风险检测提供鲁棒的结构表示。
```

不得在论文或界面中声称：

```text
可以完全判断两个程序语义等价
可以完全识别所有跨语言改写
可以证明抄袭
```

---

## 2. 输入与输出

### 2.1 输入

```text
CleanCode
LanguageType
TokenSequence
AST
SymbolTable，可选
LineMapping
ParserStatus
```

### 2.2 输出

```text
CanonicalTokenSequence
CanonicalAST
CanonicalSubtreeFingerprints
IdentifierMapping
CanonicalFunctionSignatures
CanonicalOperationSequence
CanonicalControlSequence
NormalizationWarnings
```

### 2.3 输出必须保留的映射

```text
raw_identifier -> canonical_identifier
canonical_identifier -> original_occurrences
canonical_node -> raw_line_range
canonical_token -> raw_line_range
```

原因：证据展示必须能够回溯到原始代码。

---

## 3. 规范化层级

模块分为 5 层：

```text
Level 0：代码清洗，但不改变 token 含义
Level 1：标识符规范化
Level 2：字面量与类型规范化
Level 3：表达式与 AST 子树规范化
Level 4：局部结构重排与结构指纹
Level 5：语言无关结构抽象
```

开发时必须逐层实现，不允许一开始直接做复杂跨语言语义转换。

---

## 4. Level 0：基础清洗

### 4.1 处理内容

```text
统一换行符
统一缩进表示
删除注释，保留注释位置映射
删除多余空白
标准化字符串转义，保留原值摘要
保留原始代码副本
```

### 4.2 禁止事项

基础清洗不得：

```text
删除有效语句
改变运算符
改变常量值
合并可能影响语义的语句
改变控制结构顺序
```

---

## 5. Level 1：标识符规范化

### 5.1 规范化目标

将不同命名但相同结构位置和使用模式的标识符映射到稳定名称。

示例：

```java
int sum = a + b;
```

```java
int result = x + y;
```

可规范为：

```text
TYPE VAR_1 = VAR_2 + VAR_3
```

### 5.2 标识符类别

标识符必须按类别分别编号：

```text
VAR_n        局部变量
PARAM_n      函数参数
FUNC_n       用户自定义函数
CLASS_n      用户自定义类
FIELD_n      成员变量
CONST_n      用户自定义常量
IMPORT_n     导入别名，可选
```

不能把所有标识符都统一叫 `ID_n`，否则会丢失结构信息。

### 5.3 作用域规则

标识符编号必须考虑作用域：

```text
全局作用域
类作用域
函数作用域
块级作用域
循环作用域
lambda / inner function 作用域
```

同名变量在不同作用域中应视为不同符号：

```text
function f(): x -> VAR_1
function g(): x -> VAR_1 within g, but different symbol id
```

输出展示时可使用局部编号，内部存储必须保留唯一符号 ID。

### 5.4 编号策略

推荐采用“首次定义顺序 + 作用域路径”的稳定策略：

```text
canonical_name = category + local_index_in_scope
symbol_uid = hash(scope_path + original_name + definition_location)
```

示例：

```text
main/for_block_1/i -> VAR_1
main/for_block_2/i -> VAR_2
```

### 5.5 参数编号

函数参数按声明顺序编号：

```text
PARAM_1, PARAM_2, PARAM_3
```

对于 Python 默认参数、可变参数：

```text
*args  -> PARAM_VARARGS
**kw   -> PARAM_KWARGS
```

### 5.6 函数名规范化

用户自定义函数：

```text
FUNC_1, FUNC_2, ...
```

标准库函数不能一律归一化，需要保留类别：

```text
print        -> STD_IO_PRINT
input        -> STD_IO_INPUT
len          -> STD_LEN
sort/sorted  -> STD_SORT
Math.max     -> STD_MATH_MAX
Collections.sort -> STD_SORT
```

原因：标准库调用体现算法结构。

### 5.7 类名规范化

自定义类名：

```text
CLASS_1, CLASS_2
```

常见内置类型和集合类型应保留抽象类别：

```text
int / Integer -> TYPE_INT
long / Long   -> TYPE_LONG
String / str  -> TYPE_STRING
List / list   -> TYPE_SEQUENCE
Map / dict    -> TYPE_MAP
Set / set     -> TYPE_SET
```

---

## 6. Level 2：字面量与类型规范化

### 6.1 数字常量

数字常量不能简单全部替换为 `NUM`，需要区分：

```text
0       -> NUM_ZERO
1       -> NUM_ONE
-1      -> NUM_NEG_ONE
2       -> NUM_SMALL
10      -> NUM_SMALL
1000000007 -> NUM_MAGIC_MOD
其他    -> NUM_OTHER
```

### 6.2 魔法数处理

满足以下条件的数字应标记为 magic literal：

```text
非 0/1/-1
在条件判断中反复出现
用于取模
用于边界判断
不来自题目输入
跨代码对相同出现
```

输出：

```text
literal_value
literal_category
occurrence_lines
rarity_score，可选
```

### 6.3 字符串常量

字符串常量分类：

```text
STR_EMPTY
STR_FORMAT
STR_OUTPUT_LITERAL
STR_ERROR_MESSAGE
STR_OTHER
```

若题目要求固定输出，如 `YES/NO`，应标记为题目相关模板，默认低权重。

### 6.4 布尔常量

```text
true/True  -> BOOL_TRUE
false/False -> BOOL_FALSE
```

### 6.5 类型规范化

类型归一化示例：

```text
int, Integer, long 部分场景 -> TYPE_NUMERIC
String, str -> TYPE_STRING
ArrayList, list -> TYPE_SEQUENCE
HashMap, dict -> TYPE_MAP
HashSet, set -> TYPE_SET
```

但在强类型语言内部仍应保留原始类型用于证据解释。

---

## 7. Level 3：表达式规范化

### 7.1 可交换表达式

以下运算在大多数场景可视为可交换：

```text
a + b
b + a

a * b
b * a

a == b
b == a

a != b
b != a
```

规范化方法：

```text
COMM_OP(operator, sorted(operand_fingerprints))
```

### 7.2 不可交换表达式

以下不能排序：

```text
a - b
b - a

a / b
b / a

a % b
b % a

a < b
b < a

a <= b
b <= a
赋值表达式
函数调用参数列表
存在副作用的表达式
```

### 7.3 逻辑表达式

`&&` / `and`、`||` / `or` 理论上部分可交换，但短路求值可能影响副作用。默认策略：

```text
如果子表达式均为无副作用比较表达式，则可排序；
否则保持原顺序。
```

无副作用判断的初始规则：

```text
不包含函数调用
不包含自增自减
不包含赋值
不包含 I/O
不包含集合修改
```

### 7.4 比较表达式方向归一

可将：

```text
x > 0
0 < x
```

归一为：

```text
COMPARE_GT(VAR_1, NUM_ZERO)
```

方向归一规则：

```text
a < b  等价于 b > a
a <= b 等价于 b >= a
```

但必须保留原始表达式用于证据展示。

### 7.5 算术表达式树规范化

对于连续可交换结合操作：

```text
a + (b + c)
(c + a) + b
```

规范为：

```text
ADD_GROUP(sorted(a,b,c))
```

对于减法、除法、取模不做结合展开。

---

## 8. Level 3：AST 子树规范化

### 8.1 节点表示

规范 AST 节点结构：

```json
{
  "node_type": "IF_STATEMENT",
  "canonical_label": "IF",
  "children": [],
  "line_range": [10, 15],
  "attributes": {}
}
```

### 8.2 节点类型抽象

不同语言节点映射到统一类别：

```text
if_statement       -> IF
for_statement      -> LOOP_FOR
while_statement    -> LOOP_WHILE
enhanced_for       -> LOOP_ITERATE
assignment         -> ASSIGN
binary_expression  -> BINARY_OP
call_expression    -> CALL
return_statement   -> RETURN
```

### 8.3 子树指纹

```text
fingerprint(node) = SHA256(canonical_label + attributes + child_fingerprints)
```

对于可交换节点：

```text
child_fingerprints sorted before hashing
```

对于有序节点：

```text
child_fingerprints keep original order
```

### 8.4 指纹粒度

至少生成三类指纹：

```text
fine_fingerprint：保留较多细节
medium_fingerprint：保留结构和操作类型
coarse_fingerprint：只保留控制结构形态
```

用于不同相似度指标和证据强度判断。

---

## 9. Level 4：局部结构重排

### 9.1 目标

识别无明显数据依赖的局部语句顺序变化。

### 9.2 默认原则

只能在非常保守的条件下重排，不得为了提高相似度破坏语义。

### 9.3 可重排候选

同一基本块内，若两条语句满足：

```text
无共同写变量
一条语句的写变量不是另一条语句的读变量
不包含函数调用副作用
不包含 I/O
不包含集合修改
不包含 return/break/continue/throw
```

则可作为可重排候选。

### 9.4 不可重排语句

```text
输入输出语句
函数调用且无法证明无副作用
集合 add/remove/put/update
自增自减
赋值依赖链
return
break
continue
throw
异常处理
同步/锁相关语句
```

### 9.5 重排实现

不直接改变展示代码，只生成规范块签名：

```text
block_signature = sorted(independent_statement_fingerprints) + ordered(dependent_statement_fingerprints)
```

### 9.6 证据表述

允许表述：

```text
“两个代码块在忽略无依赖声明语句顺序后具有相似结构。”
```

不允许表述：

```text
“两个代码块语义完全相同。”
```

---

## 10. 函数级规范化

### 10.1 函数签名规范

函数签名表示：

```text
FUNC(return_type_category, param_type_categories, control_summary, operation_summary)
```

示例：

```text
FUNC(TYPE_INT, [TYPE_SEQUENCE], LOOP+IF+RETURN, MOD+ACCUMULATE)
```

### 10.2 函数调用图

初始版本保存：

```text
caller -> callee_category
```

自定义函数统一为 `FUNC_n`，标准库函数保留抽象类别。

### 10.3 函数拆分/合并

V3 可实现轻量检测：

```text
如果 A 的一个大函数结构片段约等于 B 的多个小函数组合，标记为 FUNCTION_SPLIT_MERGE_CANDIDATE。
```

该证据强度默认为中等，不单独作为高风险依据。

---

## 11. 控制结构规范化

### 11.1 控制序列

将控制结构抽象为：

```text
IF
IF_ELSE
LOOP_FOR
LOOP_WHILE
LOOP_ITERATE
SWITCH
TRY_CATCH
RETURN
RECURSIVE_CALL
```

### 11.2 循环统一

Java enhanced-for、Python for-in 可统一为：

```text
LOOP_ITERATE_SEQUENCE
```

C/Java index loop 可抽象为：

```text
LOOP_INDEX_RANGE
```

当能识别数组遍历时，可进一步统一为：

```text
ITERATE_SEQUENCE
```

### 11.3 条件统一

条件表达式抽象：

```text
MOD_EQ_ZERO
BOUNDARY_CHECK
NULL_CHECK
EMPTY_CHECK
RANGE_CHECK
EQUALITY_CHECK
COMPARISON_CHECK
```

---

## 12. 数据结构使用规范化

### 12.1 类型抽象

```text
Array / list / vector -> SEQUENCE
HashMap / dict        -> MAP
HashSet / set         -> SET
Queue / deque         -> QUEUE
Stack                 -> STACK
PriorityQueue / heapq -> HEAP
```

### 12.2 操作抽象

```text
list.add / append       -> SEQUENCE_APPEND
list.get / arr[i]       -> SEQUENCE_ACCESS
map.get / dict[key]     -> MAP_GET
map.put / dict[key]=v   -> MAP_PUT
set.add                 -> SET_ADD
sort / sorted           -> SORT
```

### 12.3 语言差异处理

Python 内置语法糖和 Java 显式方法调用应尽量映射到相同操作类别。

---

## 13. I/O 规范化

### 13.1 输入抽象

```text
Scanner.nextInt      -> INPUT_READ_INT
BufferedReader.read  -> INPUT_READ_LINE
input()              -> INPUT_READ_LINE
sys.stdin.readline   -> INPUT_READ_LINE
scanf                -> INPUT_READ_FORMATTED
```

### 13.2 输出抽象

```text
System.out.println   -> OUTPUT_WRITE_LINE
print                -> OUTPUT_WRITE_LINE
printf               -> OUTPUT_WRITE_FORMATTED
```

### 13.3 降权规则

I/O 结构通常由题目强制规定，因此作为弱证据处理。

---

## 14. 语言无关 IR 规范化

### 14.1 IR 目标

IR 用于初步跨语言结构对齐，不追求完整编译器中间表示。

### 14.2 IR 节点类型

```text
PROGRAM
FUNCTION
PARAMETER
VARIABLE_INIT
INPUT_READ
OUTPUT_WRITE
ASSIGN
CONDITION
LOOP
ITERATE_SEQUENCE
INDEX_ACCESS
ARITHMETIC
COMPARISON
ACCUMULATE
COLLECTION_OP
FUNCTION_CALL
RETURN
```

### 14.3 IR 生成原则

```text
先从 AST 映射基础节点
再抽象控制结构
再抽象数据结构操作
最后生成 IR 序列和 IR 子树指纹
```

### 14.4 IR 不确定性

若某节点无法可靠映射，应标记：

```text
IR_UNKNOWN
```

不得强行猜测。

---

## 15. 标识符映射证据

### 15.1 映射生成

两个代码对比时，根据 canonical token 对齐、AST 位置和使用模式生成映射：

```text
original_identifier_a -> original_identifier_b
mapping_confidence
mapping_occurrence_count
scope
usage_pattern
```

### 15.2 稳定映射判断

满足以下条件可视为稳定映射：

```text
在多个语句中出现
读写角色一致
AST 位置相似
所属作用域相似
与其他变量关系一致
```

### 15.3 输出示例

```json
{
  "a_identifier": "sum",
  "b_identifier": "result",
  "canonical_role": "ACCUMULATOR_VAR",
  "confidence": 0.92,
  "occurrences": 7,
  "usage_pattern": "INIT_ZERO -> ACCUMULATE -> RETURN"
}
```

---

## 16. 规范化警告

规范化过程必须输出 warning，避免过度自信。

常见 warning：

```text
PARSER_PARTIAL
SCOPE_ANALYSIS_INCOMPLETE
SIDE_EFFECT_UNKNOWN
LANGUAGE_FEATURE_UNSUPPORTED
TOO_SHORT_CODE
TOO_MANY_SYNTAX_ERRORS
IR_MAPPING_PARTIAL
```

前端和报告应展示算法可信度。

---

## 17. 消融实验开关

为了期刊实验，模块必须支持开关：

```text
enable_identifier_normalization
enable_function_normalization
enable_literal_normalization
enable_commutative_normalization
enable_local_reordering
enable_ast_fingerprint
enable_language_ir
```

用于实验：

```text
无规范化
仅标识符规范化
标识符 + 表达式规范化
完整规范化
完整规范化 + 题目感知阈值
```

---

## 18. 实现优先级

### 18.1 V1 必做

```text
标识符类别识别
变量名归一化
参数名归一化
函数名归一化
CanonicalTokenSequence
IdentifierMapping 基础输出
```

### 18.2 V2 必做

```text
AST 节点类型抽象
AST 子树指纹
可交换表达式排序
类型与字面量规范化
CanonicalASTSimilarity 支撑
```

### 18.3 V3 必做

```text
局部无依赖语句签名
控制结构规范化
数据结构操作规范化
稀有片段规范化输出
消融实验开关
```

### 18.4 V4 增强

```text
Java-Python IR
C 语言部分 IR
函数拆分/合并候选检测
更精细的数据依赖分析
```

---

## 19. 测试要求

### 19.1 单元测试样例

必须测试：

```text
变量名替换前后 canonical token 一致
函数名替换前后 canonical function signature 一致
可交换表达式 a+b 与 b+a 指纹一致
不可交换表达式 a-b 与 b-a 指纹不同
不同作用域同名变量不会错误合并
标准库函数不会被错误归一化为普通函数
语法错误代码能输出 warning 而不是崩溃
```

### 19.2 样例目录

建议：

```text
analysis-service-python/tests/fixtures/canonicalization/
  java_identifier_rename/
  python_identifier_rename/
  commutative_expr/
  scope_shadowing/
  standard_library_calls/
  partial_parse/
```

---

## 20. 自检清单

每次修改规范化模块后检查：

```text
[ ] 是否保留原始代码行号
[ ] 是否区分变量、参数、函数、类、字段
[ ] 是否考虑作用域
[ ] 是否没有把标准库函数全部抹平
[ ] 是否没有错误排序不可交换表达式
[ ] 是否没有重排有副作用语句
[ ] 是否输出 normalization warnings
[ ] 是否支持消融实验开关
[ ] 是否能生成前端证据需要的映射
[ ] 是否没有声称程序语义完全等价
```
