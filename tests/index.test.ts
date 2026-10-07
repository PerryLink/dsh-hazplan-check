import { readFile, readdir } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { loadRuleset } from '../src/shared/ruleset.ts'
import { parseMaterial } from '../src/parse.ts'
import { runCheck } from '../src/check.ts'
import { buildView } from '../src/view.ts'
import { findForbiddenWording } from '../src/shared/wording.ts'
import { addDays, diffDays, parseWallClock } from '../src/shared/datetime.ts'
import { parseYaml } from '../src/shared/yaml.ts'
import { Config as ConfigSchema } from '../src/config.ts'
import { inject, name as pluginName, resolvePackageFile, TOOL_NAME } from '../src/index.ts'
import type { Report } from '../src/shared/report.ts'
import type { CheckOptions } from '../src/check.ts'

const here = dirname(fileURLToPath(import.meta.url))
const packageRoot = resolve(here, '..')
const rulesPath = join(packageRoot, 'rules', 'hazplan-check.yaml')
const fixturesRoot = join(here, 'fixtures')
const CHECKED_AT = '2026-10-06T00:00:00.000Z'

interface CaseFile {
  ruleId: string
  configure?: Record<string, Record<string, unknown>>
  pairs: { name: string; material: string; expect: { ruleId: string; count: number } }[]
}

async function loadPack() {
  return loadRuleset(await readFile(rulesPath, 'utf8'))
}

function runOptions(overrides: Partial<CheckOptions> = {}): CheckOptions {
  return { plugin: pluginName, checkedAt: CHECKED_AT, disabledRules: [], onlyRules: [], ...overrides }
}

function withConfiguration(ruleset: Awaited<ReturnType<typeof loadPack>>, configure: CaseFile['configure']) {
  if (configure === undefined) return ruleset
  return {
    ...ruleset,
    rules: ruleset.rules.map((rule) =>
      configure[rule.id] === undefined ? rule : { ...rule, params: { ...rule.params, ...configure[rule.id] } },
    ),
  }
}

async function runFixture(materialText: string, target: string, configure?: CaseFile['configure']): Promise<Report> {
  const ruleset = withConfiguration(await loadPack(), configure)
  return runCheck(parseMaterial(materialText, target), ruleset, runOptions())
}

function issuesOf(report: Report, ruleId: string) {
  return report.issues.filter((issue) => issue.ruleId === ruleId)
}

async function ruleDirectories(): Promise<string[]> {
  const entries = await readdir(fixturesRoot, { withFileTypes: true })
  return entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort()
}

async function readCases(directory: string): Promise<CaseFile> {
  return JSON.parse(await readFile(join(fixturesRoot, directory, 'cases.json'), 'utf8')) as CaseFile
}

const GOOD_ROW = {
  节点: '进料单元',
  工艺参数: '流量',
  引导词: '无',
  偏差: '无流量',
  原因: '进料泵故障',
  后果: '反应器液位下降',
  现有安全措施: '液位低报警',
  风险等级: '中',
}
const GOOD = { subject: '某装置 HAZOP 分析', rows: [GOOD_ROW] }

describe('rule pack', () => {
  it('declares a citable basis for every rule', async () => {
    const ruleset = await loadPack()
    expect(ruleset.plugin).toBe(pluginName)
    expect(ruleset.rules.length).toBeGreaterThanOrEqual(6)
    for (const rule of ruleset.rules) {
      expect(rule.basis.document, `${rule.id} document`).not.toBe('')
      expect(rule.basis.clause, `${rule.id} clause`).not.toBe('')
      expect(rule.basis.excerpt.length, `${rule.id} excerpt`).toBeGreaterThanOrEqual(8)
      expect(rule.basis.source, `${rule.id} source`).toMatch(/^https?:\/\//)
      expect(['direct', 'derived-from-principle', 'institutional-configuration']).toContain(rule.basis.kind)
    }
  })

  it('never lets a principle-derived or locally configured check be an error', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      if (rule.basis.kind === 'derived-from-principle') expect(rule.severity, rule.id).not.toBe('error')
      if (rule.basis.kind === 'institutional-configuration') expect(rule.severity, rule.id).toBe('info')
    }
  })

  it('cites the standard verbatim and reserves error for nothing, since every clause says 宜', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      expect(rule.basis.excerpt, rule.id).not.toContain('本次未取得')
      expect(rule.basis.number, rule.id).toBe('GB/T 35320-2017')
    }
    // GB/T 35320-2017 is a recommended standard and every clause this pack cites uses 宜, so no
    // rule may be an error. Pinning this stops a later edit from silently re-escalating one.
    const errors = ruleset.rules.filter((rule) => rule.severity === 'error').map((rule) => rule.id)
    expect(errors).toEqual([])
    const hz001 = ruleset.rules.find((rule) => rule.id === 'HZ-001')
    const hz002 = ruleset.rules.find((rule) => rule.id === 'HZ-002')
    expect(hz001?.basis.clause).toBe('6.6.4')
    expect(hz002?.basis.clause).toBe('6.6.3')
    // The quoted words themselves must keep the standard's modal force.
    expect(hz001?.basis.excerpt).toContain('宜')
    expect(hz002?.basis.excerpt).not.toContain('应')
  })

  it('records that appendix A.2 is informative, so a missing column is never a failure', async () => {
    const ruleset = await loadPack()
    const header = ruleset.rules.find((rule) => rule.id === 'HZ-006')
    expect(header?.basis.clause).toContain('资料性')
    expect(header?.severity).toBe('warn')
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('**不存在强制列清单**')
    expect(source).toContain('SH/T 3240-2025 只核实了编号/名称/状态/日期与术语表')
  })

  it('uses the standard 相反 rather than the colloquial 相逆, and states the guide-word tables', async () => {
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('国标用「相反」（不是"相逆"）')
    expect(source).toContain('表1 给出工艺参数类引导词')
    expect(source).toContain('表2 给出与时间和先后顺序相关的引导词')
  })

  it('says plainly which four judgements it does not make', async () => {
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('**不判断原因是否找全、后果是否分析到位、安全措施是否充分、风险定级是否恰当**')
  })

  it('refuses a rule pack that overstates a principle-derived check', () => {
    const overstated = [
      'plugin: probe',
      'version: "0"',
      'rules:',
      '  - id: X-001',
      '    title: probe',
      '    severity: error',
      '    basis:',
      '      document: 《X》',
      '      number: X〔2020〕1号',
      '      clause: 第一条',
      '      excerpt: 这是一个足够长的逐字摘录示例。',
      '      kind: derived-from-principle',
      '      source: https://example.invalid/x',
    ].join('\n')
    expect(() => loadRuleset(overstated)).toThrow(/strongest permitted severity/)
  })
})

describe('paired fixtures', () => {
  it('has both a compliant and a violating sample for every rule', async () => {
    const ruleset = await loadPack()
    const covered = new Set<string>()
    for (const directory of await ruleDirectories()) {
      const cases = await readCases(directory)
      expect(cases.pairs.filter((pair) => pair.expect.count === 0).length, `${directory} compliant sample`).toBeGreaterThanOrEqual(1)
      expect(cases.pairs.filter((pair) => pair.expect.count > 0).length, `${directory} violating sample`).toBeGreaterThanOrEqual(1)
      for (const pair of cases.pairs) {
        const material = await readFile(join(fixturesRoot, directory, pair.material), 'utf8')
        const report = await runFixture(material, pair.material, cases.configure)
        const matched = issuesOf(report, cases.ruleId)
        expect(
          matched.length,
          `${directory}/${pair.name} expected ${pair.expect.count} × ${cases.ruleId}, got ${matched.map((issue) => issue.found).join(' | ')}`,
        ).toBe(pair.expect.count)
        covered.add(cases.ruleId)
      }
    }
    for (const rule of ruleset.rules) expect(covered.has(rule.id), `covered ${rule.id}`).toBe(true)
  })

  it('gives every issue a citable basis and a stable id', async () => {
    for (const directory of await ruleDirectories()) {
      const cases = await readCases(directory)
      for (const pair of cases.pairs) {
        const material = await readFile(join(fixturesRoot, directory, pair.material), 'utf8')
        const report = await runFixture(material, pair.material, cases.configure)
        for (const issue of report.issues) {
          expect(issue.basis).toContain('「')
          expect(issue.id).toMatch(/^dsh-hazplan-check\.HZ-\d{3}\.[0-9a-f]{8}$/)
          expect(issue.found).not.toBe('')
          expect(issue.expected).not.toBe('')
        }
      }
    }
  })
})

describe('deviation derivation', () => {
  it('accepts the separator and word-order variants a sheet may use', async () => {
    const ruleset = await loadPack()
    const variants = [
      { 工艺参数: '流量', 引导词: '无', 偏差: '流量无' },
      { 工艺参数: '流量', 引导词: '过高', 偏差: '流量 + 过高' },
      { 工艺参数: '温度', 引导词: '偏低', 偏差: '温度、偏低' },
      { 工艺参数: '压力', 引导词: '高', 偏差: '压力的高' },
    ]
    for (const variant of variants) {
      const material = JSON.stringify({ subject: 'x', rows: [{ ...GOOD_ROW, ...variant }] })
      const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
      expect(issuesOf(report, 'HZ-002'), JSON.stringify(variant)).toHaveLength(0)
    }
  })

  it('skips rather than guesses when a column is missing', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({ subject: 'x', rows: [{ 节点: '甲', 偏差: '无流量', 原因: '泵故障' }] })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    expect(issuesOf(report, 'HZ-007')).toHaveLength(0)
    expect(report.skipped.find((entry) => entry.rule === 'HZ-007')?.reason).toContain('三列')
  })

  it('reads the English column names a commercial tool exports', () => {
    const input = parseMaterial(
      JSON.stringify({ subject: 'x', rows: [{ Node: 'N1', Parameter: 'Flow', 'Guide Word': 'No', Deviation: 'No flow' }] }),
      'inline',
    )
    expect(input.rows[0]?.parameter).toBe('Flow')
    expect(input.rows[0]?.guideWord).toBe('No')
    expect(input.rows[0]?.deviation).toBe('No flow')
  })
})

describe('skipped reporting', () => {
  it('names the clause-supplied fallback when the field list is left empty', async () => {
    const ruleset = await loadPack()
    const rule = ruleset.rules.find((entry) => entry.id === 'HZ-001')
    // HZ-001 needs no configuration: 6.6.4 itself supplies the required pair.
    expect(rule?.params.requiredFields).toEqual([])
    expect(rule?.note).toContain('把 requiredFields 配成 [偏差, 原因]')
    const report = await runFixture(JSON.stringify({ subject: 'x', rows: [GOOD_ROW] }), 'inline')
    // GOOD_ROW carries 偏差 and 原因, so the fallback pair is satisfied.
    expect(issuesOf(report, 'HZ-001')).toHaveLength(0)
  })

  it('reports a missing cause as well as a missing deviation, per 6.6.4', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({ subject: 'x', rows: [{ ...GOOD_ROW, 原因: '' }] })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    const issue = issuesOf(report, 'HZ-001')[0]
    expect(issue?.found).toContain('缺少 原因')
    expect(issue?.expected).toContain('与其原因一起记录')
  })

  it('admits that the risk vocabulary is not configured', async () => {
    const report = await runFixture(JSON.stringify(GOOD), 'inline')
    expect(report.skipped.find((entry) => entry.rule === 'HZ-005')?.reason).toContain('未配置 riskLevels')
  })

  it('warns when the sheet declares no subject', () => {
    const input = parseMaterial(JSON.stringify({ rows: [GOOD_ROW] }), 'inline')
    expect(input.warnings.join(' ')).toContain('未声明分析对象')
  })

  it('names disabled rules exactly once and appends the configured note', async () => {
    const ruleset = await loadPack()
    const input = parseMaterial(JSON.stringify(GOOD), 'inline')
    const report = runCheck(input, ruleset, runOptions({ disabledRules: ['HZ-006'], skipNotes: '本机构分析模板' }))
    const entries = report.skipped.filter((item) => item.rule === 'HZ-006')
    expect(entries).toHaveLength(1)
    expect(entries[0]?.reason).toContain('禁用')
    expect(entries[0]?.reason).toContain('本机构分析模板')
  })
})

describe('report rendering', () => {
  it('never uses adjudicating wording and always carries the disclaimer', async () => {
    const material = await readFile(join(fixturesRoot, 'HZ-002', 'HZ-002-unsafe.json'), 'utf8')
    const report = await runFixture(material, 'HZ-002-unsafe.json')
    const view = buildView(report)
    expect(findForbiddenWording(view.markdown)).toEqual([])
    expect(view.markdown).toContain('免责声明')
    expect(view.markdown).toContain('未执行的检查')
    expect(JSON.parse(view.reportJson)).toMatchObject({ plugin: pluginName, summary: report.summary })
  })
})

describe('plugin contract', () => {
  it('declares a static inject array covering every service apply touches', () => {
    expect(Array.isArray(inject)).toBe(true)
    expect(inject).toContain('tools')
  })

  it('exposes a Schemastery Config with serializable defaults', () => {
    const resolved = ConfigSchema(null)
    expect(resolved.rulesFile).toBe('rules/hazplan-check.yaml')
    expect(resolved.disabledRules).toEqual([])
    expect(resolved.timeoutMs).toBeGreaterThan(0)
  })

  it('resolves the packaged rule pack and rejects a missing one', () => {
    expect(resolvePackageFile('rules/hazplan-check.yaml')).toBe(rulesPath)
    expect(() => resolvePackageFile('rules/does-not-exist.yaml')).toThrow(/未找到/)
  })

  it('names the tool after the package family convention', () => {
    expect(TOOL_NAME).toBe('hazplan_check')
  })
})

describe('material reader', () => {
  it('rejects empty material instead of reporting an empty result', () => {
    expect(() => parseMaterial('   ', 'inline')).toThrow(/材料为空/)
  })

  it('rejects a sheet with no recognisable HAZOP columns', () => {
    expect(() => parseMaterial(JSON.stringify({ rows: [{ 备注: '甲' }] }), 'inline')).toThrow(/没有可识别的 HAZOP 工作表列/)
  })

  it('rejects material without rows', () => {
    expect(() => parseMaterial('subject: x', 'inline')).toThrow(/rows/)
  })
})

describe('shared kit', () => {
  it('parses wall-clock timestamps and rejects impossible dates', () => {
    expect(parseWallClock('2026-03-15')).toEqual({ date: '2026-03-15', time: '00:00', hasTime: false, minutes: 0 })
    expect(parseWallClock('2026-02-30')).toBeUndefined()
  })

  it('does calendar arithmetic', () => {
    expect(addDays('2026-03-31', 1)).toBe('2026-04-01')
    expect(diffDays('2026-03-01', '2026-03-06')).toBe(5)
  })

  it('reads the supported YAML subset and rejects the rest', () => {
    expect(parseYaml('a: 1\nb:\n  - x\n')).toEqual({ a: 1, b: ['x'] })
    expect(() => parseYaml('a: 1\na: 2\n')).toThrow(/duplicate/)
  })
})
