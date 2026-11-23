# Stage Synth — E1.1: preparação da medição ponte → pressão (somente laboratório)

**Data:** 23/11/2026. **Base pública congelada:** Stage Synth v1.12.7 (`main` após PR #28, `b49d9ab`). **Não existe novo timbre, versão v1.12.8, motor integrado ou calibração de Yamaha/Steinway.**

## Qual lacuna estamos atacando?

O solver passivo compartilhado foi verificado contra uma solução independente, mas devolve `boardVelocity` em unidade **generalizada e não calibrada**. Nenhum teste permite convertê-la diretamente em pressão sonora no ouvido. O estimador offline `research/bridge-radiation-h1.mjs` é um instrumento original de **metrologia simulada e futura análise de sensores**: receberia aceleração medida da ponte em **m/s²** e pressão de microfone em **Pa**, com amostras simultâneas no mesmo relógio, para estimar a transferência complexa `H_pa(f) = S_pa(f) / S_aa(f)` de unidade **Pa/(m/s²)**. O resultado é um **sistema observado** por posição/microfone/condição, não a identificação da massa/rigidez de um piano.

Implementação: estimador H1 por médias de Welch, janela Hann periódica, remoção da média por segmento, transformada radix-2, sobreposição configurável. A coerência `gamma²=|S_pa|²/(S_aa*S_pp)` é diagnosticada por frequência; bins com baixa excitação/coerência, DC e Nyquist são marcados inválidos, com `magnitude=null` e `phaseRadians=null`. O coeficiente de confiabilidade não comprova calibração, licenças nem um modelo mecânico único. Frequência resolvida pela janela `f_s/N`, sem alegações de resolução temporal de impacto com uma FFT longa.

**ATENÇÃO:** `H_pa` NÃO é mobilidade `Y_ponte=velocidade_ponte/força_ponte`, NEM força tecla→ponte, NEM um campo acústico completo (outros pontos do tampo/aro e sala também irradiam). Em eventos com múltiplas fontes, vibração de ponte e pressão podem não formar um sistema SISO justificável. A interpretação depende da geometria de sensores e da excitação instrumentada. Para o produto comercial, a medição real exige um piano identificado, autorização comercial de dados, proveniência, posição dos microfones e acelerômetros, calibração, relógio comum, delay dos canais, SNR/coerência e notas/dinâmicas para **validação fora das sessões de ajuste**.

## Testes sintéticos E1.1 (nenhuma gravação de terceiros)

1. Recuperar ganho complexo e fase de filtro FIR causal conhecido `.65*z^-3 - .2*z^-4` para **44,1/48/96 kHz**.
2. Rejeitar pressão independente de aceleração e diminuir confiabilidade perante ruído de saída.
3. Recusar entradas de tamanhos distintos, valores não finitos, silêncio e parâmetros FFT inválidos.
4. Verificar que multiplicar por 2,5 a calibração de pressão multiplica `|H|` por 2,5 sem mudar fase.
5. Testar dados **fora do ajuste** (sem reutilizar a mesma semente de excitação sintética).
6. Evidenciar risco: adicionar 9 amostras de atraso apenas ao canal de pressão muda a **fase**, apesar de a coerência continuar elevada. Logo, coerência alta nunca substitui sincronização instrumentada.

Os testes são **somente sintéticos** e a função é destinada a análise offline; não gera/importa WAV, não usa código restrito e não executa em AudioWorklet. O workflow congela explicitamente os motores, UI, MIDI, FX, presets e `package.json` frente ao commit público.

## Próxima decisão

Não migrar para o DSP até a chegada de pelo menos um conjunto de sinais reais `a_ponte(t)` e `p_L/R(t)` com calibração, sincronização e autorização de uso comercial, preferencialmente com excitação controlada e séries independentes de validação. Mesmo esse conjunto **não determina automaticamente** a matriz complexa de mobilidade 2×2, o impacto de feltro ou ressonâncias de todas as partes do corpo. A prioridade permanece o **grave sem caráter de violão**, sem danificar C4–C6; avaliar a contribuição física do caminho de radiação em A/B e escuta cega somente após haver medições.

**Status:** preparo metodológico E1.1; **R-GATEs globais completos: 0/7.** Preservar PR #26 não mesclada, 32 vozes mínimo/64 meta sem homologação no hardware.

### Referências metodológicas e acústicas

- SciPy, método Welch e coerência: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.coherence.html
- MathWorks, estimador de transferência H1 e espectros cruzados: https://www.mathworks.com/help/dsp/ref/dsp.transferfunctionestimator-system-object.html
- Chaigne/Cotte/Viggiano, *Dynamical properties of piano soundboards* (JASA 2013), evidência de acoplamento e radiatividade espacial: https://pubmed.ncbi.nlm.nih.gov/23556610/
- Protocolo Stage: `docs/PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md`; formalização passiva: `docs/PRONTIDAO_PONTE_TAMPO_PASSIVO_V128_2026-11-23.md`.
