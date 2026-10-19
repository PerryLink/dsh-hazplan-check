# dsh-hazplan-check — HAZOP 分析表要素齐备性与偏差推导一致性核对

[English](README.md) · [简体中文](README-zh.md) · [Español](README-es.md) · [Português](README-pt.md) · [हिन्दी](README-hi.md)

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)
[![dshfind](https://dshfind.com/api/badge/PerryLink/dsh-hazplan-check?metric=downloads)](https://dshfind.com/en/plugins/PerryLink/dsh-hazplan-check?ref=badge)

`dsh-hazplan-check` 读取一份 HAZOP 分析表——按表格自身的列名组织的行（中英文列名均可），加上可选的、写明分析对象的表头——核对这份表格自身的齐备与可追溯：每行是否填了模板要求的栏目（默认 `偏差` 与 `原因`）、每行是否写明 `节点`、`引导词` 是否取自标准表1与表2或本分析事先声明的清单、每行是否看得出偏差来自哪个要素、`风险等级` 是否出自本机构的风险档位、表头能否识别分析对象、以及每个 `偏差` 是否字面上等于 `工艺参数` 与 `引导词` 的组合；因缺列而无法执行的核对会出现在 `skipped` 里，而不是静默通过。

## Install

```sh
dsh plugin --profile <name> add dsh-hazplan-check
dsh --profile <name> --dump-config | grep 'dsh-hazplan-check'
```

## 实际输出长什么样

![dsh-hazplan-check 工作流图：文档 → 规则包 → 核对结果。](docs/assets/dsh-hazplan-check-flow.svg)

*工作流概览：文档 → 规则包 → 核对结果。下面的示例使用实际命令面。*


本插件对自己 `HZ-004` 测试夹具的**真实输出**，不是示意图。规则库不伪造引文，因此每条发现都会同时写明所引条款，以及该条款原文本次未取得。

## 它回答什么问题

### 示例

下表是示例集：第一行是详细走查，其余行是简短案例。


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

**边界（中文译文，以英文原文为准）：** 本插件核对一份 **HAZOP 工作表**，范围限于表格可以要求到的内容——每行是否记录了模板要求的分析内容，每个偏差是否确实由其旁的工艺参数与引导词推出，风险等级是否取自你自己的取值口径，每个节点是否有对应行，以及建议措施是否填写其闭环字段。它**不**判定原因是否完整、后果分析是否充分、现有安全措施是否足够，也不判定风险评级是否正确。**这四项判断属于分析小组，也正是 HAZOP 的价值所在。**

> ### ⚠️ 这里没有任何 `error`，原因在条款措辞（以英文原文为准）
>
> **GB/T 35320-2017《危险与可操作性分析（HAZOP分析）应用指南》** 是现行标准（2017-12-29 发布并实施，与 IEC 61882:2001 等同），其条款原文已逐字取得。
>
> **该标准是*推荐性*标准（标准号带“/T”），本规则库引用的每一条条款用的都是“宜”——“should”——而不是“应”。** 这一点适用于本规则库早期版本评为 `error` 的那两条条款：**6.6.4** 写的是「每一个危险和可操作性性问题都**宜**作为单项记录」，**6.6.3** 开头是「HAZOP 分析输出**宜**包括：」。**推荐性要求不能支撑错误评级**，因此这两条规则现在都是 `warn`，**本插件根本不报告任何错误**——这与本系列插件对待其他每一部推荐性标准的方式一致。有测试固定这一点，使日后的修改无法悄悄把其中一条重新升级。
>
> **其余一切都封顶在 `warn` 或 `info`，理由有三条，规则库均有记录：**
>
> 1. **附录 A.2——唯一出现栏目清单的地方——是资料性附录。** 其措辞是“表列的标题**可为**以下各项”，还补充“**也可记录**其他信息”，并直说“工作表的版面设计**各有不同**”。**不存在强制性的栏目清单**，因此缺少某一栏最多只能算建议。
> 2. **第 4.2 条没有给出节点划分粒度的准则。** 它说节点的大小“取决于系统的复杂性和危险的严重程度”，其后没有任何量化规定。本插件**不**判断节点大小。
> 3. **标准没有规定风险等级刻度。** 6.5 提到风险矩阵有用，并把方法交由 IEC 60300-3-9；GB/T 27921-2023 对矩阵的描述同样属资料性。等级必须来自你自己的风险准则，因此词表出厂为**空**。
>
> 规则库中还有两条关于诚实性的说明。引导词词表采用标准自己的措辞——**「相反」，而不是俗写的“相逆”**——并合并表 1 与表 2；自定义引导词**并不**不合规，因为 6.4.3 允许自定义，条件是“只要在分析开始前进行了定义”。另外，**SH/T 3240-2025**（石油化工 HAZOP 规范，2025-11-01 实施）只核实了其名称、状态和术语表——**其条款原文本次未取得，因此本规则库不引用其中任何内容**。
>
> 本插件不作的四项判断：原因是否完整、后果分析是否深入充分、现有安全措施是否充分、风险评级是否正确。

## Compatibility

| 项目 | 状态 |
|---|---|
| Harness | 对等版本范围 `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` —— 已实测同时接受 `0.2.0-rc.2` 与 `0.2.1-rc.2`。**已声明 `engines.dsh`**：0.2.1 起由宿主单独裁决，范围为 `>=0.2.1-0 <0.3.0` |
| Node | `^22.19.0 || >=24.0.0` |
| 平台 | 全平台（纯 ESM；无原生代码、无联网、不调用模型） |
| 工具模式 | `native` / `ptc` 均可；批量校验整个目录时建议 `ptc`，schema 成本只付一次 |

## What it does

规则表、字段说明与行为细节见 [README.md](README.md#what-it-does)（英文主版本）。本插件只列出材料与所引条款之间的字面差异，并对无法执行的检查在 `skipped` 中逐项说明。

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

## PerryLink DSH Plugin Family

本项目是 [PerryLink](https://github.com/PerryLink) 维护的 DeepSeek Harness 插件家族成员。完整名单默认折叠，避免每个 README 的首屏被长表淹没；点击展开可查看每一行及其状态。

<details>
<summary>展开全部插件</summary>

| 插件 | 状态 |
|---|---|
| **[dsh-aqua-input-check](https://github.com/PerryLink/dsh-aqua-input-check)** |  |
| **[dsh-archive-check](https://github.com/PerryLink/dsh-archive-check)** |  |
| **[dsh-auto-review](https://github.com/PerryLink/dsh-auto-review)** |  |
| **[dsh-autotier](https://github.com/PerryLink/dsh-autotier)** |  |
| **[dsh-bid-ca-precheck](https://github.com/PerryLink/dsh-bid-ca-precheck)** |  |
| **[dsh-bid-qual-check](https://github.com/PerryLink/dsh-bid-qual-check)** |  |
| **[dsh-cert-mcp](https://github.com/PerryLink/dsh-cert-mcp)** |  |
| **[dsh-checkpoint-rewind](https://github.com/PerryLink/dsh-checkpoint-rewind)** |  |
| **[dsh-click](https://github.com/PerryLink/dsh-click)** |  |
| **[dsh-composer-history](https://github.com/PerryLink/dsh-composer-history)** |  |
| **[dsh-contract-stance](https://github.com/PerryLink/dsh-contract-stance)** |  |
| **[dsh-customs-doc-check](https://github.com/PerryLink/dsh-customs-doc-check)** |  |
| **[dsh-data-quality](https://github.com/PerryLink/dsh-data-quality)** |  |
| **[dsh-demurrage-ledger](https://github.com/PerryLink/dsh-demurrage-ledger)** |  |
| **[dsh-doublecheck](https://github.com/PerryLink/dsh-doublecheck)** |  |
| **[dsh-drill-script-check](https://github.com/PerryLink/dsh-drill-script-check)** |  |
| **[dsh-eia-guide-check](https://github.com/PerryLink/dsh-eia-guide-check)** |  |
| **[dsh-emergency-plan](https://github.com/PerryLink/dsh-emergency-plan)** |  |
| **[dsh-essay-rubric-check](https://github.com/PerryLink/dsh-essay-rubric-check)** |  |
| **[dsh-evidence-check](https://github.com/PerryLink/dsh-evidence-check)** |  |
| **[dsh-export-ctl-check](https://github.com/PerryLink/dsh-export-ctl-check)** |  |
| **[dsh-fast](https://github.com/PerryLink/dsh-fast)** |  |
| **[dsh-fmea-table-check](https://github.com/PerryLink/dsh-fmea-table-check)** |  |
| **[dsh-forecast-penalty](https://github.com/PerryLink/dsh-forecast-penalty)** |  |
| **[dsh-fund-research](https://github.com/PerryLink/dsh-fund-research)** |  |
| **[dsh-github](https://github.com/PerryLink/dsh-github)** |  |
| **[dsh-gongwen-flow-check](https://github.com/PerryLink/dsh-gongwen-flow-check)** |  |
| **[dsh-gongwen-word-check](https://github.com/PerryLink/dsh-gongwen-word-check)** |  |
| **[dsh-guard-plan-qc](https://github.com/PerryLink/dsh-guard-plan-qc)** |  |
| **[dsh-hazchem-check](https://github.com/PerryLink/dsh-hazchem-check)** |  |
| **[dsh-hazplan-check](https://github.com/PerryLink/dsh-hazplan-check)** |  |
| **[dsh-hidden-risk-map](https://github.com/PerryLink/dsh-hidden-risk-map)** |  |
| **[dsh-hs-classify](https://github.com/PerryLink/dsh-hs-classify)** |  |
| **[dsh-icd-rule-check](https://github.com/PerryLink/dsh-icd-rule-check)** |  |
| **[dsh-industry-research](https://github.com/PerryLink/dsh-industry-research)** |  |
| **[dsh-lawcite-adapter](https://github.com/PerryLink/dsh-lawcite-adapter)** |  |
| **[dsh-laya](https://github.com/PerryLink/dsh-laya)** |  |
| **[dsh-lc-doc-check](https://github.com/PerryLink/dsh-lc-doc-check)** |  |
| **[dsh-learning-gap-check](https://github.com/PerryLink/dsh-learning-gap-check)** |  |
| **[dsh-library](https://github.com/PerryLink/dsh-library)** |  |
| **[dsh-local-ai](https://github.com/PerryLink/dsh-local-ai)** |  |
| **[dsh-lsp-actions](https://github.com/PerryLink/dsh-lsp-actions)** |  |
| **[dsh-mask](https://github.com/PerryLink/dsh-mask)** |  |
| **[dsh-mcp-panel](https://github.com/PerryLink/dsh-mcp-panel)** |  |
| **[dsh-medrec-qc](https://github.com/PerryLink/dsh-medrec-qc)** |  |
| **[dsh-memento](https://github.com/PerryLink/dsh-memento)** |  |
| **[dsh-nsfc-form-check](https://github.com/PerryLink/dsh-nsfc-form-check)** |  |
| **[dsh-nurse-record-check](https://github.com/PerryLink/dsh-nurse-record-check)** |  |
| **[dsh-observe](https://github.com/PerryLink/dsh-observe)** |  |
| **[dsh-origin-rvc-check](https://github.com/PerryLink/dsh-origin-rvc-check)** |  |
| **[dsh-ota-review-check](https://github.com/PerryLink/dsh-ota-review-check)** |  |
| **[dsh-output-styles](https://github.com/PerryLink/dsh-output-styles)** |  |
| **[dsh-paper-doc-adapter](https://github.com/PerryLink/dsh-paper-doc-adapter)** |  |
| **[dsh-permission-rules](https://github.com/PerryLink/dsh-permission-rules)** |  |
| **[dsh-permit-report-check](https://github.com/PerryLink/dsh-permit-report-check)** |  |
| **[dsh-pipeline-check](https://github.com/PerryLink/dsh-pipeline-check)** |  |
| **[dsh-pleading-draft](https://github.com/PerryLink/dsh-pleading-draft)** |  |
| **[dsh-plugin-doctor](https://github.com/PerryLink/dsh-plugin-doctor)** |  |
| **[dsh-plugin-guide](https://github.com/PerryLink/dsh-plugin-guide)** |  |
| **[dsh-plugin-kit](https://github.com/PerryLink/dsh-plugin-kit)** |  |
| **[dsh-plugin-upgrade](https://github.com/PerryLink/dsh-plugin-upgrade)** |  |
| **[dsh-policy-brief-draft](https://github.com/PerryLink/dsh-policy-brief-draft)** |  |
| **[dsh-power-loss-split](https://github.com/PerryLink/dsh-power-loss-split)** |  |
| **[dsh-power-ticket-check](https://github.com/PerryLink/dsh-power-ticket-check)** |  |
| **[dsh-ppap-check](https://github.com/PerryLink/dsh-ppap-check)** |  |
| **[dsh-protest-deadline](https://github.com/PerryLink/dsh-protest-deadline)** |  |
| **[dsh-railway-window](https://github.com/PerryLink/dsh-railway-window)** |  |
| **[dsh-repair-order-qc](https://github.com/PerryLink/dsh-repair-order-qc)** |  |
| **[dsh-research-report](https://github.com/PerryLink/dsh-research-report)** |  |
| **[dsh-review-reply-check](https://github.com/PerryLink/dsh-review-reply-check)** |  |
| **[dsh-rulefile-check](https://github.com/PerryLink/dsh-rulefile-check)** |  |
| **[dsh-safety-brief-check](https://github.com/PerryLink/dsh-safety-brief-check)** |  |
| **[dsh-score](https://github.com/PerryLink/dsh-score)** |  |
| **[dsh-session-sync](https://github.com/PerryLink/dsh-session-sync)** |  |
| **[dsh-site-log-check](https://github.com/PerryLink/dsh-site-log-check)** |  |
| **[dsh-skill-pack-security](https://github.com/PerryLink/dsh-skill-pack-security)** |  |
| **[dsh-soe-decision-check](https://github.com/PerryLink/dsh-soe-decision-check)** |  |
| **[dsh-soilwater-check](https://github.com/PerryLink/dsh-soilwater-check)** |  |
| **[dsh-sop-sync-check](https://github.com/PerryLink/dsh-sop-sync-check)** |  |
| **[dsh-spc-gbt-adapter](https://github.com/PerryLink/dsh-spc-gbt-adapter)** |  |
| **[dsh-talk](https://github.com/PerryLink/dsh-talk)** |  |
| **[dsh-tender-extract](https://github.com/PerryLink/dsh-tender-extract)** |  |
| **[dsh-tender-matrix](https://github.com/PerryLink/dsh-tender-matrix)** |  |
| **[dsh-test-drive](https://github.com/PerryLink/dsh-test-drive)** |  |
| **[dsh-ticktick](https://github.com/PerryLink/dsh-ticktick)** |  |
| **[dsh-translate](https://github.com/PerryLink/dsh-translate)** |  |
| **[dsh-warranty-calc](https://github.com/PerryLink/dsh-warranty-calc)** |  |
| **[dsh-budget](https://github.com/PerryLink/dsh-budget)** | 🧊 已冻结 — 见仓库 README |
| **[dsh-claude-move](https://github.com/PerryLink/dsh-claude-move)** | 🧊 已冻结 — 见仓库 README |
| **[dsh-defend](https://github.com/PerryLink/dsh-defend)** | 🧊 已冻结 — 见仓库 README |
| **[dsh-draw](https://github.com/PerryLink/dsh-draw)** | 🧊 已冻结 — 见仓库 README |
| **[dsh-reach](https://github.com/PerryLink/dsh-reach)** | 🧊 已冻结 — 见仓库 README |
| **[dsh-background-agents](https://github.com/PerryLink/dsh-background-agents)** | 🚫 已退役 — 见仓库 README |
| **[dsh-session-pin](https://github.com/PerryLink/dsh-session-pin)** | 🚫 已退役 — 见仓库 README |
| **[dsh-team-rooms](https://github.com/PerryLink/dsh-team-rooms)** | 🚫 已退役 — 见仓库 README |

</details>

## License

[Apache License 2.0](LICENSE) © 2026 dsh-hazplan-check contributors.
