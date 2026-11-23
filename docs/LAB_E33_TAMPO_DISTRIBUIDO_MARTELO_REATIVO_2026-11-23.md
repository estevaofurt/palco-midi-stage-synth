# Stage Synth E3.2–E3.3 — WAV reativo e tampo distribuído (23/11/2026)

## Decisão de produto e estado real

O titular rejeitou o som E3.0: **não tem timbre de piano**. A ordem é preservar o objetivo de **som exclusivamente de modelagem física**, sem camadas de gravações, SF2, IR gravada, ataque PCM, misturas híbridas ou reverb amostral. A v1.12.8 do Stage Synth em `main` e motores A/B/C/D/Clássico permanecem inalterados. Pesquisa em **PR #37 — DRAFT**, portas comerciais 0/7. **Nenhuma versão nova foi aprovada na escuta**.

## E3.2 — primeiro WAV de martelo reativo

`scripts/render_reactive_felt_e32.mjs` gera dois WAVs **PCM16 estéreo, 48 kHz, 5,4 s** com Dó3, Mi3, Sol3 e Dó4 **sequenciais, cada nota reinicializada com seu próprio solver de 88 teclas**, para não fingir polifonia de martelos. Usa estritamente `ReactiveFeltModalPiano` (o contato unilateral e bidirecional com gradiente discreto), `SharedPassiveModalPiano` 88 teclas e `AnalyticSoundboardRadiator` com entrada **apenas `boardPanelVelocity` no modo de placa**. A velocidade localizada da ponte NÃO é distribuída indevidamente em toda a área do tampo. A modelagem do ar é Rayleigh calculado geometricamente, **sem resposta ao impulso gravada**. O código não lê WAV de piano.

- `e32-reactive-old-mass-physical.wav`: SHA256 `aad22d91ce14721d4839e65c0d4fde3d881fe0ae6945a47589590ad696d6ea88`, 1.036.844 bytes.
- `e32-reactive-geometry-mass-physical.wav`: SHA256 `d817db4479f211bdff4532d57e4a38e3ba9557f631fc2a9ad2cbc1e0eb0de23e`, 1.036.844 bytes. Corda idealizada **0,85m, raio 0,6mm, aço 7850 kg/m³** aplicada como massa modal uniforme em todo o teclado **somente para isolar a hipótese**, não modelo físico válido de 88 cordas medidas.
- Comparativo independente e privado de escuta entregue ao titular diretamente na conversa, **11,2 s, mono 48 kHz**. Os WAVs do GitHub são novas renderizações feitas pelas classes oficiais versionadas (estéreo); por isso não possuem o mesmo SHA256 do arquivo mono da conversa. As amplitudes de pressão relativa são normalizadas para escuta e **não permitem comparar SPL físico**.
- Em ambos os casos o quinto harmônico do painel continua profundamente insuficiente; **não houve demonstração de melhoria auditiva**.

## E3.3 — nova estrutura fisicamente distribuída (não apenas mais regiões de quadratura)

`research/passive-distributed-soundboard-e33.mjs` conecta as **88 teclas, 592 coordenadas das cordas, uma ponte localizada e 2/4/8 modos físicos ativos de tampo** pelo termo elástico passivo:

`V_c = 1/2 * k * (x_ponte - Σ φ_j(u_ponte,v_ponte) q_j)^2`.

Cada modo do painel tem massa, perda viscosa positiva, mola própria e formato espacial senoidal independente `φ_{m,n}(u,v)=sin(mπu)sin(nπv)`. A matriz densa **9×9** das coordenadas de ponte e tampo é **simétrica definida positiva** e resolvida por Cholesky; cordas usam complemento de Schur O(N). O balanço energia/trabalho/perdas foi testado. Esses modos do tampo representam movimentos físicos independentes, ao contrário das 48/192 regiões da quadratura E3.0, que só refinavam a radiação de dois graus de liberdade.

`research/reactive-felt-distributed-e33.mjs` une esse tampo ao **mesmo conceito de martelo não linear E3.2**, com predição de complacência `dq/dF` que incorpora a ponte e **todos os modos do painel** através de `[S⁻¹]_00`, força de reação e gradiente discreto do potencial. É apenas **um martelo em contato por instância**, mas a rede de 88 teclas permanece permanentemente acoplada. Testes de conservação permanecem na ordem de arredondamento numérico.

`research/analytic-spatial-plate-radiation-e33.mjs` integra a **primeira integral de Rayleigh** para os modos independentes da **velocidade espacial do tampo**, não para `bridgeVelocity` localizada. Usa 48 regiões e retardos geométricos até dois pontos de escuta. Não contém convolução com IR acústica ou samples externos.

### WAVs da E3.3 para comparação exploratória

`scripts/render_reactive_spatial_e33.mjs` gerou, no CI, duas faixas do mesmo roteiro C3–E3–G3–C4, com **3,8 s, 48 kHz, estéreo, PCM16**, um martelo reativo por nota renderizado de condições iniciais separadas:

| Modelo do tampo | Arquivo | SHA256 |
|---|---|---|
| 2 modos físicos de placa | `e33-reactive-spatial-2-plate-modes.wav` | `87a6ac4f3b2ba947741084298934e3c44230912d97d3567b9cf6d99dda7e092b` |
| 8 modos físicos de placa | `e33-reactive-spatial-8-plate-modes.wav` | `b4b7d29ec60661df0c94e20f8334d23da572f955e637ca065f2fd5de648c95b3` |

**Importante:** o ganho foi normalizado **separadamente** em cada faixa, e os parâmetros de massa, geometria, frequência modal e amortecimento são ilustrativos. Não afirmar ganho de timbre, proximidade com piano real ou equivalência de pressão acústica.

## Evidência e desempenho

[GitHub Actions E3.3 — run 45235950810](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45235950810): **273/273 testes Node aprovados**. Inclui testes de 88 teclas e oito modos realmente acoplados, passividade mecânica e energia do martelo, Cholesky SPD, dissipação/CC64, causalidade e simetria estéreo da radiação, ausência de samples/IR e WAVs offline.

Benchmark E3.3 da rede física sem radiação aérea, perfis de **2/4/8 modos de tampo**, 128 frames/48kHz, Ubuntu Node. Para **8 modos**, p95 de bloco foi **0,787 / 0,809 / 0,777 ms** em 32/48/64 teclas respectivamente. O orçamento ideal por bloco é ~2,667 ms. **As 32/48/64 teclas nesse benchmark foram excitadas pelo antigo pulso de força predefinida, NÃO por 32/48/64 martelos reativos concorrentes; e o radiador espacial não faz parte desse benchmark**. Portanto isso não certifica polifonia reativa, desempenho do modelo completo, execução AudioWorklet, Windows ou Android.

[CI baseline do aplicativo no commit de implementação](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45235950728) passou. Verificação explícita do diff em DSP público, UI, MIDI, presets, FX etc não encontrou alterações. Nenhuma mudança publicada.

## Riscos e próximos experimentos (sem atalhos amostrais)

1. Não promover como som de piano o E3.2/E3.3 até aprovação auditiva. A modelagem do tampo é mais completa, mas **o ataque, distribuição harmônica e perdas das cordas ainda não estão identificados com dados físicos de piano**.
2. Próximo passo: **E3.4** — massas/tensões/comprimentos individualizados por nota, cordas rígidas dispersivas ou waveguide físico com perdas de frequência, contato martelo–corda baseado em geometria do ponto de percussão; depois afinação dos modos de tampo com mobilidade física.
3. Implementar **múltiplos martelos concorrentes** usando matriz de complacência de contato conjunta, preservando gradiente discreto e positividade; somente então medir 32/48/64 notas reativas com radiação e FX em AudioWorklet/hardware real.
4. Executar comparação por escuta nivelada, harmônicos e decaimento sobre **piano gravado apenas como referência externa**. Nenhum PCM gravado entra na síntese, independentemente de sua licença.
5. Continuar PR #37 DRAFT e a v1.12.8 estável; R-GATEs comerciais **0/7**.

**Conclusão:** já há um WAV direto da etapa E3.2 e uma cadeia E3.3 mecânica e acústica reproduzível no GitHub. Isso é evolução de **estrutura física e engenharia**, **não timbre de piano comprovado**.
