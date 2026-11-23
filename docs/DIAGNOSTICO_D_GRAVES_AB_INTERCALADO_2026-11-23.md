# Stage Synth — E1.3: comparação direta dos graves do motor D (WAV verdadeiro)

**23/11/2026.** Ponto de partida: \`main\` commit \`b882650\`, Stage público v1.12.7. O motor D 1.12.6 histórico e o D 1.12.7 experimental são preservados. A prioridade do proprietário continua **menos sensação de violão, mais corpo acústico/ressonância de piano**, sem perder o avanço de C4–C6.

## Por que a comparação anterior não foi suficiente?

O render \`scripts/render_piano_d_ab_wav.mjs\` gera **dois WAV genuínos dos motores Stage**, 48 kHz, estéreo, 24 bits, com notas, velocity, pedal e ganho rigorosamente iguais e sem efeitos externos. O A/B original tem cerca de 30 s de cada versão, separados por 1,5 s. Depois de ouvir a primeira execução, foi observado que os motores parecem quase iguais — comparar longas sequências aumenta a carga de memória auditiva.

Novo \`scripts/assemble_stage_d_bass_interleaved.mjs\`: organiza **os mesmos PCM reais** em pares imediatos de 1,98 s, sempre **v1.12.6 e depois v1.12.7**, com silêncio de 0,27 s entre versões, 0,60 s entre notas, 120 ms antes do ataque e fades de 10 ms somente nas bordas do recorte. O primeiro transiente da nota fica **fora do fade**. A montagem não muda frequências, filtros, reverb, ressonadores, envelope, estado de pedal ou normalização original. Não é um novo motor.

Programa reproduzível: C2/C3 pp/mf/ff, C4 mf como controle comparativo, A1 mf e acorde C2/G2/C3/E3/G3. O material contém ressonâncias remanescentes de notas anteriores **igualmente presentes em cada versão**, então C4 pode apresentar pequena diferença por dependência do contexto, embora o próprio código C4–C6 continue congelado.

## Resultado numérico observado no WAV real original

Diferença de energia entre **D 1.12.7 menos D 1.12.6**. Valores em dB são razões de RMS nas mesmas janelas temporais e mesmo ganho; negativos indicam menor energia no D 1.12.7. **Isto não é erro versus piano acústico, nem ABX ou prova de fidelidade.**

| Nota / intensidade | Primeiro 0–12 ms | Corpo 100–220 ms | Cauda 900–1180 ms |
| --- | ---: | ---: | ---: |
| C2 pp | −4,14 dB | −0,08 dB | +0,01 dB |
| **C2 mf** | **−4,38 dB** | **0,00 dB** | **+0,03 dB** |
| C2 ff | −5,40 dB | 0,00 dB | +0,02 dB |
| C3 pp | −0,16 dB | +0,09 dB | +0,11 dB |
| C3 mf | −1,14 dB | −0,26 dB | +0,10 dB |
| C3 ff | −1,19 dB | +0,07 dB | +0,17 dB |
| C4 mf | 0,00 dB | 0,00 dB | 0,00 dB |
| A1 mf | −4,02 dB | −0,01 dB | −0,01 dB |
| Acorde grave mf | −4,85 dB | −0,99 dB | −1,20 dB |

O principal efeito candidato do "martelo grave" v1.12.7 na região C2/A1 é **atenuar os primeiros milissegundos**; o corpo individual e a cauda apresentam praticamente a **mesma energia**. Isto é coerente com a experiência de pouca diferença auditiva, mas a relação causal entre essa energia e a sensação de violão **não está demonstrada**. O próprio estudo anterior Iowa mostrou melhora do transiente e piora em espectro/cauda; não classificar v1.12.7 como universalmente melhor.

## Regras para a próxima tentativa sonora

1. **Não acrescentar mais ruído agudo, novos harmonizadores ou "wood" aditivo da PR #26**: foi ouvido como ruído e reprovado.
2. Antes de mexer no DSP, medir **evolução temporal de parciais** e estrutura de decay/duplo decaimento nos graves em comparação com gravações acústicas originais, dando prioridade a C2 mf/C3 mf **duplamente consistentes** na auditoria de afinação E1.2.
3. Para caráter real de tampo/ponte, a resposta deve ser fisicamente identificável e ter caminho de **radiação acústica**, não multiplicação de senoides aleatórias; E1.1 H1 ainda não tem sensores reais licenciados.
4. Um eventual candidato D isolado deve demonstrar **melhoria mensurável em janelas distintas** mais escuta cega, não apenas um ataque diferente. Conservar A/B/C/Clássico e C4–C6, MIDI/CC64, FX, UI, presets, versão pública e capacidade planejada 32–64 vozes.
5. O renderizador e a comparação original são reproduzíveis somente a partir de **código próprio Stage**, sem amostras de pianos de terceiros no aplicativo, Git ou artefatos. Entregar WAV como artefato temporário do GitHub Actions. **R-GATEs 0/7**, Android/PC não homologados.

## Evidências e reprodução

- Base histórica: \`physical-piano-hybrid-v126.js\`; versão D atual: \`physical-piano-hybrid.js\`.
- Fonte áudio original: \`scripts/render_piano_d_ab_wav.mjs\` / [run 45163713407](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45163713407).
- Montagem intercalada: \`scripts/assemble_stage_d_bass_interleaved.mjs\`. Workflow isolado: \`.github/workflows/render-piano-d-bass-interleaved.yml\`.
- Nenhuma nova alegação de qualidade sonora nem homologação comercial.
