# Proteção de 88 teclas — motor D v1.12.8

Data: 23/11/2026. Base: `main` no commit `626f5089aad95d22b63283b2b6babbfc8f7f17ad`.

## Objetivo e escopo
A v1.12.8 já está integrada **experimentalmente** ao mesmo seletor D do Piano Acústico. Antes de qualquer mudança na interação corda/ponte/tampo, ampliamos a proteção de regressão de uma amostra de teclas para o teclado completo A0–C8 (MIDI 21–108).

O teste `tests/piano_d_full_keyboard_regression.test.mjs` renderiza oito blocos de 128 amostras em 48 kHz, por tecla e perfil `eco`/`balanced`/`studio` (264 cenários), e compara a saída estéreo Float32 da implementação D atual com o arquivo congelado D v1.12.7. Exige PCM idêntico fora de F1–C2 (MIDI 29–36), diferença dentro da faixa intencional, e ausência de NaN/Infinity.

## Evidências e limites
O arquivo de teste passou na verificação local de sintaxe `node --check`; os 264 cenários e o pacote completo do projeto **dependem de execução pelo CI do repositório**. Não afirmar que o teste passou integralmente antes de verificar o resultado do workflow.

Este teste verifica somente o primeiro trecho sonoro (aprox. 21,3 ms): **não** cobre cauda, pedal, número real de vozes simultâneas, desempenho real-time, nem qualidade acústica. Manter as suites existentes, e posteriormente fazer testes de maior duração, pedal e escuta em hardware.

Nenhum motor DSP, menu, preset, MIDI, FX, versão, áudio de terceiros ou página histórica é modificado nesta etapa. A/B/C/Clássico preservados; padrão C. Os tetos de 32/48/64 vozes não equivalem à homologação real em PC/Android. **R-GATEs 0/7**.

## Decisão
Não integrar modelos de madeira aditivos reprovados. Próxima evolução acústica deve ser isolada em pesquisa de acoplamento recíproco passivo e radiação calibrada, com holdout acústico, teste auditivo e CPU de AudioWorklet real antes da promoção do motor.
