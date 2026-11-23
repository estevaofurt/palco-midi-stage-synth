# Stage D v1.12.9 — candidato isolado de polarizações F1–C2 (23/11/2026)

## Problema e hipótese
A v1.12.8 pública modificou duas vias de uníssono em F1–C2, com ganho limitado de ataque e piora registrada da cauda em C2 mf. A escuta do titular já reprovou alterações quase imperceptíveis no martelo da v1.12.7. Não repetir ruídos artificiais de madeira da PR #26.

Este protótipo testa **quatro modos por parcial** (duas cordas × duas polarizações) apenas nos **dois primeiros parciais** de MIDI 29–36, com frequências ligeiramente distintas, amortecimentos diferentes e pesos com soma nominal 1, mantendo os demais modos do motor D v1.12.8. São coeficientes fenomenológicos, **não medições de corda, ponte, madeira, mobilidade ou pressão acústica**. A estrutura de corpo ainda é aditiva, não há alegação de acoplamento recíproco calibrado. É um experimento para escuta, não uma melhoria comprovada.

## Controle da experiência
- Candidato em `physical-piano-hybrid-v129-candidate.mjs`; o motor público `physical-piano-hybrid.js` **não muda**.
- Teste `tests/piano_d_v129_candidate.test.mjs`: 88 teclas × 3 perfis e testes 32/48/64 notas, pedal e valores finitos. O teste cobre somente a identidade de PCM inicial e um estresse breve em Node; não certifica real-time.
- WAV gerado pelo **próprio motor** e pelo script `scripts/render_piano_d_v129_polarization_wav.mjs`: D v1.12.8 atual versus D v1.12.9 candidato, C2 pp/mf/ff, F1/A1, C3/C4 de controle e acorde, estéreo 48 kHz PCM24. Não há piano amostrado ou fonte externa no resultado. Mesmo ganho para ambos, sem FX ou normalização individual.
- Workflow `.github/workflows/stage-d-v129-candidate-wav.yml` executa regressão geral, valida arquivos e publica artefato ZIP de WAV no GitHub Actions.

## Gates e decisão
Somente promover o D candidato depois de CI integral aprovado, escuta real demonstrando diferença útil de caráter de piano nos graves e análise de cauda versus dados originais com direito de uso, em notas independentes das de ajuste. Mesmo CI verde não implica bom timbre. Preservar A/B/C/Clássico/default C, MIDI, CC64, FX, UI, presets, arquivos congelados 1.12.6/1.12.7 e v1.12.8 público. Não renomear este candidato como integração comercial.

**Polifonia de 32–64 notas é teto de alocação** até perfil real de AudioWorklet em PC/Android, e **R-GATEs 0/7** permanecem.

## Resultado efetivamente executado (GitHub Actions 45190018443)
- Workflow completo **verde**: regressão Stage, testes D129, renderização e verificação de três arquivos WAV 48 kHz PCM24 estéreo. [Run e WAV ZIP](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45190018443).
- C2 mf: diferença de RMS D129/D128 no **primeiro 0–12ms = 0,000 dB**, corpo 100–220ms **+0,012 dB**, cauda 900–1300ms **+0,182 dB**. C2 pp apresenta **+0,955 dB na cauda**, mas não foi aferida melhoria de fidelidade versus piano real.
- F1 mf: corpo **+0,014 dB**, cauda **+0,183 dB**. A1 mf: corpo **+0,013 dB**, cauda **+0,178 dB**. C3/C4 PCM estritamente idênticos. Acorde: cauda **+0,059 dB**.
- Todos os pares em F1–C2 tiveram diferenças PCM, porém a amplitude das métricas é pequena e **não demonstra diferença perceptível**, quanto menos realismo. A tentativa não resolveu comprovadamente a ausência de sensação de madeira ou o caráter de violão no grave.
- **Decisão pós-CI: manter a PR DRAFT, NÃO promover v1.12.9 ao aplicativo.** Prosseguir com modelagem de transmissão física corda↔ponte↔tampo e calibração de radiação, em vez de iterar novas divisões quase indistinguíveis de uníssono.

