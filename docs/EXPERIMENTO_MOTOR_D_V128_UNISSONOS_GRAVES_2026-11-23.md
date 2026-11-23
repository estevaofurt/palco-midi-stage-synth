# Stage Synth — D v1.12.8, experimento isolado de uníssonos graves (aguardando escuta)

**Base pública:** `main` commit `b20c4c4`, Stage v1.12.7, motor D experimental. **Mudança autorizada pelo titular:** atualizar o motor D e gerar WAV para verificar sonoridade.

## Causa e modificação delimitada

Na v1.12.7, o D define `single=key<37`, tornando toda nota **A0–C2 (MIDI 21–36)** um único ressonador por parcial, mesmo onde pianos de cauda têm cordas graves pareadas (bichord). Isso não é apenas uma escolha de EQ: elimina o **uníssono entre duas cordas e sua dupla cauda de decaimento** nessa faixa. O projeto já possui caminho para dois ressonadores levemente desafinados, com decaimentos prompt/aftersound desiguais — mas o código o desligava em C2.

Implementação original `physical-piano-hybrid-v128-candidate.mjs` altera **somente** o limite de uma cadeia de uníssonos: `single=key<29`, permitindo bicord/duas vias de ressonância em **F1–C2 (MIDI 29–36)**. Oito teclas mais graves **A0–E1** mantêm caminho antigo. Tudo a partir de **C#2 (MIDI 37)**, incluindo C3/C4/C5/C6, preserva computação bit a bit. **Crossover é uma aproximação**, não mapa medido especificamente no Steinway B. Um modo numérico por corda não é modelagem rigorosa de duas polarizações físicas; `PianoResonanceBody` permanece com resposta radiativa não calibrada.

O motor anterior exato foi congelado como `physical-piano-hybrid-v127.mjs`. O candidato foi criado separadamente, **ainda não conectado a AudioWorklet da página pública e não aprovado como nova versão estável**. O conjunto de testes `tests/bass_unison_v128_candidate.test.mjs` compara os dois motores, checa identidade de PCM de regiões imutáveis, notas alteradas, finitude, limite da saída, pedal/CC64 e 32/48/64 vozes. `scripts/render_piano_d_v128_candidate_wav.mjs` gera três WAVs reais: D v1.12.7, candidato e comparação A/B, **PCM estéreo de 24 bits a 48 kHz, ganho linear único, sem efeitos nem amostras externas**.

## Evidência e limites científicos

O texto clássico de Gabriel Weinreich sobre **movimentos acoplados das cordas do piano** descreve uníssonos e dois estágios de decaimento; o fabricante Yamaha também documenta a passagem de cordas graves únicas para duas e três cordas por nota. Isso justifica experimentar a topologia, **não confirma a posição exata da transição no piano usado pela Iowa nem que o Stage soe mais realista**.

Fontes:
- Weinreich, *The Coupled Motions of Piano Strings* (doi pesquisável por título), https://nat.vu.nl/~henkb/Betamusica/Weinreich.pdf
- Yamaha, *Design of the Strings Enriches the Sound*, https://www.yamaha.com/en/musical_instrument_guide/piano/mechanism/mechanism004.html

### Regras para publicação

- Não promover sem CI verde, referência anterior congelada, comparação de WAV, escuta e nenhuma regressão em A/B/C, MIDI, FX ou seleção do módulo Piano.
- A diferença física de uníssono em uma faixa específica **não resolve por si só madeira, ponte, ressonâncias simpáticas ou radiação do tampo**, que ainda aguardam instrumentação comercial autorizada.
- Nesta fase **0/7 R-GATEs completos**, sem garantir 32–64 notas em dispositivo real; perfis `eco=32,balanced=48,studio=64` são capacidade de alocação apenas.
- Qualquer release público posterior deve usar novo cache-busting e preservar tanto a v1.12.6 quanto a v1.12.7 em arquivo de comparação real.


## Evidência executada — CI, WAV e comparação independente Iowa

- [GitHub Actions 45183947692](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45183947692): **162/162 regressões Node** e **5/5 testes específicos** aprovados. WAVs **48 kHz/24-bit estéreo** produzidos com os motores reais, mesmo ganho e sem FX, com validação por leitor WAV independente. Todo o DSP público, seleção de motor, UI, MIDI e presets permaneceu congelado neste PR.
- Foram novamente adquiridos e conferidos no runner **C2 mf e C3 mf Iowa Steinway B originais** (SHA256/tamanho/codec conferidos). Publicou-se somente o relatório numérico; os AIFF/PCM foram eliminados no CI.
- Primeira tentativa do uníssono (pesos prompt/aftersound 63/37 como nos agudos): **C2 mf:** melhora do erro 0–12ms de **−0,50 dB**, mas piora do erro na cauda 900–1400ms de **+2,03 dB**. **Reprovada como candidata final**.
- Segunda tentativa com contribuição inicial igual **50/50** dos dois modos **somente F1–C2**: melhora do erro C2 mf 0–12ms de **−0,34 dB**, piora em 12–36ms de **+0,28 dB**, piora da cauda 900–1400ms de **+0,87 dB**. Erro médio relativo dos 7 harmônicos confiáveis diminuiu modestamente nas quatro janelas de 171 ms (**−0,035 / −0,160 / −0,347 / −0,152 dB**); este conjunto já foi usado em calibrações anteriores (**in-sample**, não homologação). **C3 mf ficou numericamente idêntico** em todos os parâmetros, como esperado.
- Para C2 mf os WAVs novos (não comparáveis a uma gravação real, pois são duas sínteses) indicam cauda 900–1300ms aproximadamente **−1,21 dB** frente ao D v1.12.7, contra −2,48 dB da primeira tentativa. **Isto não prova mais fidelidade**, tampouco demonstra madeira/ponte/radiação físicos. As mudanças são audíveis somente se o ouvinte conseguir diferenciá-las.
- **Decisão da etapa de pesquisa**: preservar o candidato revisado e seu áudio de teste; **não declarar R-GATE aprovado ou som melhor**. Uma integração posterior no **mesmo seletor D do Piano Acústico** será explicitamente experimental, com caminho histórico verificável para D v1.12.7 e CI separado. Não integrar PR #26 nem inventar harmônicos de "madeira".
