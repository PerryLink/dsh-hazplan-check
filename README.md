# dsh-hazplan-check

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

| Surface | Status |
|---|---|
| Harness | Peer range `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verified to accept both `0.2.0-rc.2` and `0.2.1-alpha.1`. `engines.dsh` is deliberately not declared: it has no reader and cannot reject a host |
| Node | `^22.19.0 || >=24.0.0` |
| Platforms | All (plain ESM; no native code, no network, no model call) |
| Tool mode | Works in `native`, `ptc` and `both`; for several worksheets use `ptc` |

## What it does

Registers the `hazplan_check` tool. It reads one worksheet — rows keyed by the sheet's own column names,
in Chinese or English — applies a versioned rule pack, and returns a report.

| Rule | Check | Severity | Basis |
|---|---|---|---|
| `HZ-001` | every problem is its own row, with its cause | warn | 6.6.4 |
| `HZ-002` | every analysed node is recorded on the sheet | warn | 6.6.3 |
| `HZ-003` | guide words come from table 1 + table 2, or were declared first | warn | 表1、表2 + 6.4.3 |
| `HZ-004` | the row shows which element the deviation came from | warn | 3.3 + 6.4.3 |
| `HZ-005` | risk levels come from your risk criteria (off by default) | info | 6.5 + GB/T 27921 |
| `HZ-006` | the sheet names its analysis subject | warn | 附录A.2（资料性） |
| `HZ-007` | the deviation is the parameter read through its guide word | warn | 6.4.3 |

## Install

```sh
dsh plugin --profile <name> add dsh-hazplan-check
dsh --profile <name> --dump-config | grep 'dsh-hazplan-check'
```

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `rulesFile` | string | `rules/hazplan-check.yaml` | Rule-pack path, relative to the package root |
| `disabledRules` | string[] | `[]` | Rule ids to stop running; each appears in `skipped` |
| `onlyRules` | string[] | `[]` | Run only these rule ids; empty runs every rule |
| `skipNotes` | string | `""` | Note appended to every `skipped` reason |
| `timeoutMs` | number | `120000` | Cooperative tool timeout budget |

Rule-level parameters worth knowing:

- `HZ-001` `requiredFields` — the columns every row must fill. Left empty it falls back to the pair the
  clause itself names: `[偏差, 原因]`.
- `HZ-005` `riskLevels` — your risk vocabulary, e.g. `[高, 中, 低]` or `[Ⅰ, Ⅱ, Ⅲ, Ⅳ]`. Empty means the
  rule does not run. It can also be passed per call.
- `HZ-003` `guideWords` — the guide-word list your study declared before the meeting, when it uses its
  own under 6.4.3. Empty means the standard's tables 1 and 2 are used.
- `HZ-006` `requireHeader` — set to `false` if your sheet legitimately carries no subject line.

The plugin's own configuration also accepts `riskLevels` and `guideWords`, so a deployment can set the
risk vocabulary and the declared guide words once for every call rather than passing them each time.

## Material format

The tool accepts JSON or YAML. Rows are keyed by the sheet's own column names; **Chinese and English names
both work**, so an export from a commercial HAZOP tool loads without editing:

```yaml
subject: 某装置 HAZOP 分析
revision: V1.0
rows:
  - { 节点: 进料单元, 设计意图: 将原料按设计流量送入反应器, 工艺参数: 流量, 引导词: 无,
      偏差: 无流量, 原因: 进料泵故障, 后果: 反应器液位下降, 现有安全措施: 液位低报警,
      建议措施: 增加进料泵备用泵, 风险等级: 中, 责任人: 张工, 完成期限: 2026-06-30 }
  - { Node: N2, Parameter: Temperature, "Guide Word": High, Deviation: High temperature,
      Causes: Cooling failure, Consequences: Runaway, Safeguards: High-temp trip }
```

Column names are matched case-insensitively and ignoring spaces, underscores and hyphens, so `Guide Word`,
`guide_word` and `guideword` all resolve to the same field.

`HZ-002` compares the deviation against the parameter+guide-word combination over a set of separators
(`, `, `+`, `、`, `/`, `-`, `—`, `的`, `：`) and in both word orders, so `流量无`, `流量 + 无` and `无流量`
all pass. It reports a mismatch as a likely copy-paste artefact — not as a claim that the deviation is
technically wrong.

## Rule sources

Rule data lives in `rules/hazplan-check.yaml`. Every rule carries a document, a document number, a clause
in the source's own numbering, a verbatim excerpt and the URL the excerpt was read from. The loader
enforces that an excerpt is a real quotation of at least eight characters, and that a check resting on a
general principle or a local policy can never be declared `error`.

The clauses quoted come from **GB/T 35320-2017** — 3.3, 4.2, 6.4.3, 6.5, 6.6.3, 6.6.4, tables 1 and 2,
and appendix A.2 — plus **GB/T 27921-2023** appendix B.10.3 for the risk-matrix description. The clause
text was read from a full-text transcription whose structure cross-checks against the standard's official
metadata; the pack records that the source is a transcription.

Four findings shaped this pack and are recorded in its header:

1. **Appendix A.2 is informative**, so its column list is a suggestion and never a requirement.
2. **Clause 4.2 gives no criterion for node size**, so node granularity is not automatically judged.
3. **The standard fixes no risk-level scale**, so levels are yours and the vocabulary ships empty.
4. **SH/T 3240-2025 exists but its clause text was not obtained**, so no article of it is cited — only its
   identity is noted, in the pack header.

The full clause-verification report, including the sources that were checked and rejected, is in
`rules/evidence/clause-verification.md`.

## Troubleshooting

- **`HZ-001`, `HZ-003` or `HZ-005` report themselves as skipped.** Their lists are empty. Fill in the ones
  your template uses.
- **`HZ-002` fires on a row that reads fine to me.** Your sheet may write a fuller deviation than
  `参数+引导词`. The rule says "likely a copy-paste artefact"; either normalise the column or accept it as
  noise. It never blocks anything.
- **`HZ-002` reports nothing.** The sheet does not carry all three of 工艺参数, 引导词 and 偏差 — the rule
  says so in `skipped` rather than guessing.
- **The reader refuses a worksheet it used to accept.** It found none of the known column names; the error
  names the columns it saw. Rename one column or add the name to `COLUMNS` in `src/model.ts`-adjacent
  configuration.
- **The plugin installs but the tool never appears.** Check that `main` resolves to `lib/index.mjs` and
  that `pnpm run build` produced it; a wrong `main` makes the loader skip the entry silently.
- **`dsh plugin add` refuses the package as incompatible.** The peer range covers `0.1.x` and `0.2.x`; if
  your runtime sits outside it, grant an explicit exemption:
  `dsh plugin --profile <name> allow-version dsh-hazplan-check@0.1.0 --dsh-version <runtime> --accept-risk`
- **`check` reports `manifest-peers` as failed.** The static checker compares against a hard-coded peer
  range that predates the 0.2 line. The runtime enforces peer compatibility at install time, so the
  declared range is the correct one; this is a known upstream issue in `dsh-plugin-dev`.

## Development

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm test            # vitest, paired fixtures per rule
pnpm run build       # tsdown -> lib/index.mjs + lib/index.d.mts
node ../scripts/sync-shared.mjs dsh-hazplan-check   # refresh src/shared from ../_shared
```

## License

[Apache License 2.0](LICENSE) © 2026 dsh-hazplan-check contributors.
