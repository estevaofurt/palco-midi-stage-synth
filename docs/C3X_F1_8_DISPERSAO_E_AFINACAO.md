# F1.8 — separação entre afinação e dispersão de corda (24/11/2026)

**F1 PENDENTE.** Continuação de F1.7 (base 9a5406bbab4400074c5f45e6134de1c26dc16fb6). Não altera o motor, não constitui fase F3 concluída, não usa PCM externo nem publica V11. C5 é referência comparativa, NÃO C3X medido.

## Auditoria do código original
- V10 `parameters.py` (blob b23c89225c1ed0d1ad7e1a2ecd9976fe29d82339): B estimado por pi³ E d⁴/(64 T L²). C4 B bruto=0,0005284491799769235.
- `tuning.py` (blob 88ca68af75eb1abb847d8c32da0e36409137aefb): afinação equal corrige T por 1-B e B por B/(1-B), preservando T*B; B corrigido=0,0005287285861647126. Frequências teóricas f_n=n*f1*sqrt((1+B*n²)/(1+B)). Não confundir B bruto com o B após ajuste de tensão, nem estas frequências com picos efetivamente renderizados.
- `shared_mechanics.py` usa tune_note ao montar o banco. Nenhum arquivo V10 modificado.
- Dados C5: Alexander Holm, Salamander Grand Piano v3, CC BY 3.0, https://github.com/sfzinstruments/SalamanderGrandPiano commit 3382bf9496bba2486f5ab0de55a264d1dfc38404. Usados picos arquivados em C5_C4_verified_numeric_report.json (blob 63e893d8cfff79c247c0ea76b944885669a8249f), aquisição original verificada no CI https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45313270498. Sem nova aquisição ou FFT.

## Método
Manter f1 fixo e variar B separa o efeito dispersivo do simples fator de afinação. No teste de previsão, aplicar os mesmos filtros a ambos modelos (contraste >=20 dB e nível relativo >=-60 dB). Ajustar B livre por regressão linear F1.7 com parciais 2–8 e ajustar f1 de ambos modelos pela média logarítmica das razões f_observado/f_n(f1=1,B), minimizando erro quadrático em cents no treino. Comparar contra B fixo corrigido da V10, com f1 livre. Reservar n=9–12 para teste; não usar suas frequências na estimação. Critério de triagem, não gate físico: erro RMS em cents nos parciais reservados. Excluir v1 corpo por ausência de pico reservado elegível (não reduzir limiar para forçar resultado). Dados de mesma janela e gravação não são amostras independentes; holdout por parcial é teste interno de extrapolação, não validação externa de C3X.

## Resultados

| Camada/janela | N reservado | B fixo, RMS cents | B livre, RMS cents |
|---|---:|---:|---:|
| v1 ataque | 2 | 17,848 | 0,336 |
| v1 cauda | 2 | 19,954 | 1,577 |
| v8 ataque | 4 | 16,478 | 1,229 |
| v8 corpo | 4 | 17,073 | 0,872 |
| v8 cauda | 4 | 16,501 | 0,731 |
| v16 ataque | 4 | 16,371 | 1,538 |
| v16 corpo | 4 | 16,906 | 0,605 |
| v16 cauda | 4 | 16,686 | 0,567 |

28 picos reservados, 8/8 janelas melhoram; RMS agrupado 17,012224 -> 1,011155 cents (94,06% de redução do erro de frequência, não de timbre). Uma janela excluída. Os modelos são equações estáticas de parciais, não renderizações.
Mediana B dos nove ajustes de treino=0,00029561290712381465. Mesmo f1 nominal 261,6255653 Hz, delta V10 vs mediana C5: n1 0; n2 0,182703; n4 1,822541; n5 3,638387; n8 15,161175; n12 50,811740; n16 118,268973 Hz. n16 é extrapolação teórica fora dos dados testados, não medida. O ajuste de f1 com B fixo desvia f1 para baixo e não corrige os parciais altos. B pode influenciar caráter metálico, mas ganho perceptivo não demonstrado; amplitudes, envelopes, modos, batimentos e radiação não são identificados por este cálculo. Diferença entre pianos distintos não prova erro físico do C3X.

## Testes e próximos passos
15/15 verificações executadas em ambiente JavaScript V8 com função F1.7 recuperada diretamente do GitHub e números arquivados. Testes de invariância da fundamental, corda ideal, rigidez, escala de afinação, ajuste, rejeições, separação treino/teste, exclusão explícita, correção de B e contagem dos 28 picos. Sem CI novo/hardware. Reproduzir:
`node research/c3x-physical/c5-dispersion-holdout.test.mjs`

Commits fbd65551b7fb25bbebef7719c3c78239578f3092 e c5e42326aa5dfd7946ab724b1ce507ea31580ff3.
**Decisão:** preservar V10. Não copiar B do C5 para C3X, não alterar afinação do produto nem aprovar F1/F3. Próximo F1.9: auditar consistência da escala estimada do Dó4 entre diâmetro, densidade linear, tensão, comprimento, módulo de Young e B; quantificar possíveis famílias de parâmetros compatíveis, não identificar um C3X por pressão isolada. Buscar evidência física independente antes de promover. Meta 32–64 vozes intacta, hardware não homologado.
