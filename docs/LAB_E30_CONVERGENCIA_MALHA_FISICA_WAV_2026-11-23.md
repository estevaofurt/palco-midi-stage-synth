# Stage Synth — E3.0 | Convergência espacial da radiação física e WAVs audíveis

**23/11/2026** · pesquisa **PR #37** · `main` v1.12.8 intacta. O titular exige piano gerado **somente por modelagem física**, sem amostras, SoundFonts, resposta ao impulso gravada ou híbrido sample+modelagem. As gravações anteriores podem servir apenas como referência externa de escuta, nunca como insumo da geração.

## O que esta etapa realmente muda

Continuam **idênticos**: a mecânica passiva das 88 teclas, 592 coordenadas de cordas, dois modos acoplados de ponte/tampo, força de martelo, 70 eventos da partitura, CC64, geometria e posições dos microfones. Só é refinada a **quadratura espacial** da primeira integral de Rayleigh, com retardo geométrico e gradiente de velocidade para cada trecho do tampo:

- E2.9: 8×6 = **48 regiões**
- E3.0 intermediária: 12×8 = **96 regiões**
- E3.0 de referência numérica: 16×12 = **192 regiões**

**192 regiões não significam 192 modos vibratórios**: continuamos com os mesmos dois modos mecânicos generalizados do tampo. Como os parâmetros não foram calibrados e a carga acústica não realimenta a estrutura, nenhum WAV da etapa deve ser descrito como pressão real em Pa, síntese fidedigna certificada ou melhoria acústica aprovada.

## Código versionado, nenhum WAV de terceiros no repositório

- `research/compare-analytic-mesh-e30.mjs`: executa exatamente a mesma partitura, física e microfones nos três tamanhos de malha, calcula erros relativos L2 estéreo em relação à maior malha e fornece **ganho global comum** de escuta.
- `scripts/render_physical_mesh_e30.mjs`: gera três WAVs próprios da simulação, 13 s, 48 kHz estéreo PCM16, sem ler arquivos de áudio como entrada.
- `tests/compare_analytic_mesh_e30.test.mjs`: quatro novos testes de convergência, mesma energia/vozes mecânicas, WAV e proteção contra amostragem.
- `scripts/benchmark_analytic_mesh_e30.mjs`: benchmark offline das três malhas com 32/48/64 notas simultaneamente percutidas.
- `.github/workflows/stage-e2-passive-bridge.yml`: verifica código, regressões públicas, renderizações, custo e anexa relatórios/WAV; não altera DSP, UI, presets ou MIDI do aplicativo publicado.

## Evidências E3.0

[GitHub Actions de cálculo completo — run 45225140127](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45225140127): **221/221 testes aprovados**, WAVs `e30-physical-48-patches.wav`, `e30-physical-96-patches.wav`, `e30-physical-192-patches.wav` produzidos com o mesmo ganho.

Erro L2 relativo usando 192 regiões como **referência numérica local**, não como verdade acústica medida:

| Quadratura | Erro relativo à 16×12 |
|---|---:|
| 48 regiões (8×6) | **1,0539%** |
| 96 regiões (12×8) | **0,3976%** |
| 192 regiões (16×12) | Referência interna |

Isso indica **convergência numérica sob a geometria arbitrada**, mas o erro perceptual pode ser inaudível e a qualidade do piano **não foi demonstrada**. O WAV da malha 48 foi reproduzido localmente, com **SHA256 idêntico** ao WAV E2.9 original `f4f3c19de2c5d4bfad780dd4c633b3841330dd5357481cd3d74da1eee9b12d45`. O WAV E3.0 192 regiões gerado localmente e na CI também teve **o mesmo SHA256** `92f037d69beda44477c7eb42d4c0784d368fa3aaf5c8931e926d51a533b04b23`; possui 2.496.044 bytes (13 s, PCM16 48 kHz estéreo). Nenhum sample externo foi carregado na cadeia.

CPU Node/Linux (bloco 128 frames/48 kHz, orçamento teórico 2,667 ms), com 192 regiões: **p95 = 1,119 / 1,103 / 1,121 ms** para 32/48/64 notas, respectivamente. Medição apenas de **solver e radiador offline Node**, não browser AudioWorklet, MIDI real, FX ou hardware PC/Android. No mesmo runner, p95 com 48 regiões e 64 notas foi **0,871 ms**. Os números são aproximados e variam por aquecimento do runtime e cache.

[Regressão do Stage Synth — run 45225140358](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45225140358): aprovada. Os motores públicos **A/B/C/D/Clássico**, FX, presets, MIDI, HTML e versão continuam intactos.

## Próxima decisão técnica

A convergência mostra que **aumentar a malha não resolve sozinho o timbre**. Antes de adicionar mais regiões ou chamar E3.0 de melhoria audível, a prioridade é melhorar e validar a **mecânica física da excitação**, as perdas e modos de tampo/ponte, espacialidade e carga ar→tampo, sem gravar ou reproduzir notas de um piano no motor. Usar gravações externas somente para diagnóstico espectral e escuta quando permitido. Evitar afirmar realismo antes de comparação nivelada e teste de 32–64 notas em browser/hardware.

**Status:** E3.0 isolado em PR draft #37, R-GATEs comerciais 0/7. Nenhuma integração no aplicativo principal.
