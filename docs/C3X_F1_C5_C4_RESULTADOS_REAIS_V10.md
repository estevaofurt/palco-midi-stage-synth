# STAGE SYNTH — F1, estudo C5/Dó4 × protótipo V10

**Status científico:** pesquisa comparativa com gravações reais **Yamaha C5**; **NÃO** identificação de parâmetros **Yamaha C3X**. F1 C3X pendente e R-GATEs não automaticamente homologados. **Nenhum sample do C5 é utilizado como fonte de som no motor físico V10.**

## Evidências originais verificadas

A execução do [GitHub Actions #45313270498](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45313270498) baixou e verificou por tamanho e SHA-256 os arquivos `C4v1.flac`, `C4v8.flac` e `C4v16.flac` de Alexander Holm, Salamander Grand Piano V3 (piano Yamaha C5, licença **CC BY 3.0**). O analisador conferiu 48 kHz estéreo e extraiu somente métricas; todos os arquivos originais foram excluídos do runner após o cálculo. Os testes sintéticos do pipeline passaram.

As camadas **v1/v8/v16** são etiquetas do conjunto de samples, **não** velocidades medidas do martelo. Os microfones AKG C414 situavam-se aproximadamente 12 cm acima das cordas; não há medições instrumentadas de força, deslocamento do tampo ou funções de radiação. A comparação não quantifica fidelidade ao C3X real.

## Comparação espectral concreta — Dó4 (MIDI 60)

| Gravação original do Yamaha C5 | f1 estimado (Hz) | B estimado (adimensional) |
|---|---:|---:|
| C4v1 — suave | 261,56041 | 0,000281251 |
| C4v8 — média | 261,54104 | 0,000288287 |
| C4v16 — forte | 261,48562 | 0,000295142 |
| V10 Python simulada, intensidade intermediária | 261,69306 | 0,000521446 |

Os ajustes do C5 indicam *B* aproximadamente 0,00028–0,00030, contra 0,00052 estimado na V10. A diferença é suficientemente grande para orientar um estudo de rigidez/dispersão, **mas não autoriza copiar o valor do C5 para um C3X**. Pequenas variações de B estimado entre camadas também refletem incerteza experimental, janela espectral e processos físicos; não tratar como identificação de mudança material da corda.

### Parciais mais discrepantes no ataque (35–255 ms após o início)

| Parcial | C5 médio C4v8 (dB relativo à fundamental) | V10 MIDI 75 (dB relativo) | Diferença C5 − V10 |
|---|---:|---:|---:|
| 2º | +3,18 | +10,74 | −7,56 dB |
| 4º | −16,36 | +0,85 | −17,21 dB |
| 5º | −14,52 | −30,37 | +15,85 dB |
| 7º | −18,68 | −7,96 | −10,72 dB |

No **corpo (260–700 ms)**, o quinto parcial do C5 médio foi medido em **−18,69 dB** e o mesmo parcial da V10 em **−41,42 dB**, diferença de **+22,73 dB**. Isso aponta uma lacuna na trajetória dos parciais e no balanço espectral da saída sintetizada. A causa pode envolver excitação, perdas de corda, interação ponte/tampo, radiação, posição e resposta de microfones: os dados de áudio sozinhos **não identificam qual componente causa a diferença**.

### Alinhamento temporal corrigido

O cálculo final gera V10 com nota pressionada até cerca de 1,765 s e duração de 1,8 s; todas as janelas de avaliação (até 1,4 s após onset) ficam antes da soltura. Compara-se sustentação com sustentação. O primeiro ensaio interno tinha tecla solta antes do fim da janela de cauda, o que poderia exagerar a diferença: **foi corrigido antes de considerar o relatório conclusivo**.

As distâncias médias entre harmônicos 2–8, embora úteis para triagem, também incluem parciais muito fracos e sensíveis à medição. A segunda métrica inclui somente os harmônicos acima de −40 dB **em ambos** os sinais, evitando atribuir muita confiança ao ruído de fundo e a componentes praticamente ausentes.

## Próximas ações corretas

1. **F1/método:** repetir análise em dois instantes e usar prova independente de sensibilidade ao microfone e níveis de ruído, sem inventar propriedades do C3X.
2. **F2–F7:** somente após aprovação das etapas, avaliar numericamente impacto do martelo, cordas, ponte e transferência radiativa; qualquer melhoria de timbre deve ter hipótese física e teste de regressão.
3. **F8–F9:** validar a reconstrução de Dó4 e comparar audição com referências legítimas, sem confundir instrumento C5 com C3X.
4. **Licença:** atribuir claramente Alexander Holm / Salamander Grand Piano V3 / CC BY 3.0. O conjunto não será copiado ao projeto nem usado para sintetizar notas.

**Este estudo não altera o áudio público nem conclui a F1 do Yamaha C3X.**
