# Stage Synth — E2.7 | Quatro bancos privados com auditoria de afinação e comparação A/B

**23/11/2026.** Continuação da PR experimental #38. **Não houve integração ao motor D**. Todas as gravações permanecem fora do GitHub e do site público.

## Materiais privados do titular
Foram reanalisados os quatro arquivos de áudio fornecidos anteriormente: `American(1).wav`, `Japanese(1).wav`, `Felt(1).wav`, `Upright(1).wav`. Cada arquivo possui 44 kHz, estéreo e aproximadamente 386,91 segundos, com eventos musicais alinhados em tempos equivalentes. As 12 janelas escolhidas por instrumento cobrem as raízes C1, C2, C3, C4, C5 e C6, com **duas amostras por nota** identificadas como `v60` e `v110`. Essas tags são intensidade NOMINAL; não foram identificados dados MIDI originais que permitam validá-las como velocity 60 ou 110.

**Entregas feitas somente no diálogo privado do titular:**
- 48 arquivos WAV PCM24 para importação local — 12 para cada instrumento.
- Quatro ZIPs independentes, cada um **abaixo de 8 MB**, para facilitar transferência e importação por instrumento.
- Um ZIP combinado com HTML autônomo E2.7, selector de American/Japanese/Felt/Upright, teclado de 88 notas, Web MIDI opcional, CC64, corte e troca de bancos carregados.
- 12 escutas A/B, C2/C3/C4 em cada uma das quatro referências, sempre alternando **motor D American v1.12.8** e a gravação correspondente da biblioteca privada. A gravação do D não é um motor Japanese/Felt/Upright, portanto A/B cruzado entre marcas é comparativo informal e não experimento controlado de DSP.
- Manifesto com SHA256 dos arquivos-fonte, origem, trechos, RMS, picos, metodologia e ressalvas de licenciamento.

## Código reprodutível em GitHub, sem gravações

- `research/private-pcm-pitch-audit.mjs`: análise de família harmônica com janela Hann + FFT, comparando a raiz declarada com ±1 e ±2 semitons, inclusive quando a fundamental é mais fraca que os sobretons. **Não resolve independentemente ambiguidade de oitavas** nem identifica uma origem acústica; resultados permanecem evidencia de afinação relativa, não confirmação acústica comercial.
- `scripts/audit_private_piano_bank.mjs`: CLI de execução **local e offline**, leitura de WAV `MIDI##_v##.wav`, saída em JSON por nota, erro de processo se houver etiqueta incompatível e relatório sem bytes de áudio. Executar `node scripts/audit_private_piano_bank.mjs /CAMINHO/PARA/BANCO [RELATORIO.json]`. Sem serviço de rede.
- `tests/private_pcm_pitch_audit.test.mjs`: testes com WAVs sintéticos construídos em memória, incluindo fundamental ausente, nota errada por semitom, PCM16/24, silêncio, parâmetros inválidos e execução da CLI com bancos locais falsos.
- `.github/workflows/stage-e26-private-samples.yml`: testes completos Stage, checks do CLI, guarda do motor público e proibição de áudio/arquivos ZIP versionados.

**Falha e correção:** a primeira tentativa da rotina de FFT falhou em duas provas sintéticas por pular o XOR final da reversão de bits. A correção da permutação foi aplicada antes de continuar; não se relaxaram limiares dos testes.

## Evidência privada de extração E2.7

Em auditoria local independente com `scipy/numpy`, 48/48 trechos tiveram contraste positivo superior a **7,6 dB** entre a família harmônica declarada e a melhor hipótese dentre quatro semitons vizinhos. Os menores contrastes por banco foram aproximadamente: American **7,66 dB**, Japanese **7,87 dB**, Felt **7,82 dB**, Upright **8,05 dB**. Essa checagem **não examina a oitava fora desse raio, a altura absoluta com um detector independente, a velocity original ou a licença**. Há apenas seis notas raízes por instrumento e a interpolação/transposição entre elas pode piorar o timbre.

**GitHub Actions:** [CI E2.7 #45213393180](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45213393180) aprovou **178/178 testes**, verificação do CLI, guarda dos motores públicos e ausência de WAV/ZIP no diff. [Regressão principal #45213393059](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45213393059) acompanha a mesma revisão. A página HTML privada teve sintaxe JavaScript verificada em Node; o navegador Chromium headless do ambiente de trabalho não concluiu o smoke test e por isso **nenhuma homologação gráfica nem Web MIDI em PC/Android é reivindicada**.

## Decisão

A PR #38 permite apenas selecionar WAVs privados no **motor Clássico**, que já continha o backend de amostras. O modelo físico E2.5/PR #37 e o D v1.12.8 NÃO usam as gravações. A comparação gravada serve para o titular escutar diferenças qualitativas e decidir qual origem vale investigar; não demonstra evolução do timbre DSP D.

**Antes de publicar um piano de amostras**: confirmar direitos para uso comercial e redistribuição, criar gravações lícitas completas das 88 teclas, dinâmica real multivelocidade, pedal/release, 32–64 vozes com gerenciamento de memória e benchmark em PC/Android. Não incorporar material do usuário à distribuição sem essa autorização. Preservar A/B/C/Clássico/default C, MIDI, FX e presets e manter 0/7 R-GATEs comerciais fechados.
