# STAGE SYNTH C3X — Relatório técnico da Etapa 10

Data: 23/11/2026 — V10 experimental. Referência acústica pretendida: Yamaha C3X, **parâmetros mecânicos estimados**.

## Implementação

1. **Tecla dinâmica:** ao longo de passos de 0,5 ms a posição da tecla persegue alvos de profundidade. A taxa de descida é proporcional à velocidade MIDI solicitada; a subida usa velocidade separada.
2. **Escapamento:** quando a profundidade ultrapassa o limiar de 82% do curso, o martelo simulado perde o impulso do mecanismo e percorre um intervalo de voo livre. A velocidade na colisão considera arrasto experimental.
3. **Backcheck e rearme:** após o impacto o martelo entra em estado `checked` e só volta a `ready` após liberação suficiente da tecla e intervalo mínimo de rearme; posição e tempo são considerados conjuntamente.
4. **Dupla repetição:** limiar de rearme de 54% do curso; para o modo comparativo de repetição simples, 13%. **Esses valores são hipóteses, não especificações Yamaha.**
5. **Martelo/feltro:** usa a velocidade calculada da colisão, sem arredondar para MIDI, no mesmo integrador não linear de contato da V9. A rigidez dinâmica continua uma estimativa experimental de dependência com a velocidade.
6. **Cordas e corpo:** permanecem o sistema acoplado V9 (mesmas cordas em impactos repetidos, tampo compartilhado, duas polarizações, abafadores e pedal). O algoritmo dry não acrescenta reverberação de ambiente; parte da radiação modal interna é preservada para manter os harmônicos naturais.

A implementação é um sistema por estados e não a geometria exata de toda a ação de um piano de cauda.

## Verificações reproduzíveis

- `medicoes/resultados_testes_v10.txt`: 17 testes próprios V10.
- `medicoes/resultados_regressao_completa.txt`: **123 testes aprovados em 43,7 s** na máquina da execução, incluindo históricos e novos.
- Bypass: `render_sequence_v10_action(..., bypass_continuous=True)` produz saída exatamente igual à V9 nos testes A/B ao nível `float32`.
- Repetição com liberação parcial: **3 impactos** no modo double e **1 impacto** no modo single; a diferenciação ocorre por posição e rearme e não apenas por sobreposição de notas MIDI.
- Tecla que só alcança 50% de profundidade, sem atingir o escapamento, não produz impacto.
- RMS não normalizado do Lá4 para velocidades 25, 55, 85, 115: aproximadamente **0,0704; 0,1312; 0,2112; 0,3081** (unidades digitais de áudio, não pressão acústica calibrada).
- Parciais 2 a 7 do Lá4, no protocolo descrito no CSV: maior diferença de **0,067 dB** entre V9 e V10; medições por outras notas no CSV `medicoes/comparacao_parciais_v9_v10.csv`.
- Auditoria de 88 notas: **88 detecções confiáveis** no critério do analisador, mediana do valor absoluto do erro **0,6165 cent**, máximo **1,651 cent**. Esses erros são relativos à escala temperada configurada no motor, não a uma afinação medida em C3X físico.
- **Ressalva E6:** na janela inicial de 0,10–0,52 s, um modo transitório em cerca de 1291,4 Hz podia ser confundido com a fundamental esperada de 1318,5 Hz. Na janela mais estável da sustentação, o pico dominante próximo da fundamental é identificado corretamente. Não foi alterada a afinação do motor para mascarar o problema. Este modo transitório merece estudo auditivo específico.
- Integridade: WAV V1 e WAV V9 copiados e conferidos por SHA-256, conforme `medicoes/SHA256_referencias_v1_v9.json`.

## Limites da interpretação

1. Não há dados autenticados de escala, massas dos martelos, parâmetros do feltro, escapamento e geometria da ação específicos do Yamaha C3X; não alegar correspondência física exata.
2. A dinâmica das articulações (jack, wippen, alavanca de repetição, molas, backcheck) é aproximada por estados discretos e limiares empíricos.
3. A tecla intermediária é modelada no agendamento da colisão; o abafador ainda é representado com um limite simplificado de liberação e não com contato completo dependente de posição.
4. A síntese e os testes foram executados offline em Linux. Não se verificou estabilidade em buffers de áudio em tempo real, latência de plugin, suporte ASIO ou MIDI no Windows.
5. Preservar a V1 como referência sonora subjetiva; não promover V10 automaticamente sem comparação auditiva.
6. O audio que chega ao ouvido ainda tem parâmetros acústicos estimados. Verificar notas em registro alto especialmente E6 antes de considerar a calibração final.

## Referências técnicas consultadas

- Goebl, Bresin e Galembo: *Touch and temporal behavior of grand piano actions*, JASA 2005. https://pubmed.ncbi.nlm.nih.gov/16158669/
- Chabassier, Chaigne e Joly: *Time-domain simulation of a piano*, ESAIM 2014. https://www.numdam.org/item/M2AN_2014__48_5_1241_0/
- Multibody-Based Piano Action: Validation of a Haptic Key, Machines (2020). https://www.mdpi.com/2075-1702/8/4/76
- Physical piano hammer modeling: https://pubmed.ncbi.nlm.nih.gov/10790050/

O motor usa essas referências como fundamentação do tipo de fenômeno estudado, não como fonte de medidas exatas do C3X.
