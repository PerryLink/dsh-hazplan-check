/**
 * Input contract for the HAZOP worksheet checker.
 *
 * The material is one analysis worksheet: a list of rows, each a node/parameter/
 * guide-word combination with its causes, consequences, safeguards and actions.
 * The checker works on the sheet's own text — it never re-derives the analysis,
 * because whether a cause list is complete is the study team's judgement and no
 * amount of string handling can replace it.
 */

/** One worksheet row. */
export interface WorksheetRow {
  /** 1-based row number in the source. */
  row: number
  /** 节点. */
  node?: string
  /** 设计意图. */
  intent?: string
  /** 工艺参数. */
  parameter?: string
  /** 引导词. */
  guideWord?: string
  /** 偏差, as written on the sheet. */
  deviation?: string
  /** 原因. */
  causes?: string
  /** 后果. */
  consequences?: string
  /** 现有安全措施. */
  safeguards?: string
  /** 建议措施. */
  recommendations?: string
  /** 风险等级, as written. */
  riskLevel?: string
  /** 严重性, as written. */
  severity?: string
  /** 可能性, as written. */
  likelihood?: string
  /** Values keyed by the sheet's own column names. */
  fields: Record<string, string>
  /** The same values under their original column names, for diagnostics. */
  raw: Record<string, string>
}

/** The whole normalized input. */
export interface WorksheetInput {
  target: string
  /** 分析对象/装置名称, when declared. */
  subject?: string
  /** Analysis revision or date, when declared. */
  revision?: string
  rows: WorksheetRow[]
  /** Column names the reader saw, in order. */
  columns: string[]
  warnings: string[]
}

/** Column names recognised as each field, in priority order. */
export const COLUMNS = {
  node: ['节点', '分析节点', 'node'],
  intent: ['设计意图', '意图', 'intent', '设计目的'],
  parameter: ['工艺参数', '参数', 'parameter'],
  guideWord: ['引导词', 'guideword', 'guide word', 'guideWord'],
  deviation: ['偏差', '偏差描述', 'deviation'],
  causes: ['原因', '可能原因', '偏差原因', 'causes', 'cause'],
  consequences: ['后果', '偏差后果', '可能后果', 'consequences', 'consequence'],
  safeguards: ['现有安全措施', '安全措施', '现有措施', 'safeguards', 'safeguard'],
  recommendations: ['建议措施', '建议', '整改建议', 'recommendations', 'action'],
  riskLevel: ['风险等级', '风险级别', 'risklevel', 'risk level', '风险'],
  severity: ['严重性', '后果严重性', 'severity'],
  likelihood: ['可能性', '发生可能性', 'likelihood'],
} as const

/** The deviation separator a sheet may use between parameter and guide word. */
export const DEVIATION_SEPARATORS = ['', ' ', '+', '＋', '、', '/', '-', '—'] as const
