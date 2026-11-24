# STAGE SYNTH C3X — F1.5 (pesquisa, sem alteração de timbre)

Experimento **espacial hipotético** com quadratura de Rayleigh e teste de não-identificabilidade de pressão isolada, mais ablação audível dos caminhos originais da V10, sem modificar fonte sonora nem dados de C3X. **F1 específica do C3X continua pendente**.

- `radiation_identifiability.py`: equações/efeitos de posição de microfone em superfície fictícia.
- `test_radiation_identifiability.py`: 10 testes matemáticos.
- `diagnostic_v10_output_paths.py`: recompõe caminhos V10 através de `c4_v10_stem_ablation.py`, que já está no repositório na F1.4.
- `test_v10_output_paths.py`: 5 testes offline.
- `F1_5_RESULTADOS.json`: resultados e decisões.
- `audios/`: WAVs de **ablação técnica do próprio V10**, não de novo motor de piano, nem de amostras externas.
- `RELATORIO_F1_5_RADIACAO_IDENTIFICABILIDADE.md`: metodologia, matemática, limites e próximas evidências.

Executar no checkout do projeto com V10 instalada: `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s research/c3x-physical -p 'test_radiation_identifiability.py' -v` e `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s research/c3x-physical -p 'test_v10_output_paths.py' -v`.

A referência C5 é usada somente através de números já arquivados em estudos anteriores; o pacote não distribui nenhum FLAC/PCM de terceiros nem calibra a V10 com fontes de outro instrumento.
