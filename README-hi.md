# dsh-hazplan-check — HAZOP वर्कशीट के तत्वों की पूर्णता और विचलन व्युत्पत्ति की संगति की जाँच

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-hazplan-check` एक HAZOP वर्कशीट पढ़ता है — शीट के अपने कॉलम नामों पर आधारित पंक्तियाँ (चीनी या अंग्रेज़ी नाम, दोनों चलते हैं), साथ में विश्लेषण-वस्तु बताने वाला वैकल्पिक हेडर — और उसी शीट की पूर्णता तथा आंतरिक अनुरेखणीयता की जाँच करता है: क्या हर पंक्ति अपने टेम्पलेट में माँगे गए कॉलम भरती है (डिफ़ॉल्ट रूप से `偏差` और `原因`), क्या हर पंक्ति में `节点` दर्ज है, क्या `引导词` मानक की तालिका 1 और तालिका 2 से या अध्ययन द्वारा पहले घोषित सूची से लिए गए हैं, क्या हर पंक्ति से दिखता है कि विचलन किस तत्व से आया, क्या `风险等级` आपके संस्थान की जोखिम-शब्दावली से है, क्या शीट विश्लेषण-वस्तु को पहचानती है, और क्या हर `偏差` शब्दशः अपने `引导词` के माध्यम से पढ़ा गया `工艺参数` है; किसी कॉलम के अभाव में जो जाँच चल नहीं सकती, वह चुपचाप पास होने के बजाय `skipped` में दर्ज होती है।

## आउटपुट कैसा दिखता है

![Terminal demo of dsh-hazplan-check: real output over its HZ-004 fixture](https://raw.githubusercontent.com/PerryLink/dsh-hazplan-check/main/docs/assets/dsh-hazplan-check-demo.png)

इस प्लगइन का अपने ही `HZ-004` टेस्ट फ़िक्स्चर पर वास्तविक आउटपुट — कोई नकली चित्र नहीं। नियम-पैक उद्धरण नहीं गढ़ता, इसलिए हर निष्कर्ष लागू किए गए खंड का नाम और यह भी बताता है कि उसका मूल पाठ इस बार प्राप्त नहीं हुआ।

## यह किन सवालों का जवाब देता है

| आपका सवाल | इसका जवाब |
|---|---|
| एक पंक्ति में विचलन दर्ज है पर कारण खाली है। क्या यह दर्ज होता है? | हाँ। `HZ-001` हर पंक्ति में अनिवार्य कॉलम भरे होने की अपेक्षा करता है; बिना कॉन्फ़िगर किए यह उसी जोड़ी पर लौट आता है जिसे धारा स्वयं नाम देती है — `偏差` और `原因` — इसलिए खाली `原因` अपने आप में एक कमी है। यह केवल देखता है कि कॉलम भरा है, यह नहीं कि समस्याओं की सूची पूरी है या कारण तकनीकी रूप से सही है। |
| तीन पंक्तियों में नोड ही नहीं है। क्या कुछ बताया जाता है, और नोड का बँटवारा कैसा है यह भी आँका जाता है? | `HZ-002` उन पंक्तियों को एक ही प्रविष्टि में दर्ज करता है और पंक्ति-संख्या गिनाता है, क्योंकि नोड रहित रिकॉर्ड से धारा में माँगी गई नोड-सूची बन ही नहीं सकती। यह केवल देखता है कि `节点` भरा है; नोड की बारीकी उचित है या नहीं, यह नहीं आँकता क्योंकि धारा 4.2 कोई कसौटी नहीं देती, और यह भी तय नहीं करता कि कोई नोड विश्लेषण से छूट गया है। |
| हमारे अध्ययन ने `引导词` कॉलम में «相逆» लिखा है। क्या यह दर्ज होगा? | `HZ-003` इसे सूची से बाहर का गाइड-शब्द बताकर दर्ज करता है: मानक का अपना शब्द «相反» है, «相逆» नहीं, और तालिका 1 व 2 ये देती हैं — 无/多/少/伴随/部分/相反/异常 और 早/晚/先/后। यह एक सूचना है, निर्णय नहीं, क्योंकि विश्लेषण से पहले परिभाषित और संग्रहित अपना गाइड-शब्द मान्य होता है — इसीलिए नियम `warn` पर रहता है। तैनाती अपनी सूची घोषित कर सकती है, और तब केवल उससे बाहर के शब्द दर्ज होते हैं। |
| `偏差` कॉलम में «无流量» लिखा है, पर `工艺参数` «温度» है और `引导词` «无»। क्या यह पकड़ में आता है? | `HZ-007` उस पंक्ति को दर्ज करता है जब लिखा हुआ `偏差` अपने `引导词` के माध्यम से पढ़े गए `工艺参数` को किसी भी क्रम में नहीं रखता; खाली स्थान और सामान्य संयोजक (जैसे `+`, `、`, `/`, `-`, `—`, `的`, `：`) नहीं गिने जाते, इसलिए 流量无, 流量 + 无 और 无流量 तीनों मेल खाते हैं। यह केवल तब चलता है जब तीनों कॉलम मौजूद हों — वरना यह `skipped` में दिखता है — और मेल मिलना आम तौर पर कॉपी-पेस्ट की गड़बड़ बताता है, यह नहीं कि विचलन तकनीकी रूप से गलत है। |
| `风险等级` कॉलम में «中» भरा है, पर हमने कोई जोखिम-स्तर कॉन्फ़िगर नहीं किया। जवाब में क्या आएगा? | `HZ-005` स्वयं को `skipped` में दर्ज करता है, पास के रूप में नहीं: मानक जोखिम-स्तर का कोई पैमाना तय नहीं करता, इसलिए स्तर आपके संस्थान के जोखिम-मानदंड से आने चाहिए और छोड़ी गई सूची खाली है। कॉन्फ़िगर करने के बाद यह केवल देखता है कि मान सूची में है, यह नहीं कि वर्गीकरण सही है, और इसकी गंभीरता `info` तक सीमित है। |
| शीट में कहीं भी विश्लेषण-वस्तु (इकाई) का नाम नहीं है। क्या यह कमी है? | `HZ-006` इसे एक बार, शीर्ष स्तर पर दर्ज करता है: विश्लेषण-वस्तु के बिना निष्कर्ष उस सीमा तक वापस नहीं जोड़े जा सकते जिसका विश्लेषण हुआ। जिस हेडर-सूची पर यह टिका है वह सूचनात्मक परिशिष्ट से आती है — सुझाव, बाध्यता नहीं — इसीलिए नियम `warn` पर रहता है, और जिन शीटों में वह वस्तुतः नहीं होती उनके लिए `requireHeader: false` इसे बंद कर देता है। |

## यह किन मानकों पर आधारित है

| दस्तावेज़ | संख्यांक | इन्हें उद्धृत करने वाले नियम |
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

| सतह | स्थिति |
|---|---|
| Harness | peer रेंज `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — `0.2.0-rc.2` और `0.2.1-alpha.1` दोनों को स्वीकार करने के लिए सत्यापित। **`engines.dsh` जानबूझकर घोषित नहीं**: इसका कोई पाठक नहीं और यह किसी होस्ट को अस्वीकार नहीं कर सकता |
| Node | `^22.19.0 || >=24.0.0` |
| प्लेटफ़ॉर्म | सभी (शुद्ध ESM; कोई नेटिव कोड नहीं, कोई नेटवर्क नहीं, कोई मॉडल कॉल नहीं) |
| टूल मोड | `native`, `ptc` और `both` में काम करता है; पूरे फ़ोल्डर के लिए `ptc` चुनें |

## What it does

नियम-सूची, फ़ील्ड और विस्तृत व्यवहार [README.md](README.md#what-it-does) (अंग्रेज़ी मुख्य संस्करण) में हैं। यह प्लगइन केवल उद्धृत धाराओं के सामने शाब्दिक अंतर सूचीबद्ध करता है और हर न चल पाई जाँच को `skipped` में बताता है।

## Install

```sh
dsh plugin --profile <name> add dsh-hazplan-check
dsh --profile <name> --dump-config | grep 'dsh-hazplan-check'
```

## Configuration

सभी समायोज्य पैरामीटर `src/config.ts` की Schemastery स्कीमा में हैं, इसलिए कोड बदले बिना `cordis.yml` से बदले जा सकते हैं; प्रति-नियम सीमाएँ `rules/` के नियम-पैक में हैं।

| कुंजी | प्रकार | डिफ़ॉल्ट | विवरण |
|---|---|---|---|
| `rulesFile` | string | `rules/hazplan-check.yaml` | नियम-पैक का पथ, पैकेज रूट के सापेक्ष |
| `disabledRules` | string[] | `[]` | बंद करने वाले नियम id; प्रत्येक `skipped` में दिखता है |
| `onlyRules` | string[] | `[]` | केवल ये नियम चलाएँ; खाली होने पर सभी नियम चलते हैं |
| `skipNotes` | string | `""` | हर `skipped` कारण के आगे जोड़ी जाने वाली टिप्पणी |
| `timeoutMs` | number | `120000` | उपकरण का सहकारी समय-सीमा बजट |

## Material format

JSON या YAML स्वीकार्य है। पूरा फ़ील्ड उदाहरण [README.md](README.md#material-format) (अंग्रेज़ी मुख्य संस्करण) में है। पढ़ने की परत में फ़ील्ड वैकल्पिक हैं और जाँच इंजन उन्हें सत्यापित करता है, इसलिए आंशिक निर्यात पर क्रैश के बजाय "अनुपस्थित" श्रेणी के निष्कर्ष मिलते हैं।

## Rule sources

नियम-डेटा कोड से अलग है: प्रत्येक नियम में दस्तावेज़, संख्या, स्रोत की अपनी क्रमांकन-प्रणाली के अनुसार धारा, शब्दशः उद्धरण और स्रोत URL होता है। लोडर लागू करता है कि उद्धरण कम से कम आठ अक्षरों का वास्तविक उद्धरण हो, और जिस जाँच का आधार केवल सामान्य सिद्धांत (`kind: derived-from-principle`, अधिकतम `warn`) या स्थानीय नीति (`kind: institutional-configuration`, अधिकतम `info`) हो, उसे कभी `error` घोषित न किया जाए।

सत्यापित सीमाएँ और जान-बूझकर **न** कहे गए निष्कर्ष [README.md](README.md#rule-sources) (अंग्रेज़ी मुख्य संस्करण) और `rules/evidence/` में हैं।

## Troubleshooting

- **प्लगइन इंस्टॉल हो गया पर टूल दिखता नहीं**: जाँचें कि `main` `lib/index.mjs` पर जाता है और `pnpm run build` ने उसे बनाया है।
- **`dsh plugin add` असंगत बताकर मना करता है**: peer range `0.1.x` और `0.2.x` दोनों को कवर करती है; बाहर होने पर स्पष्ट छूट दें: `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`।
- **कोई नियम नहीं चला**: `skipped` सरणी देखें।
- **`check` में `manifest-peers` विफल दिखता है**: यह `dsh-plugin-dev` की ज्ञात अपस्ट्रीम समस्या है; रनटाइम इंस्टॉल के समय अनुकूलता लागू करता है।
- **समय खिसका हुआ लगता है**: सारी गणना दिए गए स्ट्रिंग पर वॉल-क्लॉक है।

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-hazplan-check
```

अंतिम कमांड `../_shared` का साझा किट `src/shared/` में कॉपी करता है; हर साझा बदलाव के बाद इसे दोबारा चलाएँ।

## License

[Apache License 2.0](LICENSE) © 2026 dsh-hazplan-check contributors.
