# F9.4 — sensibilidade das perdas após avaliação de sustain

Feedback do titular: "acho que falta sustain para a nota". F9.2 preservada integralmente. Sem mudança no DSP público, parâmetros da referência, main ou áudio. F10 ainda bloqueada. Hipóteses de perdas internas não são medidas em piano Yamaha. Teste isolado da mecânica completa F9.2, 96 kHz, 0,3 s, toque médio; resistência radiativa ativa sem mudança, sem renderizar pressão acústica. Dois ensaios variam um grupo de perdas por vez em 50%, valor escolhido para sensibilidade e não calibração. Norma RMS das velocidades modais do tampo (coordenadas normalizadas em massa) NÃO é pressão ou SPL.

| cenário | perda cordas mJ | perda estrutural tampo mJ | perda radiativa mJ | norma RMS do tampo 0,2–0,3 s | diferença relativa dB |
|---|---:|---:|---:|---:|---:|
| F9.2 | 0.259150 | 0.663354 | 0.219450 | 0.01486004 | 0.000 |
| cordas ×0,5 | 0.135395 | 0.681280 | 0.226161 | 0.01529826 | 0.252 |
| tampo ×0,5 | 0.275222 | 0.396673 | 0.256312 | 0.01759912 | 1.469 |

O tampo tem a maior dissipação acumulada no baseline deste intervalo; isso não demonstra a causa dominante do decaimento acústico tardio. Reduzir perdas do tampo também muda sua resposta mecânica e o ataque, logo não promover automaticamente o candidato. Todos os três ensaios V8 passaram os invariantes do renderizador: resíduo global < 1e-9 J, aumento energético observado zero, separação e ausência de recontato. Não executado Node/CI, não há novo WAV ou teste auditivo, nem certificação 32–64 vozes. Relatório numérico em audio/analysis_f9_4_sensitivity.json (seleção das métricas observadas). Reprodução: node research/stage-concert-grand/f9-sustain-sensitivity-demo.mjs.

Próxima ação: comparar pressão e parciais de 5 s em ganho fixo para baseline e candidato, ataque 0–100 ms e cauda 1–5 s; medir com referências C5 em janelas equivalentes; manter a F9 aberta até avaliação auditiva. Não adicionar reverb, compressor, ganho de cauda ou loop. Sem alterar qualquer versão pública.
