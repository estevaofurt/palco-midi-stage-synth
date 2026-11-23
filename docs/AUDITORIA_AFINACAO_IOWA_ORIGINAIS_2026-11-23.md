# Stage Synth — auditoria independente da afinação das fontes Iowa originais (E1.2)

**Data:** 23/11/2026. **Base pública protegida:** Stage v1.12.7, commit `04049ae`. Esta etapa é de **avaliação de fonte e preparação de calibração**, sem qualquer alteração de motor, timbre, presets ou versão pública.

## Problema concreto

Os 15 AIFF Steinway B/Iowa (C2–C6 × pp/mf/ff), já verificados por SHA-256, foram usados como referências de comportamento espectral e de ataque. Seu manifesto `research/commercial_audio/iowa_steinway_b_verified_original_sha256.json` informa **`pitchVerifiedByAnalysis=false` para todas as notas**. Há menções anteriores a divergência em rótulos de oitava; se uma comparação assumir a nota nominal sem conferir a afinação efetiva, poderá inferir um erro de harmônicos ou um ajuste de física inexistente.

## Auditoria implementada sem copiar áudio para o aplicativo

- `research/iowa-f0-label-audit.mjs`: estimativa por **YIN CMND** em duas janelas de 350 ms depois do início, com busca de frequência em faixa **±aproximadamente uma oitava** em torno do rótulo. Usa média de pares como decimação diagnóstica de 48→24 kHz. Não confundir esta decimação com SRC de produção ou inferência física de corda.
- A escolha de período é guiada por mínimos locais, e não pela maior parcial isolada. Avalia consistência de frequência entre janelas, limiar de periodicidade e diferença em cents do rótulo. Registra `label-consistent`, `label-mismatch-candidate`, `tuning-or-label-review` ou `inconclusive`.
- `scripts/audit_iowa_original_pitch_labels.mjs`: lê somente a matriz previamente aprovada de 15 fontes, exige correspondência entre ID, nota, dinâmica, **tamanho e SHA-256 originais**, além de codec e taxa originais. O `fetch_iowa_reference.py` realiza o download e decodifica PCM apenas em diretório temporário do runner; depois o workflow apaga todos esses bytes.
- `tests/iowa_f0_label_audit.test.mjs`: cenários sintéticos de C2–C6, fundamental fraca/ausente, fonte uma oitava acima do rótulo, silêncio, desafinação em cents e janelas contraditórias. **São testes de estimativa**, não gravações acústicas nem comprovação de resultado em piano real.
- `.github/workflows/iowa-original-pitch-label-audit.yml`: CI completo, proteção `git diff --exit-code` do DSP, análise dos originais e artefato somente JSON de **resultados numéricos**. Nada de áudio externo é enviado ao GitHub ou incorporado ao Stage.

## Interpretação conservadora

YIN também sofre erro sob **inarmonicidade**, cordas múltiplas, decaimento, ruído de martelo, cancelamento de fase, amostras com transientes e ressonâncias de sala. A estimativa de 2 janelas não é medição instrumentada de f0 de cada corda. Para evitar certificação falsa, notas com periodicidade insuficiente ou discordância entre janelas **não têm a identidade confirmada**. Um candidato a discrepância de oitava deve ser reproduzido por método independente e escuta antes de corrigir rótulos ou parâmetros do Stage.

A acústica da Iowa continua com microfones e sala, valores de pp/mf/ff **não são velocidade de martelo medida**, e a fonte não contém força de ponte `F_ponte`, mobilidade `Y=v/F`, acelerômetro de ponte nem a transferência radiativa H1 do E1.1. **Não altera 0/7 R-GATEs.**

## Critério de avanço

1. Testes Node do projeto e cenários sintéticos do novo auditor aprovados no GitHub.
2. Original 15/15: hash/tamanho/codec/identidade completos, execução numérica por amostra; resultados **candidatos** publicados somente em JSON e resumidos neste documento depois do CI.
3. Sem correção automática do nome da fonte, dos pesos de modo, da calibração D ou do motor A/B/C/D. **O objetivo é tornar a referência confiável antes do próximo ajuste perceptivo**, sobretudo no grave C2/C3.
4. Preservar v1.12.6 A/B, v1.12.7 D experimental, C4–C6, MIDI/CC64, FX, interface, presets e polifonia planejada 32/48/64; esta etapa não constitui homologação no PC/Moto g04s.


## Resultado efetivamente obtido — originais 15/15, dupla verificação

Workflow concluído com sucesso: [run 45178612159](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45178612159), **157/157 testes Node aprovados**, **6/6 testes YIN dedicados**, **4/4 testes de FFT/harmônicos dedicados**. Reaquisição oficial dos 15 AIFF com byte count, origem, codec e SHA-256 conferidos com o manifesto fixo. Resultados somente numéricos, sem artefatos WAV/AIFF/PCM; diretório efêmero removido.

**Resultados conservadores:**

| Nota | pp | mf | ff |
| --- | --- | --- | --- |
| C2 (MIDI 36) | YIN inconclusivo, espectro apoia rótulo | concordância dupla | YIN consistente, espectro inconclusivo |
| C3 (MIDI 48) | concordância dupla | concordância dupla | concordância dupla |
| C4 (MIDI 60) | concordância dupla | concordância dupla | concordância dupla |
| C5 (MIDI 72) | concordância dupla | concordância dupla | concordância dupla |
| C6 (MIDI 84) | YIN inconclusivo, espectro apoia rótulo | concordância dupla | concordância dupla |

- **YIN:** 13/15 rótulos consistentes, 2/15 inconclusivos. Os 13 desvios estimados do rótulo ficaram entre aproximadamente **+0,7 e +15,1 cents**; não são medidas instrumentadas de afinação individual de cordas.
- **FFT/harmonic comb:** apoia o rótulo em 14/15, e é inconclusivo para C2/ff. Usa busca de inarmonicidade ilustrativa, não um ajuste calibrado da rigidez real de cordas.
- **Dupla concordância:** **12/15** registros. **Três sem confirmação conjunta:** C2/pp, C2/ff e C6/pp. **Zero discrepâncias de oitava confirmadas por dois métodos.**
- Em **C6/pp**, as estimativas temporais foram contraditórias entre janelas (diferença de aproximadamente 1.207 cents), enquanto o verificador espectral apoia C6. Isso é **ambiguidade do sinal/estimador**, não prova de que a gravação seja outra nota.

### Decisão baseada nos dados

**Não corrigir nome das amostras, não reatribuir notas por suposição e não ajustar o D com base na análise inconclusiva.** A premissa de erro generalizado de oitava **não se sustentou** nos 15 originais inspecionados. O próximo ganho perceptivo deve concentrar-se no **ataque, evolução temporal dos harmônicos, reação da ponte e radiação real**, verificando piano grave contra gravações independentes; a investigação do conjunto Iowa não é substituto de medidas do martelo/ponte. Conservar 0/7 R-GATEs; 32–64 vozes ainda sem homologação no dispositivo.

