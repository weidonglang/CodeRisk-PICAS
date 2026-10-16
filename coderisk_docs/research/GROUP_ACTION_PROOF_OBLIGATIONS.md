# S1/S2 命题状态、反例与实现义务

状态标签不能互换：`PROVED_CONDITIONALLY` 是此前提下的数学推导；`TESTED_FINITE` 是真实有限测试；`NOT_PROVED` 不得写成实现保证；`OUT_OF_SCOPE` 不是已经实现了拒绝所有语法。

| ID | 命题/义务 | 状态 | 依据与缺口 |
| --- | --- | --- | --- |
| G1 | 固定 N 的 Sym(N) 是群、位置上的 e/逆/复合满足作用律 | PROVED_CONDITIONALLY | 封闭对象域、F固定和同时改名；逐位置证明，orbit tests |
| G2 | ~G 为等价关系，商集存在 | PROVED_CONDITIONALLY | 由恒等/逆/复合；不是算法的风险等级 |
| C1 | D1—D3 成立则 C(g·P)=C(P) | PROVED_CONDITIONALLY | 作用域/声明次序归纳，见轨道文档 |
| C2 | C 可下降为商集上唯一 C̄ | PROVED_CONDITIONALLY | 良定义/π满射；不声称单射 |
| I1 | 生产索引器在全部支持语法上满足 D1—D3 | NOT_PROVED | Python特殊绑定/动态封装、Java近似符号解析尚不全 |
| I2 | 12 gold 的完整位置绑定及有限置换 | TESTED_FINITE | 手标独立 oracle、AST/symtable、三固定 seed，真实产物 |
| I3 | Java源码可编译 | TESTED_FINITE | 6 bounded javac；编译不证明 binding/语义 |
| A1 | 统一内部拼写轨道蕴含受限绑定α-关系 | PROVED_CONDITIONALLY | 不改外部/接口，全部名字绑定、捕获规避 |
| A2 | α-等价或 C相同必在同一G轨道 | NOT_PROVED，反例成立 | 同名两个参数分别改 left/right，实际 C同却无单值g |
| F1 | n-gram集合相同必C相同/语义相同 | NOT_PROVED，反例成立 | 两/三重复增量语句，C不同集合相同 |
| W1 | PICAS融合总分为群不变量 | OUT_OF_SCOPE，实际不成立 | raw 随名改变；rename_sensitivity实际输出 |
| S1 | 任意重排、交换、split/merge为当前G | OUT_OF_SCOPE | 不保留本模型语法骨架，缺逆/封闭也不能泛称群 |
| R1 | 表示稳定可证明低误报、关系成立 | OUT_OF_SCOPE | 需可信独立负例；高分只能提示人工复核 |

## 具体用例与预期行为

源码金样例在 `group_action_oracle.py`，所有出现位置手写标识后机械渲染；以下不是仅用口头说明替代测试。

| 类型 | 源码机制 | 前提/预期与证据 |
| --- | --- | --- |
| 默认值作用域 | `seed=9; def fold(seed=seed): return seed` | 默认value用module绑定，参数/返回用function绑定；py-default-scope |
| lambda默认值 | `handler=lambda value=base:value+base` | 默认外层、body的value局部；py-lambda-default |
| varargs/kw-only | `def fold(*items,step=1,**options)` | 参数声明可规范化；**kwargs keyword派发仍不支持；py-variadic-declarations |
| 类定义期/方法 | class seed=2，默认value=seed，method body用module seed | 默认和body不同查找规则；py-class-default；动态类/forward类绑定保守回退 |
| 直接关键字调用 | fold(value=2)定义前/后出现 | label归到callee参数而非调用方同名变量；py-forward-keyword |
| 嵌套遮蔽/闭包 | outer(value)定义inner(value)，引用outer total | 同拼写不同身份及free查找；py-shadow-closure |
| Unicode坐标 | 同行字符串“中”之后出现value | AST字节列与token字符列不可混用；py-unicode-offset |
| Java声明点/字段 | `int first=value; int value=2; ...this.value` | 字段/局部归属明确；java-declaration-point |
| Java块局部 | if与else各声明part | 块路径区分；java-block-locals |
| 外部/字面量 | `print("value",value)`、`Math.abs`、System.out.println | 外部及字符串固定；不得用普通替换抹平 |
| for/catch遮蔽 | field value，header也声明value，末尾return field | brace索引不够，明确 located raw回退；先2红后绿，新增基本/增强for和catch测试 |
| 捕获/非双射 | x→y、y→y | INVALID_CAPTURE，不计合法不变性失败/成功 |
| 动态访问/alias | globals字符串、保存动态函数、alias keyword | 已知形态拒绝；opaque外部wrapper为ORACLE_UNCERTAIN，不能称静态黑名单穷尽 |
| Java重载/泛型/成员 | 同f有int/double重载、未知对象成员 | 无类型/签名oracle，ORACLE_UNCERTAIN/OUT_OF_SCOPE；mode不认证 |
| parse failure | 不完整Python def、Java未闭合 | PARSER_FAILURE，raw/空identifiers/reason；Java平衡不等于完全parse |
| 非群变换 | +改-、插语句、交换a+b、重排赋值、拆函数 | 不受G命题约束；不变失败不是改名定理的反例 |
| 信息损失 | 两次/三次total自增 | 完整C不同，指纹/融合可同；判别机制而非真实FPR |

## 审查规则

新的边界输入先写会失败的测试、保留红日志，再小修或降级；不得为通过率剔除失败 fixture。`ACCEPTED_VALID` 指独立 oracle 在**自有金样例范围**内批准，不能推广到任意生产输入。`ORACLE_UNCERTAIN` 和 parser/unsupported 均独立列出。有限抽样不是遍历所有程序；对一个六名 fixture 三seed抽样也不等于全部720个不同置换。

形式化机器证明、完整Java类型/符号解析、全Python动态名称行为均未完成。导师应审查对象域封闭、外部契约和证明前提；优先精读已有绑定理论，不为增加数学术语扩大主张。
