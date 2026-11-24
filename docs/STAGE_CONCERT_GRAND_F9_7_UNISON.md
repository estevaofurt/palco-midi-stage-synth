# F9.7 — sensibilidade de afinação do tricórdio

Base 92344c752067f663b219b47ad54bad1fd11fadc3. F9.6 (0,5 rad) preservada como candidato, não homologada. Em 15 s, ganho PCM fixo +5,899 dB aos 10–10,5 s frente a F9.5, fundamental -40 dB de 6 para 8,5 s; C5 v8 11,5 s. Segundo parcial 9,5 s vs C5 5 s, terceiro 6,5 s vs C5 9 s. Não confundir aumento relativo com melhoria universal.

Variar exclusivamente dispersão simétrica (-d,0,+d) em cents das frequências livres de projeto das três cordas, mantendo centro C4, geometria/material do fio, cálculo de tensão a partir de f1, ponte 0,5 rad, boardFactor 0,5, impacto 1 m/s, 96 kHz e ganho original. d=0,25, 0,5 (controle F9.6), 1,0. São hipóteses experimentais, não medições Yamaha ou recomendações de afinação. Modos acoplados não têm necessariamente a mesma separação de frequência que cordas isoladas; batimento deve ser medido, não inferido apenas da diferença nominal. Novos arquivos isolados, sem editar F9.6. Checkpoint inclui dispersão e rejeita mudança durante nota. Render 20 s, blocos de 1 s, continuidade física, sem loop, reverb ou clipping. Exclusão do fade editorial da análise.

Critérios definidos antes dos resultados: confrontar todas as variantes com controle, mesma janela/ganho; medir nível PCM absoluto e relativo, quedas 20/40/60 dB e contraste lateral nos dez parciais, relação P2/P1 inicial, energia por corda/polarização e passividade. Não escolher somente por cauda longa; preservar ataque (comparação auditiva e espectral necessária), evitar ampliar erro da segunda/terceira parcial; observar modulação/batimentos perceptivos (análise temporal fina ainda pendente). Comparar C5 com limites de duração/ruído e sem afirmar SPL absoluto comum. T60 padronizado, duração audível de 30–35 s, pedal e polifonia não demonstrados. Não promover automaticamente nenhuma variante; teste de 20 s e escuta antecedem novo refinamento. Workflow inicia ao push; resultados ainda não conhecidos no momento da gravação.

A duplicação isolada do renderizador mantém revisões F9.2–F9.6 congeladas, mas é dívida técnica a resolver por refatoração com testes de paridade antes de integração. Main, V10, UI, MIDI, outros motores e presets intactos.

## Verificação curta executada

Revisão 576e5388462a42513cef8839f422dc7af7d99d8a: ensaio V8 de 25 ms confirmou pressão numericamente idêntica e energia final idêntica ao controle F9.6 para ±0,5 cent. As variantes ±0,25 e ±1 cent tiveram erro relativo L2 da pressão de 0,006058% e 0,024205%, respectivamente. Resíduo máximo 8,595e-15 J, aumento de energia observado zero e sem recontato nos três casos. Isso preserva numericamente o ataque curto, não comprova equivalência perceptiva. [CI 45411276258](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45411276258). F9.7 tests passed: 8; F9.6 tests passed: 9; F9.5 tests passed: 13; F9.3 tests passed: 12 Estado dos jobs no relatório JSON; resultados de 20 s precisam ser lidos antes da seleção. Nenhuma promoção ou integração.

## Resultado de 20 s e avaliação auditiva

Feedback do titular após demonstrações F9.6: "o sustain aumeuntou um pouquinho" (sic). Melhora percebida discreta, não aprovação. CI [45411276258](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45411276258): quatro jobs concluídos com sucesso, 42/42 testes Node, três WAVs de 20 s, ganho comum, zero clipping (gate do exportador), sem recontato, resíduo máximo 1.8311e-14 J. Análise até 19,5 s sem fade.

| Dispersão (cent) | Global -40 dB | Global -60 dB | P1 -40 dB | P1 -60 dB | P2 -40 dB | P3 -40 dB | PCM relativo ao controle aos 10 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| ±0.25 | 7.5 s | 15.5 s | 8.5 s | 16.5 s | 9 s | 7 s | 0.199 dB |
| ±0.5 | 7.5 s | 15.5 s | 8.5 s | 16.5 s | 9.5 s | 6.5 s | 0.000 dB |
| ±1 | 7.5 s | 15 s | 8 s | 17 s | 9.5 s | 7.5 s | -0.454 dB |

Quedas são início de janela de 0,5 s confirmada por janela seguinte, não duração audível. Dispersão entre ±0,25 e ±1 cent não trouxe ganho material global: todas -40 dB em 7,5 s; aos 10 s, diferença PCM comum de 0.199 e -0.454 dB. Variações de parciais e batimentos ainda requerem escuta; nenhuma nova afinação promovida. Manter ±0,5 cent, ângulo 0,5 rad e boardFactor 0,5 como controle de pesquisa. Próximo diagnóstico prioritário: perdas distribuídas intrínsecas das cordas, isolando termo constante de perdas dependentes de frequência e diferenciando a hipótese das duas polarizações. Necessário verificar dados de contraste, referência C5, ataque e cauda com ganho fixo, sem forçar 30–35 s. Pedal, ressonância simpática e reatância acústica não modelados; não confundir simulação de cordas livres com pedal. F9 aberta, main intacta.
