import Schema from '@deepseek-ai/schemastery'

/**
 * Every tunable lives here so an operator can change behaviour from
 * `cordis.yml` without editing code (the family's "no hard-coded tunables"
 * redline). The rule pack itself is data as well and can be pointed elsewhere.
 */
export interface Config {
  /** Rule-pack path relative to the plugin package root. */
  rulesFile: string
  /** Rule ids disabled for this deployment. */
  disabledRules: string[]
  /** When non-empty, only these rule ids run. */
  onlyRules: string[]
  /** Extra note appended to every `skipped` reason. */
  skipNotes: string
  /** Risk levels from this organisation's risk criteria. */
  riskLevels: string[]
  /** Guide words the study declared before the meeting, when it uses its own. */
  guideWords: string[]
  /** Tool timeout budget in milliseconds. */
  timeoutMs: number
}

export const Config: Schema<Config> = Schema.object({
  rulesFile: Schema.string()
    .default('rules/hazplan-check.yaml')
    .description('规则库文件路径（相对插件包根目录）。替换该文件即可切换规则集版本。'),
  disabledRules: Schema.array(Schema.string())
    .default([])
    .description('要停用的规则 id 列表；停用的规则会出现在报告的 skipped 中。'),
  onlyRules: Schema.array(Schema.string())
    .default([])
    .description('只执行这些规则 id；留空表示执行全部规则。'),
  skipNotes: Schema.string()
    .default('')
    .description('附加到每条 skipped 说明后的备注，例如标注本机构实施细则。'),
  riskLevels: Schema.array(Schema.string())
    .default([])
    .description('本机构风险准则的档位清单，例如 ["高","中","低"]。留空表示不核对风险档位。'),
  guideWords: Schema.array(Schema.string())
    .default([])
    .description('分析前自定义并存档的引导词清单（GB/T 35320-2017 6.4.3）。留空时按标准表1、表2核对。'),
  timeoutMs: Schema.number()
    .default(120000)
    .description('工具协作式超时预算（毫秒）。'),
})
