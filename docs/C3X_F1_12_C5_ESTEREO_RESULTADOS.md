# STAGE SYNTH — F1.12 | Influência de canal e janela nos harmônicos do Yamaha C5

**24/11/2026. Pesquisa complementar; F1 C3X permanece PENDENTE.** O objetivo não é acrescentar uma nova versão sonora, mas verificar a robustez dos dados da referência C5 antes de inferir mudanças na V10. Esta pesquisa dá continuidade às etapas até F1.11, preservadas integralmente.

## Evidência e proveniência

- Três gravações **isoladas de Dó4**, Yamaha **C5** Salamander Grand Piano V3, Alexander Holm, **CC BY 3.0**; microfones AKG C414 em arranjo AB a cerca de 12 cm sobre as cordas. **Não são C3X**. Originais FLAC obtidos no GitHub Actions, SHA-256 conferidos e descartados após cálculo. Sem samples incorporados no sintetizador.
- [GitHub Actions F1.12](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45377592874): **11/11 testes aprovados e 3/3 hashes verificados**, coleta e análise concluídas.
- Método: f1/B previamente estimados da própria referência C5 servem apenas como previsão da frequência central do 4º/5º parcial. FFT Hann x8, busca em **±8 Hz**, exigindo contraste local ≥6 dB. São três inícios × três durações nas fases ataque/corpo/cauda e canais L/R/mono. **243 observações de janelas**, todas aceitas.

## Resultado principal — mediana H5/H4 em dB

| Camada | Região temporal | Esquerdo | Direito | Mono | Diferença L/R |
|---|---|---:|---:|---:|---:|
| v1 | Ataque | -3.25 | -8.56 | -1.65 | 5.31 |
| v1 | Corpo | +1.69 | -2.58 | -7.43 | 4.27 |
| v1 | Cauda | +8.99 | -10.94 | -8.44 | 19.93 |
| v8 | Ataque | +1.06 | -5.45 | +1.85 | 6.51 |
| v8 | Corpo | +2.42 | -0.96 | -1.63 | 3.38 |
| v8 | Cauda | +14.60 | -7.17 | -2.78 | 21.77 |
| v16 | Ataque | +2.43 | -4.59 | +2.87 | 7.02 |
| v16 | Corpo | +2.83 | -0.87 | +1.11 | 3.70 |
| v16 | Cauda | +18.29 | -5.21 | -0.92 | 23.50 |

Valores são **20 log10(amplitude H5 / amplitude H4)** de sinais captados por microfone, não pressão absoluta ou força do martelo. Nove configurações de janela por entrada da tabela; o detalhamento está no artefato numérico do CI.

## Interpretação e limites físicos

1. Na camada média **v8**, o H5/H4 muda **+14,60 dB (L)** para **−7,17 dB (R)** na cauda: diferença observada de **21,77 dB**. Camada forte v16: diferença **23,50 dB**. Isto pode refletir a combinação de posição dos microfones, fase, propagação, batimentos e modo de vibração; **não permite identificar a causa única**.
2. Converter L/R para mono não preserva a energia por parcial: a fase relativa pode atenuar ou reforçar picos. Assim, as comparações anteriores em mono descrevem somente uma das projeções da gravação. Elas não são falsas, mas têm **domínio de validade limitado**.
3. H5/H4 não é uma propriedade invariável da tecla: varia no tempo, além de variar entre camadas de intensidade e microfones. Os percentis 10–90 computados são uma **análise de sensibilidade à janela**, não intervalos de confiança estatísticos nem replicações independentes.
4. O diagnóstico F1.4 da **V10** continua válido no seu próprio sistema: a IR sintética cancela H5 e destaca H4. Mas **não é justificável ajustar os filtros da V10 por um único espectro mono do C5**, e o C5 não determina a radiação física do C3X.
5. A fórmula f_n = n·f1·sqrt[(1+B n²)/(1+B)] define a guarda de pico; o f1/B de entrada foram ajustados a gravações C5 de outro ensaio. Os mesmos dados foram usados para centrar a busca, de modo que este protocolo **não é validação externa independente** da afinação/rigidez.

## Decisão operacional e critérios de avanço

- **V10 original, motor web, UI e presets permanecem inalterados.** F1 C3X continua PENDENTE; F2–F13 não recebem aprovação.
- Não copiar B ou espectro H4/H5 do C5 para parâmetros físicos do C3X; novas hipóteses sobre o corpo devem preservar a topologia física e ser avaliadas contra várias posições/tempos, preferencialmente com medições independentes.
- Para fechar F1 específica: ainda faltam exemplar C3X identificado, escala da corda C4, força/velocidade de ponte sincronizadas com pressão e/ou mapa de radiação, incerteza instrumental e direitos comerciais.
- Próxima decisão cabe à rota do projeto: manter a identificação C3X em espera de dados ou autorizar explicitamente um **modelo de piano de cauda genérico de pesquisa** com metas de realismo sem alegar réplica validada da Yamaha. Isso não ocorre automaticamente pela pesquisa presente.

**Fontes:** [Salamander](https://sfzinstruments.github.io/pianos/salamander/) · [Relatório F1.5](C3X_F1_5_RADIACAO_IDENTIFICABILIDADE_E_ABLACAO.md) · [Decisão F1.11](C3X_F1_11_FONTES_EXTERNAS_E_DECISAO_REFERENCIA.md).
