# dsh-hazplan-check — HAZOP 分析表要素齐备性与偏差推导一致性核对

`dsh-hazplan-check` 读取一份 HAZOP 分析表——按表格自身的列名组织的行（中英文列名均可），加上可选的、写明分析对象的表头——核对这份表格自身的齐备与可追溯：每行是否填了模板要求的栏目（默认 `偏差` 与 `原因`）、每行是否写明 `节点`、`引导词` 是否取自标准表1与表2或本分析事先声明的清单、每行是否看得出偏差来自哪个要素、`风险等级` 是否出自本机构的风险档位、表头能否识别分析对象、以及每个 `偏差` 是否字面上等于 `工艺参数` 与 `引导词` 的组合；因缺列而无法执行的核对会出现在 `skipped` 里，而不是静默通过。

## 它回答什么问题

| 你会问 | 它怎么答 |
|---|---|
| 某行填了偏差，但原因栏空着，会被报出吗？ | 会。`HZ-001` 要求每行填写必填栏目；出厂未配置 `requiredFields` 时，回退到条款本身点名的一对：`偏差` 与 `原因`，所以 `原因` 空着本身就是缺项。它只核对栏目是否填写，不判断问题是否找全、原因是否成立。 |
| 有三行根本没有写节点，会被指出来吗？节点划分得粗或细，它会不会评价？ | `HZ-002` 会把这几行合并报出一条，并列出所在行号，因为记录没有节点就生成不了条款要求的节点清单。它只核对 `节点` 是否填写；节点划分粒度是否恰当，它不判断（4.2 没有判据），也不判断有没有节点被漏掉未作分析。 |
| 我们的分析在 `引导词` 栏里写了「相逆」，会被提示吗？ | `HZ-003` 会把它作为清单之外的引导词报出：国标自己的用词是「相反」而不是「相逆」，表1与表2给出的是 无/多/少/伴随/部分/相反/异常 与 早/晚/先/后。这条只是提示而不断定不合规——6.4.3 允许自定义引导词，只要分析前已定义并存档，所以本条为 `warn`。部署时也可以换成自己的清单，那时只有清单之外的词会被报出。 |
| `偏差` 栏写的是「无流量」，而 `工艺参数` 是「温度」、`引导词` 是「无」，这能查出来吗？ | 能。`HZ-007` 在写下的 `偏差` 不包含 `工艺参数` 与 `引导词` 的组合（两种语序都算）时报出该行；空白与常见连接符（如 `+`、`、`、`/`、`-`、`—`、`的`、`：`）忽略不计，所以「流量无」「流量 + 无」「无流量」都算相符。它只在三列同时具备时执行，否则出现在 `skipped` 里；命中通常意味着复制粘贴串行，不代表该偏差在工艺上不成立。 |
| `风险等级` 栏填了「中」，但我们没有配置任何风险档位，会怎样？ | `HZ-005` 会把自己报进 `skipped`，而不是当作通过：标准未规定风险等级的刻度，档位必须来自本机构的风险准则，出厂清单是空的。配置之后，它只核对所填值是否在册，不判断定级是否正确；本条严重级封顶为 `info`。 |
| 分析表里没有任何一行写明所分析的对象（装置或单元），算缺项吗？ | `HZ-006` 会在顶层报出一条：没有分析对象，结论就无法追溯到被分析的边界。它依据的表头项来自资料性附录——是建议而不是强制——所以本条停在 `warn`；确实不带表头的表格可用 `requireHeader: false` 停用本条。 |

## 依据的标准

| 文件 | 文号 | 引用它的规则 |
|---|---|---|
| 《危险与可操作性分析（HAZOP分析）应用指南》 | GB/T 35320-2017 | HZ-001, HZ-002, HZ-003, HZ-004, HZ-005, HZ-006, HZ-007 |
| 《风险管理 风险评估技术》 | GB/T 27921-2023 | HZ-005 |

**Boundary:** this plugin checks one **HAZOP worksheet** for what a sheet can be held to — that every row
records the analysis content your template requires, that each 偏差 actually follows from the 工艺参数 and
引导词 beside it, that risk levels come from your own vocabulary, that every node has rows, and that
recommendations carry their closure fields. It does **not** judge whether the causes are complete, whether
the consequences are analysed far enough, whether the safeguards are adequate, or whether a risk rating is
correct. **Those four judgements are the study team's, and they are where HAZOP's value lies.**

> ### ⚠️ Nothing here is `error`, and the clause wording is why
>
> **GB/T 35320-2017《危险与可操作性分析（HAZOP分析）应用指南》** is in force (published and effective
> 2017-12-29, identical to IEC 61882:2001), and its clause text was obtained verbatim.
>
> **The standard is a *recommended* one (the number carries "/T"), and every clause this pack cites uses
> 宜 — "should" — not 应.** That applies to the two clauses an earlier version of this pack rated as
> `error`: **6.6.4** reads 「每一个危险和可操作性性问题都**宜**作为单项记录」 and **6.6.3** opens
> 「HAZOP 分析输出**宜**包括：」. **A recommendation cannot support an error rating**, so both rules are
> now `warn` and **this plugin reports no error at all** — consistent with how the family treats every
> other recommended standard. A test pins this so a later edit cannot quietly re-escalate one.
>
> **Everything else is capped at `warn` or `info`, for three reasons the pack records:**
>
> 1. **Appendix A.2 — the one place a column list appears — is a 资料性附录.** Its wording is "表列的标题
>    **可为**以下各项", it adds "**也可记录**其他信息", and it says outright that "工作表的版面设计**各有不同**".
>    **There is no mandatory column list**, so a missing column can only ever be a suggestion.
> 2. **Clause 4.2 gives no criterion for node granularity.** It says the size of a node "取决于系统的
>    复杂性和危险的严重程度" and nothing quantitative follows. This plugin **does not** judge node size.
> 3. **The standard fixes no risk-level scale.** 6.5 mentions a risk matrix as useful and defers the method
>    to IEC 60300-3-9; GB/T 27921-2023's matrix description is likewise informative. Levels must come from
>    your own risk criteria, so the vocabulary ships **empty**.
>
> Two further honesty notes are in the pack. The guide-word vocabulary uses the standard's own wording —
> **「相反」, not the colloquial "相逆"** — and combines table 1 with table 2; a custom guide word is
> **not** non-compliant, because 6.4.3 permits one "只要在分析开始前进行了定义". And **SH/T 3240-2025**
> (the petrochemical HAZOP specification, in force 2025-11-01) had only its identity, status and glossary
> verified — **its clause text was not obtained, so this pack cites none of it**.
>
> The four judgements this plugin does not make: whether the causes are complete, whether the consequences
> are analysed far enough, whether the safeguards are adequate, whether a risk rating is correct.

## Compatibility

| 项目 | 状态 |
|---|---|
| Harness | 对等版本范围 `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` —— 已实测同时接受 `0.2.0-rc.2` 与 `0.2.1-alpha.1`。**刻意不声明 `engines.dsh`**：它没有任何读取者，也无法拒装任何宿主 |
| Node | `^22.19.0 || >=24.0.0` |
| 平台 | 全平台（纯 ESM；无原生代码、无联网、不调用模型） |
| 工具模式 | `native` / `ptc` / `both` 均可；批量校验整个目录时建议 `ptc`，schema 成本只付一次 |

## What it does

规则表、字段说明与行为细节见 [README.md](README.md#what-it-does)（英文主版本）。本插件只列出材料与所引条款之间的字面差异，并对无法执行的检查在 `skipped` 中逐项说明。

## Install

```sh
dsh plugin --profile <name> add dsh-hazplan-check
dsh --profile <name> --dump-config | grep 'dsh-hazplan-check'
```

## Configuration

全部可调参数都在 `src/config.ts` 的 Schemastery schema 中，只改 `cordis.yml` 即可生效，无需改代码；逐条阈值在 `rules/` 下的规则库文件里。

| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rulesFile` | string | `rules/hazplan-check.yaml` | 规则库文件路径，相对插件包根目录 |
| `disabledRules` | string[] | `[]` | 要停用的规则 id 列表；每条都会出现在 `skipped` 中 |
| `onlyRules` | string[] | `[]` | 只执行这些规则 id；留空表示执行全部规则 |
| `skipNotes` | string | `""` | 附加到每条 `skipped` 说明后的备注 |
| `timeoutMs` | number | `120000` | 工具协作式超时预算（毫秒） |

## Material format

支持 JSON 与 YAML。完整字段示例见 [README.md](README.md#material-format)（英文主版本）。字段在读取层是可选的，由检查引擎校验，因此部分导出的材料会产生"缺项"类差异，而不是让程序崩溃。

## Rule sources

规则数据与代码分离，每条规则都带文件名、文号、按原文自身编号体系的条款号、逐字摘录与来源地址。加载期强制：摘录必须是真实引文且不少于八个字符；依据仅为原则性条款（`kind: derived-from-principle`，严重级上限 `warn`）或本机构配置（`kind: institutional-configuration`，上限 `info`）的检查不得标为 `error`。夸大依据的规则库会在加载期失败，而不会产出一份看起来很有底气的报告。

核验中确认的边界与"刻意没有作出的结论"见 [README.md](README.md#rule-sources)（英文主版本）与随包的 `rules/evidence/` 目录。

## Troubleshooting

- **插件装上了但工具不出现**：确认 `main` 指向 `lib/index.mjs` 且 `pnpm run build` 已生成该文件；`main` 写错会让加载器静默跳过该条目。
- **`dsh plugin add` 报版本不兼容**：peer 范围覆盖 `0.1.x` 与 `0.2.x`；若运行时在其之外，可显式豁免：`dsh plugin --profile <name> allow-version <包名@版本> --dsh-version <runtime> --accept-risk`
- **某条规则没有执行**：查看 `skipped` 数组，其中写明了规则 id 与原因。
- **`check` 报 `manifest-peers` 失败**：静态检查器比对的是一份早于 0.2 世代的硬编码 peer 范围；安装期的 peer 校验以运行时为准。这是 `dsh-plugin-dev` 的已知上游问题。
- **时间看起来偏移**：全部计算都是对输入字符串做墙上时钟运算，不做时区换算。

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-hazplan-check
```

第 4 项把 `../_shared` 的共享件同步进 `src/shared/`；每次改动共享件后都要重跑。

## License

[Apache License 2.0](LICENSE) © 2026 dsh-hazplan-check contributors.
