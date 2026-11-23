# Stage Synth — E1.4: escuta não diferencia D v1.12.6 e D v1.12.7

**Data:** 23/11/2026. **Feedback explícito do proprietário:** “não existem diferenças perceptíveis entre os dois modelos”, após receber WAVs reais Stage D v1.12.6/v1.12.7, incluindo a comparação intercalada. **Conclusão de produto: hipótese de melhoria do martelo grave da v1.12.7 REPROVADA na escuta do titular.** Não chamar v1.12.7 de avanço de realismo, mesmo que os arrays PCM difiram.

## Por que os números anteriores não contradizem a escuta

No diagnóstico E1.3, comparando os dois motores no mesmo ganho, o C2 mf mudou **−4,38 dB nos 12 ms iniciais**, mas **0,00 dB entre 100–220 ms** e **+0,03 dB em 900–1180 ms**. Os demais graves mostram o mesmo padrão aproximado de quase nenhuma transformação do corpo ou da cauda. A análise prévia das 15 referências Iowa demonstrou efeito **misto**: erro de envelope inicial C2/C3 3,58→2,96 dB (melhora) mas discrepância de espectro do ataque 3,23→4,30 dB e do trecho tardio 9,38→10,49 dB (**pioras**). **Diferença numérica não implica diferença auditivamente relevante, muito menos fidelidade ao piano.**

## Lacuna arquitetural confirmada no código, não causalidade perceptiva comprovada

O motor D em `physical-piano-hybrid.js` ainda tem a cadeia:

1. Múltiplos ressonadores de corda somados diretamente em `tmp`, `L` e `R` (com envelope de ataque e pequena componente mecânica).
2. `this.body.step(dryL*.65,dryR*.65)` excita `PianoResonanceBody`.
3. Saída `x=(dryL+this.body.wetL*.48)*this.mixGain`, equivalente para direita: **sinal modal seco direto + contribuição ressonante separada**.
4. O corpo calcula `this.reaction` em `piano-resonance.js`, porém o código de render do motor D **não o utiliza para alterar a evolução dos ressonadores primários**. Assim, o D não tem ligação mecânica bidirecional nota↔ponte/tampo no mesmo callback. Sua saída de corpo é *wet* adicionado, não resposta radiada espacialmente calibrada.

Esta é uma deficiência estrutural concreta. **Não comprova, isoladamente, que seja a causa subjetiva do caráter “violão”**. Além disso, os parâmetros de corpo/ponte/tampo não são provenientes de medições conjuntas; o laboratório passivo compartilhado (`research/shared-passive-piano-bridge.mjs`) ainda só fornece coordenadas mecânicas generalizadas, não pressão do ar. Seu desempenho Node não homologa o AudioWorklet.

## Decisão e critério de nova versão

- **Reprovar** a intervenção de martelo grave de v1.12.7 **como ganho de timbre**; não promover a versão a estável, não anunciar resultado e não gastar mais ciclos com pequenas variantes de ataque.
- **Preservar o estado e o código publicado**, incluindo D v1.12.7 para reprodutibilidade, histórico D v1.12.6, A/B/C/Clássico, MIDI/CC64, FX, UI, presets e C4–C6; não apagar ou reverter sem uma substituição aprovada.
- **Não integrar PR #26** (“madeira” aditiva e longitudinal), já reprovada por escuta.
- **Priorizar experimento realmente estrutural:** acoplamento bidirecional passivo das cordas à ponte/tampo compartilhados, sua emissão acústica espacial/temporariamente plausível e evolução de parciais/dupla cauda. Primeiro identificar os parâmetros e os limites com dados permitidos comercialmente; não copiar sons ou código de terceiros nem converter `boardVelocity` fictícia em Pa.
- Antes de pedir outra escuta, comparar, em C2/C3 e acordes graves, **atacque 0–12 ms, corpo 100–220 ms, sustain, cauda, trajetórias de parciais e resposta a pedal**, com referência acústica confiável (prioridade Iowa C2/C3 mf, ver E1.2) e segregar fontes de ajuste versus validação. Exigir **melhora em métricas relevantes ao som de piano**, não só diferença entre modelos. Filtros de diferença numérica são *triagem*, não garantia de perceptibilidade ou limiar de ABX.
- **Somente então** entregar um WAV curto, nivelado, para escuta comparativa com a versão de referência e decisão explícita do titular. **Nenhuma quantidade de testes unitários substitui a escuta**.
- Meta de **32 vozes mínimas e 64 desejadas** requer desempenho no PC/Android real. **0/7 R-GATEs completos**; nenhum novo timbre integrado nesta decisão.

## Fontes internas

- [Medição E1.3 dos dois WAVs genuínos do Stage](DIAGNOSTICO_D_GRAVES_AB_INTERCALADO_2026-11-23.md).
- [V1.12.7 — evidência mista versus Iowa](EXPERIMENTO_D_MARTELO_V127_2026-11-23.md).
- [Solver mecânico passivo compartilhado](PRONTIDAO_PONTE_TAMPO_PASSIVO_V128_2026-11-23.md).
- [Preparação H1 ponte→pressão sem dados medidos](VERIFICACAO_TRANSFERENCIA_RADIATIVA_H1_E11_2026-11-23.md).
