# Stage Synth — WAV de comparação direta D v1.12.6 × D v1.12.7

**Gerado em 23/11/2026** no workflow [45163713407](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45163713407) com `scripts/render_piano_d_ab_wav.mjs`. **O motor original arquivado da v1.12.6 e o motor experimental da v1.12.7 foram executados de verdade**, offline, sem gravar sample de terceiros ou importar material Steinway/Iowa para o repositório.

## Material gerado

Artefato temporário do GitHub Actions: **`stage-synth-d-v126-v127-comparacao-audio-wav-24bit`** (retido por 7 dias); contém:

- `01_Stage_D_v1.12.6_original_48k_stereo_24bit.wav` — 29,301 segundos
- `02_Stage_D_v1.12.7_martelo_48k_stereo_24bit.wav` — 29,301 segundos
- `03_COMPARACAO_AB_v126_depois_v127_48k_stereo_24bit.wav` — 60,103 segundos, versão antiga primeiro, silêncio de 1,5 segundo e versão nova
- `metadata.json` — sequência de notas, modelo, velocidades e ganho compartilhado
- `LEIA-ME.txt` — instruções e marcações temporais em português

Todos são **PCM WAV estéreo, 48 kHz, 24 bits**, característica qualitativa `american`, qualidade `studio`, sem efeitos externos adicionados. São renderizações do sintetizador Stage, **não gravações de piano acústico**.

### Sequência MIDI idêntica nos dois motores

C2 pp/mf/ff, C3 pp/mf/ff, C4 mf como guarda do médio-agudo, A1 mf grave profundo, acorde C2/G2/C3/E3/G3 e uma frase de C2 a C4 com CC64 e liberação. Todos os eventos note on/off, duração, velocidades, controles e ordem são iguais. Foi aplicado **um único ganho linear compartilhado de 5,731985**, calculado pelo pico mais alto entre ambas as execuções; **não há normalização independente** nem troca de qualidade entre versões. Isto preserva diferenças relativas de dinâmica e timbre.

No arquivo A/B, a nova v1.12.7 começa aproximadamente aos **30,80 segundos**.

### Verificações

O workflow passou **127/127 testes do código** antes do render, validou as três estruturas RIFF/WAVE (PCM 24, 48k, 2 canais), os tamanhos de arquivos, os frames iguais por motor, a ordem A/B e a duração da pausa. O contraste resultou em **2.766.651 amostras estéreo diferentes** (efeito real do DSP novo nos graves, não arquivos idênticos renomeados). O código original `physical-piano-hybrid-v126.js` e o novo `physical-piano-hybrid.js` são importados independentemente.

**Interpretação:** material de *escuta comparativa*. Não é certificação de semelhança com Steinway, fidelidade física do martelo, estabilidade de CPU no dispositivo real ou aprovação comercial: **0/7 R-GATEs integrais**. O usuário decide se a mudança sonora é preferível; dados acústicos anteriores indicaram melhora do transiente inicial mas piora parcial dos harmônicos sustentados.

**Reprodução:** `node scripts/render_piano_d_ab_wav.mjs artifacts/stage-d-comparacao-ab` sob Node 22+. Não alterar motores existentes para executar este render. O workflow tem gatilho manual `workflow_dispatch` e pode renovar o artefato quando necessário, sem guardar WAVs grandes no código-fonte.
