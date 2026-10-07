/**
 * Reader for the HAZOP worksheet.
 *
 * The material is JSON or YAML with a `rows` list, each row a mapping of the
 * sheet's own column names. Known column names are recognised in either Chinese
 * or English so an export from a commercial HAZOP tool loads without editing.
 */

import { YamlSubsetError, parseYaml } from './shared/yaml.ts'
import { COLUMNS } from './model.ts'
import type { WorksheetInput, WorksheetRow } from './model.ts'

/** Raised when the material cannot be read at all. */
export class MaterialError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'MaterialError'
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function text(value: unknown): string | undefined {
  if (value === undefined || value === null) return undefined
  if (typeof value === 'string') return value.trim() === '' ? undefined : value.trim()
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return undefined
}

/** Find the first present value among a set of candidate column names. */
function pick(fields: Record<string, string>, names: readonly string[]): string | undefined {
  for (const name of names) {
    const value = fields[name]
    if (value !== undefined && value !== '') return value
    // Commercial exports vary capitalisation and spacing.
    const loose = Object.keys(fields).find((key) => key.toLowerCase().replace(/[\s_-]/g, '') === name.toLowerCase().replace(/[\s_-]/g, ''))
    if (loose !== undefined) {
      const looseValue = fields[loose]
      if (looseValue !== undefined && looseValue !== '') return looseValue
    }
  }
  return undefined
}

function parseRow(raw: unknown, index: number): WorksheetRow {
  if (!isRecord(raw)) throw new MaterialError(`rows[${index}] 必须是映射`)
  const fields: Record<string, string> = {}
  for (const [key, value] of Object.entries(raw)) {
    if (value === undefined || value === null) continue
    const rendered = typeof value === 'string' ? value.trim() : text(value)
    fields[key] = rendered ?? ''
  }
  const row: WorksheetRow = { row: index + 1, fields, raw: { ...fields } }
  const declared = text(raw.row)
  if (declared !== undefined && /^\d+$/.test(declared)) row.row = Number.parseInt(declared, 10)

  for (const [field, names] of Object.entries(COLUMNS) as [keyof typeof COLUMNS, readonly string[]][]) {
    const value = pick(fields, names)
    if (value === undefined) continue
    row[field] = value
  }
  return row
}

/** True when the sheet carries at least one column this reader understands. */
function hasRecognisedColumn(columns: readonly string[]): boolean {
  const normalize = (value: string): string => value.toLowerCase().replace(/[\s\u3000_-]/g, '')
  const known = new Set(
    [...COLUMNS.node, ...COLUMNS.deviation, ...COLUMNS.causes, ...COLUMNS.consequences].map(normalize),
  )
  return columns.some((column) => known.has(normalize(column)))
}

/**
 * Parse material into the normalized input contract.
 * @param source - JSON or YAML text.
 * @param target - description of where the material came from.
 * @returns the normalized input.
 */
export function parseMaterial(source: string, target: string): WorksheetInput {
  const trimmed = source.trim()
  if (trimmed === '') throw new MaterialError('材料为空')
  let document: unknown
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      document = JSON.parse(trimmed)
    } catch (error) {
      throw new MaterialError(`JSON 无法解析：${error instanceof Error ? error.message : String(error)}`)
    }
  } else {
    try {
      document = parseYaml(trimmed)
    } catch (error) {
      if (error instanceof YamlSubsetError) throw new MaterialError(`YAML 无法解析：${error.message}`)
      throw error
    }
  }

  const warnings: string[] = []
  let list: unknown
  let subject: string | undefined
  let revision: string | undefined
  if (Array.isArray(document)) {
    list = document
  } else if (isRecord(document)) {
    list = document.rows ?? document.items ?? document.工作表
    subject = text(document.subject ?? document.分析对象 ?? document.装置名称)
    revision = text(document.revision ?? document.版本 ?? document.日期)
  } else {
    throw new MaterialError('材料根节点必须是映射或列表')
  }

  if (list === undefined || list === null) throw new MaterialError('材料缺少 rows 列表，无法执行检查')
  if (!Array.isArray(list)) throw new MaterialError('rows 必须是列表')
  if (list.length === 0) throw new MaterialError('rows 为空列表，无法执行检查')

  const rows = list.map((entry, index) => parseRow(entry, index))
  const columns = [...new Set(rows.flatMap((row) => Object.keys(row.fields)))]
  if (!hasRecognisedColumn(columns)) {
    throw new MaterialError(
      `材料中没有可识别的 HAZOP 工作表列，已识别的列名为：${columns.join(' / ') || '（无）'}；` +
        `请至少提供以下之一：${[...COLUMNS.node, ...COLUMNS.deviation, ...COLUMNS.causes, ...COLUMNS.consequences].join(' / ')}`,
    )
  }

  const input: WorksheetInput = { target, rows, columns, warnings }
  if (subject !== undefined) input.subject = subject
  if (revision !== undefined) input.revision = revision
  if (subject === undefined) warnings.push('材料未声明分析对象（subject），按对象核对的检查将无法执行')
  return input
}
