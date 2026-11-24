# F9.8 — isolamento da perda interna das cordas

Base 64aea407ceec444035883e36ea33bcae0a1dae30. Feedback do titular: melhora pequena do sustain F9.6. F9.7 não produziu ganho material global por afinação. Controle: 0,5 rad, boardFactor 0,5, ±0,5 cent, 1 m/s. Testar apenas o termo de amortecimento distribuído constante sigma0 em s^-1, mantendo sigma2 (m²/s), rigidez, massa, tensão, ponte, tampo, martelo e radiação. Casos controle [vertical .4, horizontal .2]; horizontal-half [.4,.1]; both-half [.2,.1]. Redução escolhida como ensaio de sensibilidade não medição Yamaha; nenhum controle de ganho por parcial. O amortecimento por modo depende de sigma0+sigma2*k², assim reduzir sigma0 afeta proporcionalmente mais os modos baixos. Coeficientes constantes na nota, não negativos. A anisotropia efetiva é hipótese de perdas do sistema, não propriedade comprovada do aço. Não simular duração audível impondo envelope.

Comparação em 20 s, mesma escala PCM, 96 kHz mecânico/48 kHz PCM, continuidade, 10 parciais, contrastes e energia. Priorizar P1 e cauda 8–14 s, sem piorar P2 que já decai mais lentamente que C5, nem comprometer ataque e timbre. Nenhum candidato automaticamente promovido. Gate de passividade, clipping, checkpoint e regressão. Workflow dedicado acionado na branch de pesquisa; resultados pendentes no momento da gravação. Renderizadores históricos congelados; duplicação de laboratório é dívida técnica. Sem alteração em main, versões públicas, MIDI, efeitos, integração, pedal ou polifonia. A F9 não homologada; não ampliar para 88 teclas.

## Validação curta e controle confirmados

CI [45413792006](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45413792006): 51/51 testes Node (9+8+9+13+12). Controle reproduz F9.7 no ensaio de 25 ms, paridade de pressão e energia; candidatos passivos, checkpoint contínuo, rejeição de configuração divergente. Pico de pressão controle 0.71761638 Pa, horizontal-half 0.71760050 Pa, both-half 0.71832667 Pa. Isso não prova paridade perceptiva. Controle de 20 s concluído, [artefato](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45413792006/artifacts/14931251101), queda global -40 dB 7,5 s / -60 dB 15,5 s, fundamental -40 dB 8,5 s / -60 dB 16,5 s, consistentes com F9.7. Estado dos outros jobs na consulta: smoke: success; render (horizontal-half): in_progress; render (both-half): in_progress; render (control): success. Resultados dos candidatos não inferidos.

### Limite analítico de corda isolada

Para modo subamortecido sem ponte móvel, envelope de amplitude exp(-sigma*t), sigma=sigma0+sigma2*(n*pi/L)^2. L=0,65 m. Queda de amplitude de 60 dB ideal = ln(1000)/sigma. Fundamental vertical/horizontal (s): control 17.07/34.06; horizontal-half 17.07/67.19; both-half 33.75/67.19. Não é T60 acústico, não é previsão do sustain do piano acoplado nem prova de duração audível. Explica por que testar sigma0 separadamente. Mantém hipótese de corda efetiva com perdas de apoio não medidas. Auditoria de precisão pré-PCM adicionada em e10d9347e878e180e708966de293a68bf033c436; 8/8 verificações V8 sintéticas, ainda sem Node ou medição de render real. F9 aberta, main intacta.

## Resultados finais F9.8

[CI 45413792006](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45413792006): quatro jobs concluídos com sucesso. 51/51 testes Node; 60 blocos de 1 s, sem clipping ou recontato, máximo resíduo 1.87897e-14 J. Análise PCM até 19,5 s exclui fade. Ganho comum.

| Caso | Global -40 | Global -60 | P1 -40 | P2 -40 | P3 -40 | PCM aos 19 s vs controle |
|---|---|---|---|---|---|---|
| control | 7.5 s | 15.5 s | 8.5 s | 9.5 s | 6.5 s | 0.000 dB |
| horizontal-half | 9.5 s | não observada até 19.5 s | 11 s | 10 s | 7.5 s | 11.426 dB |
| both-half | 13 s | não observada até 19.5 s | 15.5 s | 13 s | 9.5 s | 21.410 dB |

C5 médio v8: global -40 14 s, P1 11,5 s, P2 5 s, P3 9 s. A se aproxima de P1, porém P2 piora 0,5 s; B se aproxima do global e P3, mas P1 e P2 tornam-se excessivamente longos frente ao C5. Não aprovar automaticamente. Ganho PCM comum aos 19–19,5 s A 11.426 dB, B 21.410 dB; curvas normalizadas dão +11,399 e +21,243 dB, respectivamente, não SPL absoluto. Contraste lateral não equivale a SNR de gravação. Ataque 25 ms e passividade aprovados, escuta pendente.

Artefatos: [control](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45413792006/artifacts/14931251101), [horizontal-half](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45413792006/artifacts/14932025780), [both-half](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45413792006/artifacts/14932365714). Retenção finita.

Decisão: manter A e B como alternativas de pesquisa, não substituir controle F9.6. F9.9 comparar 40 s de controle, A, B em toque médio com análise float e PCM no mesmo ganho. Não inferir duração audível ou calibrar pp/ff. F9 aberta, V10, pedal, ressonância simpática, 32–64 vozes e integração pendentes.

## Retorno auditivo do titular — 24/11/2026

Sobre o artefato F98-both-half-20s (CI 45413792006, artefato 14932365714): "F98-both-half-20s nesse exemplo o sustain melhorou". Melhora de sustain percebida pelo titular, não uma aprovação de timbre, preferência comparativa frente a A ou homologação final. Priorizar B como candidato de pesquisa sem substituir os controles. Manter coeficientes constantes vertical 0,2 e horizontal 0,1 s^-1, com demais parâmetros F9.8 intactos; não reduzir perdas novamente sem evidência. Avaliação F9.9 de 40 s e dinâmica pendentes. Discrepância P2 permanece em aberto. Nenhuma alteração em main.
