# Stage Synth — E3.4: demonstração auditiva com escalas, arpejos e acordes (23/11/2026)

## Pedido do titular
Após diagnosticar falta de dureza/percussão do martelo e acrescentar endurecimento não linear do feltro e 16 modos de vibração distribuída do tampo na E3.4, o titular solicitou **"gerar um wav do modelo tocando escals e acordes"**.

A renderização foi executada e **entregue diretamente em WAV**, na conversa, com os três arquivos separados e a versão completa; ZIP contendo WAVs/relatório também disponível. A geração está isolada na PR #37 em estado draft. A `main` v1.12.8, motores A/B/C/D/Clássico, MIDI, FX, presets e HTML não foram alterados.

## Implementação real

Código: `scripts/render_e34_scales_chords.mjs` invoca sem alteração/substituição os módulos versionados
`ReactiveFeltDistributedPianoE33`, `PassiveDistributedSoundboardE33` e `AnalyticSpatialPlateRadiatorE33`.
Configuração: **16 modos de vibração do tampo**, feltro com `feltHardeningRatio=12` e `feltHardeningThresholdM=0.00016m`, saída Rayleigh analítica 8×6 patches, **WAV estéreo 48kHz PCM16**.

O fluxo de cada nota consiste exclusivamente de condições iniciais de um martelo móvel, contato unilateral não linear, vibrações de corda, resposta passiva de ponte/placa e integração de radiação espacial. Não há amostra de piano, ataque PCM gravado, SoundFont, resposta ao impulso medida, noise layer ou convolver na geração. Não existe resampling de áudio de nota para mudar a altura: **cada nota/velocidade solicitada é simulada pela física**.

### Limite essencial da síntese de acordes

O E3.4 possui **apenas um martelo reativo por instância**, então os acordes são feitos pela **soma linear das pressões sonoras de notas sintetizadas em instâncias físicas independentes**. Dentro de cada nota, o sistema de 88 cordas está mecanicamente conectado à sua própria ponte e tampo, mas **não há interação cruzada de vários martelos no MESMO tampo** durante o acorde. Portanto, o WAV ilustra acordes auditivamente sem provar a polifonia física coletiva de 32–64 notas ou a CPU em tempo real. A soma é acústica por superposição; não é sample playback de gravações de piano. Os pares/chordes foram ligeiramente desencontrados em 12ms por nota; nenhuma faixa percussiva artificial é adicionada.

## Partitura — 74 notas, 50 simulações distintas

- 0,22s: escala Dó maior ascendente e descendente (C3–C4)
- 5,045s: escala Sol maior ascendente e descendente (G3–G4)
- 9,99s: arpejo Dó maior
- 13,13s: arpejo Lá menor
- 16,43s: acorde Dó maior
- 18,87s: acorde Lá menor
- 21,31s: acorde Fá maior
- 23,75s: acorde Sol7
- 26,19s: resolução em Dó maior

## WAVs verificáveis

| Arquivo | Duração | Bytes | SHA-256 |
|---|---:|---:|---|
| `Stage_Synth_E34_Escalas_Arpejos_Acordes_Fisica_Pura.wav` | **29,080 s** | 5.583.408 | `613802b708a97a9c2f2002358674e63fd741e10b66e93f3b03d8551504a70e7c` |
| `Stage_Synth_E34_Escalas_Fisica_Pura.wav` | 9,870 s | 1.895.084 | `56507b9e4739e2b3c5c93151c4fded206e8470370017dc07d49339141e87edd7` |
| `Stage_Synth_E34_Acordes_Fisica_Pura.wav` | 12,770 s | 2.451.892 | `f6d9918d4339204c2f420b3c6b77acd33a488f5c732d99af47c2a42103ec2b58` |

Os SHA256 foram verificados **localmente, após extrair o ZIP do GitHub**, e coincidem com o JSON do relatório gerado no workflow. Os três WAVs são decodificados por `soundfile`, 48kHz, 2 canais, PCM16. O arquivo completo tem pico absoluto ~0,78 da escala de amplitude digital (não clipa) e RMS global ~0,071. A duração não prova realismo; é apenas um arquivo reproduzível.

## Resultado CI e confiabilidade

[CI da PR #37 (execução 45242466276)](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45242466276): **279/279 testes Node aprovados**, 0 falhas; três WAVs e `stage-e34-scales-chords-report.json` anexados no artefato `stage-e34-escalas-acordes-fisica-pura`. [Regressão Stage v1.12.8 (execução 45242466043)](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45242466043): aprovada.

O relatório informa **74 eventos de nota, 50 vozes diferentes realmente calculadas**, 29,08s, pico de força de contato generalizada 459,32 (não medida/qualificada em Newtons), e resíduo máximo relativo de balanço de energia ~1,44×10⁻¹³ nas instâncias isoladas.

**Não declarar que o timbre já é de piano aprovado.** O titular rejeitou as E3.0/E3.2 em realismo, e ainda não avaliou esta sequência. Falta calibrar modos/acoplamento reais da ponte/tampo, medir espectro de 2–5 kHz e decaimento de notas, desenvolver contato de múltiplos martelos no mesmo solver, validar 32–64 notas em AudioWorklet/PC/Android e realizar escuta com ganho nivelado.

**Status:** pesquisa, DRAFT, R-GATEs 0/7; preservar o motor público até validação.
