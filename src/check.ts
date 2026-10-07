/**
 * Pure check core: `(input, ruleset, options) => Report`.
 *
 * No plugin context, no I/O, no clock and no model access, so the whole rule set
 * is unit-testable without credentials. Every finding carries the verbatim clause
 * that produced it, and every check that could not run is reported in `skipped`
 * so an empty issue list can never be read as "the analysis is complete".
 *
 * The checks are about the worksheet's **internal consistency and traceability**:
 * does every row record one problem and its node, do the guide words come from the
 * standard's tables, is the deviation the parameter read through its guide word.
 * Whether the cause lists are technically complete is the study team's judgement
 * and nothing here attempts it.
 */

import { disabledAsSkipped, formatBasis } from './shared/rules.ts'
import { paramStrings, ruleById } from './shared/ruleset.ts'
import { issueId, makeReport } from './shared/report.ts'
import { COLUMNS } from './model.ts'
import type { Issue, Locator, Report, Skipped } from './shared/report.ts'
import type { Ruleset } from './shared/rules.ts'
import type { WorksheetInput, WorksheetRow } from './model.ts'

/** Options that come from the plugin configuration rather than the rule pack. */
export interface CheckOptions {
  plugin: string
  checkedAt: string
  disabledRules: readonly string[]
  onlyRules: readonly string[]
  /** Risk levels the deployment's risk criteria use. */
  riskLevels?: readonly string[]
  /** Guide words the study declared before the meeting, when it uses its own. */
  guideWords?: readonly string[]
  skipNotes?: string
}

interface RuleContext {
  input: WorksheetInput
  ruleset: Ruleset
  issues: Issue[]
  skipped: Skipped[]
  fired: Set<string>
  skipReasons: Map<string, string>
  options: CheckOptions
  add(ruleId: string, locator: Locator, found: string, expected: string, fix?: string): void
  skip(ruleId: string, reason: string): void
}

function locatorOf(row: WorksheetRow, column?: string): Locator {
  const locator: Locator = { row: row.row }
  if (column !== undefined) locator.column = column
  return locator
}

function makeAdd(context: Omit<RuleContext, 'add' | 'skip'>): RuleContext['add'] {
  return (ruleId, locator, found, expected, fix) => {
    const rule = ruleById(context.ruleset, ruleId)
    const issue: Issue = {
      id: issueId(context.ruleset.plugin, ruleId, locator),
      ruleId,
      severity: rule.severity,
      locator,
      found,
      expected,
      basis: formatBasis(rule.basis, rule.alsoBasis ?? []),
    }
    if (fix !== undefined) issue.fix = fix
    context.issues.push(issue)
    context.fired.add(ruleId)
  }
}

/** True when the cell carries something. */
function filled(value: string | undefined): boolean {
  return value !== undefined && value.trim() !== ''
}

/** The guide words of the standard's tables 1 and 2, plus the common variants. */
const STANDARD_GUIDE_WORDS = new Set([
  '无',
  '没有',
  '多',
  '过量',
  '少',
  '减量',
  '伴随',
  '部分',
  '相反',
  '异常',
  '早',
  '晚',
  '先',
  '后',
])

/**
 * HZ-001 — 6.6.4: each problem is recorded as its own row.
 *
 * The clause also requires every problem to be recorded *together with its cause*,
 * whether or not protection already exists, so a blank cause is a gap as much as a
 * blank deviation is.
 */
function checkRowCompleteness(context: RuleContext): void {
  const ruleId = 'HZ-001'
  const rule = ruleById(context.ruleset, ruleId)
  const declared = paramStrings(rule, 'requiredFields', [])
  const required = declared.length > 0 ? declared : ['偏差', '原因']
  for (const row of context.input.rows) {
    const missing = required.filter((field) => !filled(row.fields[field]))
    if (missing.length === 0) continue
    context.add(
      ruleId,
      locatorOf(row),
      `第 ${row.row} 行缺少 ${missing.join('、')}`,
      `每一个危险和可操作性问题都应作为单项记录，并与其原因一起记录；本机构配置的必填项为 ${required.join('、')}`,
      '补齐栏目；本条只核对是否填写，不判断该问题是否找全',
    )
  }
}

/** HZ-002 — 6.6.3: the output lists every analysed node. */
function checkNodeRecorded(context: RuleContext): void {
  const ruleId = 'HZ-002'
  const blank = context.input.rows.filter((row) => !filled(row.node))
  if (blank.length === 0) return
  context.add(
    ruleId,
    locatorOf((blank[0] as WorksheetRow), COLUMNS.node[0] as string),
    `${blank.length} 行没有写明节点（行号：${blank.map((row) => row.row).join('、')}）`,
    '分析输出应能列出所有分析的节点清单，以及没有被分析节点的理由',
    '补填节点；本条只核对节点是否填写，不判断节点划分粒度是否恰当',
  )
}

/** HZ-003 — the guide words come from the standard's tables, or were declared. */
function checkGuideWords(context: RuleContext): void {
  const ruleId = 'HZ-003'
  const rule = ruleById(context.ruleset, ruleId)
  const configured = context.options.guideWords ?? paramStrings(rule, 'guideWords', [])
  const allowed = new Set(configured.length > 0 ? configured : [...STANDARD_GUIDE_WORDS])
  const withWord = context.input.rows.filter((row) => filled(row.guideWord))
  if (withWord.length === 0) {
    context.skip(ruleId, '材料没有可识别的引导词列或该列全为空，本条不适用')
    return
  }
  const outside = withWord.filter((row) => !allowed.has((row.guideWord ?? '').trim()))
  if (outside.length === 0) return
  const values = [...new Set(outside.map((row) => (row.guideWord ?? '').trim()))]
  context.add(
    ruleId,
    locatorOf((outside[0] as WorksheetRow), COLUMNS.guideWord[0] as string),
    `${outside.length} 行使用了清单之外的引导词：${values.join('、')}`,
    configured.length > 0
      ? `引导词应为 ${[...allowed].join(' / ')} 之一`
      : '引导词应取自 GB/T 35320-2017 表1（无/多/少/伴随/部分/相反/异常）与表2（早/晚/先/后）',
    '确认分析前是否已按 6.4.3 定义并存档该引导词；使用自定义引导词本身不必然不合规，故本条为提示级',
  )
}

/** HZ-004 — the row shows which element and guide word the deviation came from. */
function checkDeviationTraceable(context: RuleContext): void {
  const ruleId = 'HZ-004'
  // The check needs the worksheet to carry the columns at all; if no row has either
  // value, the sheet is a different shape and the rule says so rather than firing.
  const carriesColumns = context.input.columns.some(
    (column) => column === '偏差' || column === '偏差描述' || column === 'deviation' || column === '工艺参数' || column === '参数',
  )
  if (!carriesColumns) {
    context.skip(ruleId, '材料既没有偏差列也没有工艺参数列，无法核对偏离的可追溯性')
    return
  }
  for (const row of context.input.rows) {
    if (filled(row.deviation) || filled(row.parameter) || filled(row.raw.工艺参数)) continue
    context.add(
      ruleId,
      locatorOf(row),
      `第 ${row.row} 行既没有偏差也没有工艺参数`,
      '记录中应能看出「哪个要素 + 哪个引导词 → 哪个偏离」',
      '补填偏差或工艺参数；本条依据 3.3 的偏离定义与 6.4.3 的组合存档要求，属原则性推论，故为提示级',
    )
  }
}

/** HZ-005 — the risk level comes from the deployment's own criteria. */
function checkRiskVocabulary(context: RuleContext): void {
  const ruleId = 'HZ-005'
  const rule = ruleById(context.ruleset, ruleId)
  const levels = context.options.riskLevels ?? paramStrings(rule, 'riskLevels', [])
  const withLevel = context.input.rows.filter((row) => filled(row.riskLevel))
  if (withLevel.length === 0) {
    context.skip(ruleId, '材料没有可识别的风险等级列或该列全为空，本条不适用')
    return
  }
  if (levels.length === 0) {
    context.skip(
      ruleId,
      '规则库未配置 riskLevels：标准未规定风险等级刻度（6.5 只述其有用性并指向 IEC 60300-3-9），档位须来自本机构风险准则',
    )
    return
  }
  const outside = withLevel.filter((row) => !levels.includes((row.riskLevel ?? '').trim()))
  for (const row of outside) {
    context.add(
      ruleId,
      locatorOf(row, COLUMNS.riskLevel[0] as string),
      `第 ${row.row} 行风险等级「${row.riskLevel}」不在本机构配置的档位内（${levels.join(' / ')}）`,
      `风险等级应为 ${levels.join(' / ')} 之一`,
      '核对是否使用了本单位风险准则之外的档位；本条不判断该定级是否正确',
    )
  }
}

/** HZ-006 — the sheet can be identified. */
function checkSheetHeader(context: RuleContext): void {
  const ruleId = 'HZ-006'
  const rule = ruleById(context.ruleset, ruleId)
  if (rule.params.requireHeader === false) {
    context.skip(ruleId, '规则库配置为不要求工作表表头，本条不执行')
    return
  }
  if (context.input.subject !== undefined) return
  context.add(
    ruleId,
    {},
    '工作表未声明分析对象',
    '工作表表头应能识别分析对象，否则结论无法追溯到被分析的边界',
    '在材料顶层加入 subject 字段；附录 A.2 为资料性附录，故本条为提示级',
  )
}

/**
 * HZ-007 — the deviation is the parameter read through its guide word.
 *
 * This is the one fully mechanical property of a HAZOP record: a deviation is by
 * definition the parameter read through a guide word (3.3 with 6.4.3). It only
 * runs when all three columns are present, and it reports a mismatch as a likely
 * copy-paste artefact rather than a technical error.
 */
function checkDeviationDerivation(context: RuleContext): void {
  const ruleId = 'HZ-007'
  const pairs = context.input.rows.filter(
    (row) => filled(row.parameter) && filled(row.guideWord) && filled(row.deviation),
  )
  if (pairs.length === 0) {
    context.skip(
      ruleId,
      '材料没有同时提供工艺参数、引导词与偏差三列（或至少一列为空），无法核对偏差是否由参数与引导词构成',
    )
    return
  }
  const separators = ['', ' ', '+', '＋', '、', '/', '-', '—', '的', '：', ':']
  const bare = (value: string): string => value.replace(/[\s\u3000，,。.、；;：:（）()【】\[\]]/g, '').toLowerCase()
  for (const row of pairs) {
    const parameter = bare(row.parameter ?? '')
    const guideWord = bare(row.guideWord ?? '')
    const deviation = bare(row.deviation ?? '')
    const forms = new Set<string>()
    for (const separator of separators) {
      forms.add(`${parameter}${separator}${guideWord}`.replace(/\s/g, ''))
      forms.add(`${guideWord}${separator}${parameter}`.replace(/\s/g, ''))
    }
    if ([...forms].some((form) => deviation === form || deviation.includes(form))) continue
    context.add(
      ruleId,
      locatorOf(row, '偏差'),
      `第 ${row.row} 行偏差「${row.deviation}」不等同于参数「${row.parameter}」与引导词「${row.guideWord}」的组合`,
      '偏差应为工艺参数与引导词的组合，例如「流量 + 无 → 无流量」',
      '核对是否复制粘贴串行；本条只做字面组合比对，不判断该偏差在工艺上是否成立',
    )
  }
}

const CHECKERS: readonly ((context: RuleContext) => void)[] = [
  checkRowCompleteness,
  checkNodeRecorded,
  checkGuideWords,
  checkDeviationTraceable,
  checkRiskVocabulary,
  checkSheetHeader,
  checkDeviationDerivation,
]

/**
 * Run the whole rule pack against one worksheet.
 * @param input - normalized worksheet.
 * @param ruleset - validated rule pack.
 * @param options - plugin identity, clock value and rule selection.
 * @returns the report, with `skipped` listing every check that did not run.
 */
export function runCheck(input: WorksheetInput, ruleset: Ruleset, options: CheckOptions): Report {
  const disabled = new Set([...ruleset.disabled, ...options.disabledRules])
  const only = new Set(options.onlyRules)
  const base = {
    input,
    ruleset,
    issues: [] as Issue[],
    skipped: [] as Skipped[],
    fired: new Set<string>(),
    skipReasons: new Map<string, string>(),
    options,
  }
  const context: RuleContext = {
    ...base,
    add: makeAdd(base),
    skip: (ruleId, reason) => {
      base.skipReasons.set(ruleId, reason)
    },
  }

  for (const checker of CHECKERS) checker(context)

  const withNote = (reason: string): string => (options.skipNotes === undefined ? reason : `${reason}；${options.skipNotes}`)
  const skipped: Skipped[] = disabledAsSkipped(ruleset, [...disabled], withNote('该规则在当前配置中被禁用'))
  const already = new Set(skipped.map((entry) => entry.rule))
  for (const [ruleId, reason] of base.skipReasons) {
    if (already.has(ruleId)) continue
    if (disabled.has(ruleId) || (options.onlyRules.length > 0 && !only.has(ruleId))) continue
    skipped.push({ rule: ruleId, reason: withNote(reason) })
    already.add(ruleId)
  }
  for (const rule of ruleset.rules) {
    if (disabled.has(rule.id) || base.fired.has(rule.id) || already.has(rule.id)) continue
    if (options.onlyRules.length > 0 && !only.has(rule.id)) continue
    skipped.push({ rule: rule.id, reason: withNote('材料满足该检查的前置条件且未发现差异条目') })
  }
  if (options.onlyRules.length > 0) {
    const notSelected = ruleset.rules.filter((rule) => !only.has(rule.id) && !disabled.has(rule.id))
    if (notSelected.length > 0) {
      skipped.push({
        rule: notSelected.map((rule) => rule.id).join(','),
        reason: withNote(`本次调用通过 only 参数把执行范围限制为 ${[...only].join(', ')}，上列规则未执行`),
      })
    }
  }

  return makeReport({
    plugin: options.plugin,
    target: input.target,
    rulesetVersion: ruleset.version,
    checkedAt: options.checkedAt,
    issues: context.issues,
    skipped,
  })
}
