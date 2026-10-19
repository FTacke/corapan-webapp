# CO.PRE.PAN Tense Reference Schema

Source: `C:\dev\coprepan\json_annotated`

Files scanned: 926
Tokens scanned: 17527723
Tense-bearing tokens: 620150

## Allowed Values

### PastType
- `simplePast`: 420702
- `imperfectPast`: 100601
- `presentPerfect`: 66938
- `pastPerfect`: 12028
- `perfectInfinitive`: 4104
- `otherCompoundPast`: 3755
- `futurePerfect`: 164

### FutureType
- `periphrasticFuture`: 6918
- `periphrasticFuturePast`: 836

### VoiceType
- `passive`: 46535
- `resultative_or_state`: 6324

### TenseRole
- `finite_verb`: 414395
- `copula_or_aux`: 59004
- `lexical_participle`: 28907
- `aux_passive`: 20790
- `aux_pass_chain`: 4574
- `aux_nonfinite_perfect`: 4104
- `nonfinite_perfect`: 4104
- `copula_resultative`: 3162

## Typical Combinations

- 58684: `PastType=presentPerfect`, `Tense=Past`, `VerbForm=Part`
  Example: `identificado` / `identificar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 20400: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=copula_or_aux`, `VerbForm=Fin`, `VerbLemma=ser`
  Example: `fue` / `ser` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 19402: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=aux_passive`, `VerbForm=Fin`, `VerbLemma=ser`, `VoiceType=passive`
  Example: `fueron` / `ser` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 19299: `PastType=simplePast`, `Tense=Past`, `TenseRole=lexical_participle`, `VerbForm=Part`, `VoiceType=passive`
  Example: `internadas` / `internar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 11775: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=decir`
  Example: `dijeron` / `decir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 11548: `Mood=Ind`, `PastType=imperfectPast`, `Tense=Imp`, `TenseRole=copula_or_aux`, `VerbForm=Fin`, `VerbLemma=haber`
  Example: `había` / `haber` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 9806: `PastType=pastPerfect`, `Tense=Past`, `VerbForm=Part`
  Example: `detenido` / `detener` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 9589: `Mood=Ind`, `PastType=imperfectPast`, `Tense=Imp`, `TenseRole=copula_or_aux`, `VerbForm=Fin`, `VerbLemma=ser`
  Example: `era` / `ser` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 7047: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=señalar`
  Example: `señaló` / `señalar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 6918: `FutureType=periphrasticFuture`, `VerbForm=Inf`
  Example: `ver` / `ver` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 6302: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=afirmar`
  Example: `afirmó` / `afirmar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 6135: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=hacer`
  Example: `hizo` / `hacer` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 5565: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=tener`
  Example: `tuvieron` / `tener` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 5237: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=informar`
  Example: `informó` / `informar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 5213: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=explicar`
  Example: `explicó` / `explicar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 5169: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=indicar`
  Example: `indicaron` / `indicar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 4822: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=asegurar`
  Example: `aseguró` / `asegurar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 4765: `Mood=Ind`, `PastType=imperfectPast`, `Tense=Imp`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=tener`
  Example: `teníamos` / `tener` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 4718: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=llegar`
  Example: `llegó` / `llegar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 4430: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=dar`
  Example: `dio` / `dar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 4104: `TenseRole=aux_nonfinite_perfect`, `VerbForm=Inf`
  Example: `haber` / `haber` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 4063: `PastType=perfectInfinitive`, `Tense=Past`, `TenseRole=nonfinite_perfect`, `TenseSubtype=perfectInfinitive`, `VerbForm=Part`
  Example: `oído` / `oer` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 3790: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=expresar`
  Example: `expresó` / `expresar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 3602: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=dejar`
  Example: `dejó` / `dejar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 3435: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=anunciar`
  Example: `anunció` / `anunciar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 3277: `PastType=presentPerfect`, `Tense=Past`, `TenseRole=aux_pass_chain`, `VerbForm=Part`
  Example: `sido` / `ser` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 3275: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=destacar`
  Example: `destacó` / `destacar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 3272: `Mood=Ind`, `PastType=imperfectPast`, `Tense=Imp`, `TenseRole=copula_or_aux`, `VerbForm=Fin`, `VerbLemma=estar`
  Example: `estaban` / `estar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 3248: `PastType=presentPerfect`, `Tense=Past`, `TenseRole=lexical_participle`, `VerbForm=Part`, `VoiceType=passive`
  Example: `asociados` / `asociar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 3051: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=quedar`
  Example: `quedó` / `quedar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2984: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=sostener`
  Example: `sostuvo` / `sostener` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2902: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=lograr`
  Example: `logró` / `lograr` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2870: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=recibir`
  Example: `Recibí` / `recibir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 2864: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=confirmar`
  Example: `confirmó` / `confirmar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 2784: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=comenzar`
  Example: `comenzó` / `comenzar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2772: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=agregar`
  Example: `agregó` / `agregar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2663: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=añadir`
  Example: `añadió` / `añadir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2534: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=declarar`
  Example: `declaré` / `declarar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2475: `PastType=otherCompoundPast`, `Tense=Past`, `VerbForm=Part`
  Example: `imaginado` / `imaginar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2422: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=llevar`
  Example: `llevó` / `llevar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2384: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=advertir`
  Example: `advirtió` / `advertir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2368: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=realizar`
  Example: `realizó` / `realizar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2307: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=presentar`
  Example: `presentaron` / `presentar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2167: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=pasar`
  Example: `pasó` / `pasar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2069: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=terminar`
  Example: `terminó` / `terminar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2069: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=copula_or_aux`, `VerbForm=Fin`, `VerbLemma=haber`
  Example: `hubo` / `haber` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2063: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=volver`
  Example: `volvió` / `volver` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2062: `PastType=imperfectPast`, `TenseRole=lexical_participle`, `VerbForm=Part`, `VoiceType=resultative_or_state`
  Example: `preocupada` / `preocupado` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 2025: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=ver`
  Example: `vio` / `ver` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 2021: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=pedir`
  Example: `pidió` / `pedir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 1978: `Mood=Ind`, `PastType=imperfectPast`, `Tense=Imp`, `TenseRole=copula_resultative`, `VerbForm=Fin`, `VerbLemma=estar`, `VoiceType=resultative_or_state`
  Example: `Estaba` / `estar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 1971: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=ocurrir`
  Example: `ocurrió` / `ocurrir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1897: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=recordar`
  Example: `recordó` / `recordar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1822: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=registrar`
  Example: `registró` / `registrar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1746: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=convertir`
  Example: `convirtió` / `convertir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1702: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=manifestar`
  Example: `manifestaron` / `manifestar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1685: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=subrayar`
  Example: `subrayó` / `subrayar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1680: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=escribir`
  Example: `escribió` / `escribir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 1650: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=detallar`
  Example: `detalló` / `detallar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1644: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=salir`
  Example: `salió` / `salir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 1640: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=permitir`
  Example: `permitió` / `permitir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1623: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=poner`
  Example: `puso` / `poner` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1614: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=ganar`
  Example: `ganó` / `ganar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1611: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=contar`
  Example: `contó` / `contar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 1607: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=mostrar`
  Example: `mostró` / `mostrar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1591: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=decidir`
  Example: `decidió` / `decidir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1562: `Mood=Ind`, `PastType=imperfectPast`, `Tense=Imp`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=encontrar`
  Example: `encontraba` / `encontrar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1543: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=iniciar`
  Example: `inició` / `iniciar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1475: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=generar`
  Example: `generaron` / `generar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1459: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=perder`
  Example: `perdió` / `perder` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1434: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=denunciar`
  Example: `denunciaron` / `denunciar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1413: `Mood=Ind`, `PastType=imperfectPast`, `Tense=Imp`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=estar`
  Example: `estaba` / `estar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 1408: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=encontrar`
  Example: `encontró` / `encontrar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1407: `Mood=Sub`, `PastType=imperfectPast`, `Tense=Imp`, `TenseRole=copula_or_aux`, `VerbForm=Fin`, `VerbLemma=ser`
  Example: `fuese` / `ser` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`
- 1396: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=morir`
  Example: `murió` / `morir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1391: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=responder`
  Example: `respondió` / `responder` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1375: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=calificar`
  Example: `calificaron` / `calificar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1368: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=participar`
  Example: `participó` / `participar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1325: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=concluir`
  Example: `concluyó` / `concluir` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-14.ann.json`
- 1316: `Mood=Ind`, `PastType=simplePast`, `Tense=Past`, `TenseRole=finite_verb`, `VerbForm=Fin`, `VerbLemma=empezar`
  Example: `empezó` / `empezar` in `json_annotated/ARG/clarin/ARG_clarin_2025-12-13.ann.json`

## Code Reference

Rules were checked against `C:/dev/coprepan/scripts/annotation/lib/tense_rules.py`.
