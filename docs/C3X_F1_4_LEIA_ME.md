# Pesquisa F1.4 — por que a V10 atenua o 5º harmônico do Dó4?

Esta entrega contém **somente código de auditoria, métricas e testes**, sem modificar a V10 nem incorporar samples. As gravações C5 foram verificadas em CI anterior e usadas somente como métricas numéricas de referência. Não equivale à calibração do Yamaha C3X nem à conclusão F1.

- `RELATORIO_F1_4_DIAGNOSTICO_H4_H5.md`: conclusão física e correção da confusão do pico lateral de 1291 Hz.
- `c4_v10_stem_ablation.py`: recria o sinal original em canais `direct`, `body`, `board`, verifica equivalência e estima o filtro analítico.
- `test_c4_v10_stem_ablation.py`: 17 testes locais.
- `F1_4_V10_STEM_RESULTS.json`: medições em três velocidades e três janelas.
- `F1_4_HARMONICOS_C4.csv`: resumo para inspeção rápida.
- `testes_f1_4.log`: registro da execução local.

**Uso:** `python -m pip install -r ../Stage_Synth_C3X_Etapa_10/requirements.txt` e executar os comandos descritos no relatório com `--v10-root` apontando para a V10 original.
