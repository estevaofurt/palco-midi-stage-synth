# Stage Synth — D v1.12.8, experimento isolado de uníssonos graves (aguardando escuta)

**Base pública:** `main` commit `b20c4c4`, Stage v1.12.7, motor D experimental. **Mudança autorizada pelo titular:** atualizar o motor D e gerar WAV para verificar sonoridade.

## Causa e modificação delimitada

Na v1.12.7, o D define `single=key<37`, tornando toda nota **A0–C2 (MIDI 21–36)** um único ressonador por parcial, mesmo onde pianos de cauda têm cordas graves pareadas (bichord). Isso não é apenas uma escolha de EQ: elimina o **uníssono entre duas cordas e sua dupla cauda de decaimento** nessa faixa. O projeto já possui caminho para dois ressonadores levemente desafinados, com decaimentos prompt/aftersound desiguais — mas o código o desligava em C2.

Implementação original `physical-piano-hybrid-v128-candidate.js` altera **somente** o limite de uma cadeia de uníssonos: `single=key<29`, permitindo bicord/duas vias de ressonância em **F1–C2 (MIDI 29–36)**. Oito teclas mais graves **A0–E1** mantêm caminho antigo. Tudo a partir de **C#2 (MIDI 37)**, incluindo C3/C4/C5/C6, preserva computação bit a bit. **Crossover é uma aproximação**, não mapa medido especificamente no Steinway B. Um modo numérico por corda não é modelagem rigorosa de duas polarizações físicas; `PianoResonanceBody` permanece com resposta radiativa não calibrada.

O motor anterior exato foi congelado como `physical-piano-hybrid-v127.js`. O candidato foi criado separadamente, **ainda não conectado a AudioWorklet da página pública e não aprovado como nova versão estável**. O conjunto de testes `tests/bass_unison_v128_candidate.test.mjs` compara os dois motores, checa identidade de PCM de regiões imutáveis, notas alteradas, finitude, limite da saída, pedal/CC64 e 32/48/64 vozes. `scripts/render_piano_d_v128_candidate_wav.mjs` gera três WAVs reais: D v1.12.7, candidato e comparação A/B, **PCM estéreo de 24 bits a 48 kHz, ganho linear único, sem efeitos nem amostras externas**.

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
