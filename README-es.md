# dsh-hazplan-check — Verificación de la completitud de los elementos de una hoja de trabajo HAZOP y de la coherencia en la derivación de las desviaciones

`dsh-hazplan-check` lee una hoja de trabajo HAZOP —filas organizadas según los propios nombres de columna de la hoja, en chino o en inglés, más una cabecera opcional que declara el 分析对象— y comprueba la completitud y la trazabilidad interna de esa misma hoja: que cada fila rellene las columnas que exige su plantilla (`偏差` y `原因` por defecto), que cada fila registre su `节点`, que los `引导词` procedan de las tablas 1 y 2 de la norma o de la lista que el estudio declaró de antemano, que cada fila deje ver de qué elemento proviene la desviación, que el `风险等级` salga del vocabulario de riesgo de su organización, que la hoja identifique el objeto de análisis y que cada `偏差` sea literalmente el `工艺参数` leído a través de su `引导词`; toda comprobación que no pueda ejecutarse por falta de una columna se informa en `skipped` en lugar de pasar en silencio.

## Qué responde

| Usted pregunta | Qué responde |
|---|---|
| Una fila registra la desviación pero deja vacía la causa. ¿Se informa de ello? | Sí. `HZ-001` exige los campos que debe rellenar cada fila; sin configurar, recurre al par que la propia cláusula nombra, `偏差` y `原因`, de modo que un `原因` vacío ya es una falta por sí solo. Comprueba que la columna esté rellena, no que la lista de problemas esté completa ni que la causa sea técnicamente válida. |
| Tres filas no llevan nodo alguno. ¿Se dice algo y se juzga cómo se dividieron los nodos? | `HZ-002` informa de esas filas en una sola entrada y enumera sus números de fila, porque un registro sin nodos no permite generar la lista de nodos que pide la cláusula. Solo comprueba que `节点` esté relleno; no juzga si el grano del nodo es adecuado, porque la cláusula 4.2 no da criterio, ni decide si algún nodo quedó sin analizar. |
| Nuestro estudio escribió «相逆» en la columna `引导词`. ¿Se señalará? | `HZ-003` lo informa como palabra guía fuera de la lista: la norma dice «相反», no «相逆», y las tablas 1 y 2 aportan 无/多/少/伴随/部分/相反/异常 y 早/晚/先/后. Es un aviso y no un veredicto, porque una palabra guía definida y archivada por el estudio antes del análisis está permitida — por eso la regla se queda en `warn`. Una implantación puede declarar su propia lista y entonces solo se informa de lo que quede fuera de ella. |
| La columna `偏差` dice «无流量», pero `工艺参数` es «温度» y `引导词` es «无». ¿Se detecta? | `HZ-007` informa de la fila cuando el `偏差` escrito no contiene el `工艺参数` leído a través de su `引导词` en ninguno de los dos órdenes; los espacios y los separadores habituales (por ejemplo `+`, `、`, `/`, `-`, `—`, `的`, `：`) no cuentan, así que 流量无, 流量 + 无 y 无流量 coinciden. Solo se ejecuta si están las tres columnas —si no, figura en `skipped`— y un hallazgo suele indicar un copiado y pegado, no que la desviación sea técnicamente inválida. |
| La columna `风险等级` está rellena con «中», pero no hemos configurado ningún nivel de riesgo. ¿Qué devuelve? | `HZ-005` se informa a sí misma en `skipped`, no como un aprobado: la norma no fija escala de niveles de riesgo, así que los niveles deben venir de los criterios de riesgo de su organización y la lista de origen está vacía. Una vez configurados, solo comprueba que el valor figure en la lista, no si la calificación es correcta, y su severidad está topada en `info`. |
| La hoja no tiene ninguna línea que nombre la unidad analizada. ¿Es una falta? | `HZ-006` lo informa una vez, en el nivel superior: sin objeto de análisis, las conclusiones no se pueden remontar al límite que se analizó. La lista de cabecera en que se apoya procede de un anexo informativo —una sugerencia, no una obligación—, por eso la regla se queda en `warn` y `requireHeader: false` la desactiva para hojas que legítimamente no la llevan. |

## Normas que sigue

| Documento | Número | Reglas que lo citan |
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

| Superficie | Estado |
|---|---|
| Harness | Rango de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificado para aceptar tanto `0.2.0-rc.2` como `0.2.1-alpha.1`. **No se declara `engines.dsh`**: no tiene lector y no puede rechazar ningún host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sin código nativo, sin red, sin llamada al modelo) |
| Modo de herramienta | Funciona en `native`, `ptc` y `both`; para un directorio completo use `ptc` |

## What it does

La tabla de reglas, los campos y el comportamiento detallado están en [README.md](README.md#what-it-does) (versión principal en inglés). El plugin sólo enumera divergencias literales frente a las cláusulas citadas e indica en `skipped` cada comprobación que no pudo ejecutarse.

## Install

```sh
dsh plugin --profile <name> add dsh-hazplan-check
dsh --profile <name> --dump-config | grep 'dsh-hazplan-check'
```

## Configuration

Todos los parámetros ajustables viven en el esquema Schemastery de `src/config.ts`, por lo que se cambian desde `cordis.yml` sin tocar el código; los umbrales por regla están en el paquete de reglas bajo `rules/`.

| Clave | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `rulesFile` | string | `rules/hazplan-check.yaml` | Ruta del paquete de reglas, relativa a la raíz del paquete |
| `disabledRules` | string[] | `[]` | Ids de reglas que se dejan de ejecutar; cada una aparece en `skipped` |
| `onlyRules` | string[] | `[]` | Ejecutar solo estas reglas; vacío ejecuta todas |
| `skipNotes` | string | `""` | Nota añadida a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Presupuesto de tiempo de espera cooperativo de la herramienta |

## Material format

Acepta JSON o YAML. El ejemplo completo de campos está en [README.md](README.md#material-format) (versión principal en inglés). Los campos son opcionales en la capa de lectura y los valida el motor, de modo que una exportación parcial produce hallazgos sobre lo que falta en lugar de un fallo.

## Rule sources

Los datos de las reglas están separados del código: cada regla lleva documento, número, cláusula en la numeración propia de la fuente, extracto literal y URL de origen. El cargador impone que el extracto sea una cita real de al menos ocho caracteres y que una comprobación basada sólo en un principio general (`kind: derived-from-principle`, tope `warn`) o en una política local (`kind: institutional-configuration`, tope `info`) nunca se declare `error`.

Los límites verificados y las conclusiones deliberadamente **no** afirmadas están en [README.md](README.md#rule-sources) (versión principal en inglés) y en `rules/evidence/`.

## Troubleshooting

- **El plugin se instala pero la herramienta no aparece**: compruebe que `main` resuelve a `lib/index.mjs` y que `pnpm run build` lo generó.
- **`dsh plugin add` rechaza el paquete**: la faixa de peers cubre `0.1.x` y `0.2.x`; fuera de ella, conceda una exención explícita con `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Una regla no se ejecutó**: lea el arreglo `skipped`.
- **`check` informa `manifest-peers` como fallo**: es un problema conocido de `dsh-plugin-dev`; el runtime aplica la compatibilidad al instalar.
- **Los horarios parecen desplazados**: toda la aritmética es de hora local sobre las cadenas entregadas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-hazplan-check
```

El último comando copia el kit compartido de `../_shared` a `src/shared/`; vuelva a ejecutarlo tras cada cambio compartido.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-hazplan-check contributors.
