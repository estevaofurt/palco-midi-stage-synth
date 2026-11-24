# STAGE SYNTH — Etapa 11B: primeiro processamento contínuo em blocos

**Pesquisa isolada. Não é a V10 portada, não é motor Yamaha C3X calibrado e não substitui a prévia web V8.**

A Etapa 11A já inclui `midi-block-scheduler.mjs`, um escalonador de referência que retorna eventos por bloco e aloca arrays. A Etapa 11B acrescenta:

- `rt-midi-ring.mjs`: fila de capacidade fixa com `Float64Array`/`Uint8Array`, eventos em ordem cronológica, tratamento explícito de overflow e escrita direta em buffers `Float32Array` fornecidos pelo chamador. **Não há alocações explícitas na função de processamento por amostra**, mas isso NÃO comprova comportamento real-time seguro, ausência de GC, nem uso multithread; a fila **não é thread-safe**.
- `modal-continuity-probe.mjs`: demonstrador de *cordas modais amortecidas* com `q/v` preservados entre chamadas, golpes que acrescentam energia sem apagar a corda, pedal de sustentação contínuo e decaimento. A fonte sonora é inteiramente sintetizada. Esta é uma **sonda de integração**, sem o martelo não linear V10, ponte/tampo bidirecional, 88 escalas físicas calibradas, duas polarizações ou modelagem completa de abafadores. Os parâmetros são artificiais, não medidos do C3X.
- `rt-modal-continuity.test.mjs`: teste de equivalência **exata**, amostra a amostra, para 64/128/256 frames; MIDI nas fronteiras, pedal, meio-pedal, repetição sobre cordas vibrantes, erros e capacidade fixa.
- `demo-stage11b.mjs`: gera um WAV offline de diagnóstico; **não utilizar como WAV de referência sonora do STAGE SYNTH**.

## Executar

```bash
node --test research/c3x-v10-port/midi-block-scheduler.test.mjs research/c3x-v10-port/rt-modal-continuity.test.mjs
node research/c3x-v10-port/demo-stage11b.mjs /tmp/V11B_modal_probe_DIAGNOSTICO.wav
```

Compatibilidade de 44,1 e 48 kHz está testada na sonda. Nenhum arquivo Python ou fonte da aplicação publicada foi modificado nesta etapa.

## Etapa 11C: paridade da escala V10

O módulo `c3x-scale-v10.mjs` replica a fórmula da escala estimada de `stage_synth_c3x/parameters.py` da V10: comprimento vibrante, tensão, densidade, B de inarmonicidade, número de cordas, posição de impacto e parâmetros do martelo. Um *fixture* congelado (`v10-scale-python-reference.json`) gerado a partir do Python original permite validar numericamente **88/88 notas** sem mudar o áudio. O teste `c3x-scale-v10.test.mjs` cobre os dados de todas as notas e as descontinuidades estimadas da ponte. Todos esses valores continuam sendo hipóteses, não dados de fábrica.

```bash
node --test research/c3x-v10-port/*.test.mjs
```

## Próximo trabalho técnico (Etapa 11D)

1. Substituir o `ModalContinuityProbe` por um **port real** da integração das cordas, martelos e tampo V10, com estados pré-alocados, sem zerar osciladores entre blocos.
2. Manter separadas as etapas de integração mecânica e radiativa e comparar sinais offline V10 × blocos na mesma sequência. Não tratar a sonoridade da sonda como benchmark de qualidade.
3. Revisar integridade numérica, limites de energia, compensação de afinação, critérios de desativação de vozes e pedal nas fronteiras.
4. Mover o processamento para um AudioWorklet isolado, medir latência, GC, CPU, underruns e compatibilidade em Windows/Android com hardware real.
5. Preservar a referência sonora aprovada V1 e os arquivos de calibração, e deixar reverberação somente nos efeitos opcionais desligados por padrão.

**Estado:** prova de arquitetura e continuidade numérica em JS/Node. Não é instrumento pronto para performance.