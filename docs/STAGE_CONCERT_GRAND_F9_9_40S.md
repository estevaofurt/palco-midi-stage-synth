# F9.9 — 40 segundos, precisão e escuta

Base 50472a5d3035189da00f9d8d24d2fef95a674a04; F9.8 mostrou ganho real em PCM comum de +11,426 dB (A) e +21,410 dB (B) aos 19 s. A aproxima fundamental C5, B aproxima global e P3, mas piora P2. Sem aprovação auditiva. Manter controle e ambos candidatos, tocar C4 a 1 m/s, 40 s contínuos, mesmos parâmetros, 96 kHz mecânico, 48 kHz acústico, sem efeitos/loop/normalização por nota. Não modificar DSP público nem F9.8. 40 s é duração de trajetória, não meta de som audível.

Usar análise pré-PCM em Float64 após soma/filtragem (blocos armazenados Float32 como antes, portanto não afirmar precisão integral Float64), comparar PCM16 efetivo, erro de quantização, fração zero, RMS e contraste dos 10 parciais. Fade de 40 ms excluído das análises. Acrescentar WAV estéreo PCM24 com exatamente mesmo ganho e fade, sem dither, sem boost, gate de clipping e igualdade do pico com exportador F8. PCM24 melhora resolução, não sustain físico. 8/8 testes PCM24 executados no V8 contra exportador F8 recuperado do GitHub; 8 testes auditoria V8 prévios. CI Node e três renders longos ainda pendentes no commit. Análise global -20/-40/-60 dB é relativa à primeira janela, não RT60 nem percepção; C5 original limitado a 12–16 s, sem comparação direta aos 30–40 s.

Após resultados: comparar dinâmica em velocidades .5/1/2.5 m/s, sem rotular pp/ff reais sem calibração; verificar headroom comum antes de exportar fortes. Investigar discrepância P2 por mobilidade/impedância e perdas dependentes de frequência, sem EQ arbitrário. Não ampliar a F10 antes da validação do Dó4. Pedal e ressonância simpática não modelados, polifonia e V10 pendentes, main preservada.

## Atualização de validação e escuta

Feedback positivo de sustentação F98-both-half-20s registrado em docs/STAGE_CONCERT_GRAND_F9_8_STRING_LOSS.md. B passa a ser candidato prioritário de pesquisa, não homologado. Preservar A e controle como comparadores. CI [45415259799](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45415259799): 67 testes Node aprovados no job smoke (F9.9 PCM24 tests passed: 8; Precision audit tests passed: 8; F9.8 tests passed: 9; F9.7 tests passed: 8; F9.6 tests passed: 9; F9.5 tests passed: 13; F9.3 tests passed: 12). Estado observado: render (both-half): in_progress; render (horizontal-half): in_progress; render (control): in_progress; smoke: success. Não alegar resultado de 40 s sem leitura dos logs e verificação dos artefatos. Nenhuma mudança física ou DSP adicional neste registro.

## Candidato B de 40 s confirmado

CI 45415259799, artefato 14932760494: 40 blocos, 1920239 frames, zero clipping, pico 0,306769 FS, PCM16/24. Float e PCM16 concordam nas quedas globais -40 13 s e -60 28,5 s, fundamental -60 31 s. Aos 39–39,5 s float -96,389 dBFS (-74,180 dB relativo), PCM16 69,065% zeros e SNR de quantização 4,413 dB. Não inferir audibilidade. Relatório completo do candidato em audio/analysis_f9_9_both_half_ci.json; os outros dois jobs não confirmados nesta leitura. [Áudio B](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45415259799/artifacts/14932760494).

## Matriz completa confirmada

CI [45415259799](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45415259799), quatro jobs concluídos com sucesso. 67 testes Node, 120 blocos contínuos, todos os WAVs de 16/24 bits sem clipping. Maior resíduo de energia 4.34375e-14 J. Análise float e PCM16 concordam nos cruzamentos globais -60 dB dos três casos.

| Caso | Global -60 dB | Fundamental -60 dB | Float aos 39 s (dBFS) | PCM16 zeros aos 39 s |
|---|---:|---:|---:|---:|
| control | 15.5 s | 16.5 s | -140.80 | 100.00% |
| horizontal-half | 20 s | 22 s | -117.18 | 100.00% |
| both-half | 28.5 s | 31 s | -96.39 | 69.06% |

Artefatos: [controle](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45415259799/artifacts/14931568743), [A](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45415259799/artifacts/14933170303), [B](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45415259799/artifacts/14932760494). B permanece candidato prioritário pela melhora percebida no F9.8 de 20 s. Não afirmar audibilidade aos 40 s nem validação perceptiva do novo áudio. P2, dinâmica, pedal, outras notas e integração pendentes. Não alterar física neste registro. Relatórios separados em audio/analysis_f9_9_control_ci.json, audio/analysis_f9_9_horizontal_half_ci.json, audio/analysis_f9_9_both_half_ci.json.

## Retorno auditivo — 24/11/2026

Titular: "nao ouço nada apos 14s". Contexto imediato: demonstração F99-both-half-40s. Não se sabe qual resolução foi ouvida, ganho de reprodução ou ruído ambiente. Na janela 14–14,5 s, float RMS 0,00065187585 FS (-63,717 dBFS), queda de 41,507 dB relativamente à primeira janela; SNR de quantização PCM16 37,369 dB e apenas 1,202% amostras zero. Não é falta de resolução PCM16 nessa janela; PCM24 não garante audibilidade. Quedas físicas -60 dB de 28,5 s (global) e 31 s (P1) não equivalem ao sustain percebido. F9 não homologada. Tratar -41,5 dB relativo ao RMS inicial de B como nível de comparação experimental em ganho comum, não limiar auditivo universal. Preservar B e comparar níveis absolutos e relativos em dinâmica F9.10; corrigir ganho de protocolo se comparar FS (0,1 vs 0,3676702344). Testar candidatos com cauda mais musical, sem boost artificial ou reduzir perdas indiscriminadamente. Investigar acoplamentos e ressonância simpática/pedal, que ainda não estão implementados; comparar C5 somente nos trechos disponíveis e condições compatíveis. Main intacta.
