# Stage Synth — E2.3: banco modal com parciais ligados à ponte passiva (23/11/2026)

## Hipótese testada
A E2.1 tinha apenas uma frequência fundamental e duas polarizações em cada tecla. Isso deixa de fora a estrutura harmônica da corda mesmo antes da radiação do tampo. Nesta etapa foi criado `research/shared-passive-modal-piano.mjs`, **separado do motor público D**. Não adiciona som de madeira ou efeitos. Cada modo de corda tem deslocamento, velocidade, massa, rigidez, amortecimento e uma mola passiva ligada ao **mesmo** sistema de ponte/tampo de dois graus de liberdade.

- Teclas MIDI 21–60: **até cinco parciais × duas polarizações**.
- Teclas MIDI 61–108: **até dois parciais × duas polarizações**.
- Omissão de modos acima de 42% da amostragem para controle de aliasing.
- Total a 48 kHz nas configurações de laboratório: **592 coordenadas de corda + duas da ponte/tampo**, preservando as 88 teclas permanentemente ligadas; portanto mais modalidades, não mais instrumentos independentes.
- Formato de parcial esticado por coeficiente de inarmonicidade positivo; projeção mecânica da força do martelo pela posição de golpe, com pesos assinados. Parciais **não** são adicionados à saída como osciladores sem reação: a saída do laboratório é exclusivamente velocidade mecânica da ponte/tampo, resultado do solver conjunto.
- Método de ponto médio implícito com complemento de Schur O(N), sem criação de objetos por amostra, com `E_depois - E_antes = trabalho_externo - energia_dissipada` verificado em testes.

## Testes
`tests/shared_passive_modal_piano.test.mjs` verifica oito casos: estrutura harmônica de 88 teclas, inarmonicidade, silêncio, balanço de energia a 44,1/48/96 kHz, transições de tecla/pedal, transmissão a nota não golpeada por ponte compartilhada, 32/48/64 teclas e parâmetros inválidos. Regressão Stage executada no GitHub Actions.

## Resultados reproduzíveis
[GitHub Actions E2.3 run 45197948158](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45197948158): **192/192 testes aprovados**; benchmark e `git diff` dos módulos públicos também aprovados.

| Teclas acionadas | Coordenadas de cordas | p95, bloco 128 @48kHz | Parcela de 2,667ms |
|---|---:|---:|---:|
| 32 | 592 | 0,77202ms | 28,95% |
| 48 | 592 | 0,77999ms | 29,25% |
| 64 | 592 | 0,78471ms | 29,43% |

**Cautela:** benchmark de mecânica em Node/Linux, sem Audioworklet/browser, motor Stage D, FX, radiação ou hardware PC/Android. Na estrutura compartilhada, o custo é dominado pelos **592 modos ligados permanentemente**, não pelo número de notas pressionadas, o que explica tempos próximos para 32/48/64 notas. O desempenho indica que ainda precisamos otimizar antes de incluir toda a cadeia — não certifica 64 notas. Na prática um piano real tem múltiplas cordas em uníssono por tecla e resposta do tampo com muito mais estrutura. Este modelo de dois modos de placa não é calibração acústica de piano.

## Limites e decisões
Nenhuma frequência de placa, mobilidade mecânica, rigidez/atrito de corda, duração/força do martelo ou função de transferência ponte→pressão foi identificada por medição do instrumento. O `boardVelocity` é grandeza mecânica normalizada, **não um WAV de piano**. O contrato E2.2 exige FIR medido e autorizado, além de calibração SI real; não é permitido introduzir uma FIR sintética para apresentar avanço comercial.

**Não fazer merge ao D público** sem auditoria física/acústica, escuta e CPU real. D v1.12.8 permanece, com A/B/C/Clássico/default C, MIDI/CC64, FX, UI, presets e arquivos históricos inalterados. R-GATEs 0/7. A PR #37 segue em draft para pesquisa.
