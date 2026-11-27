# Reprodução exata do checkpoint regional de 250 ms

O controle realizado em 27 de novembro de 2026 reproduziu **os dez NPY históricos e o NPZ de pressão** pelo SHA-256. A auditoria física original passou nas cinco janelas até 250 ms e na pressão completa. Foram 96.000 passos por caso, 192.000 passos para os dois casos com SciPy 1.17.0, à taxa de 384 kHz.

| Controle | SciPy 1.15.3 | SciPy 1.17.0 |
|---|---:|---:|
| Sinais brutos de 18 ms no passo 1.200 | 0/5 | 5/5 |
| Sinais brutos de 18 ms no passo 3.200 | 0/5 | 5/5 |
| Sinais brutos de 18 ms no passo 6.912 | 0/5 | 5/5 |
| Arquivos NPY históricos de 250 ms | 0/10 | 10/10 |
| NPZ histórico de pressão de 250 ms | — | Igual pelo SHA-256 |

Com SciPy 1.15.3, a repetição de 18 ms foi bit a bit no mesmo ambiente. Os dois ensaios independentes de 250 ms também coincidiram bit a bit com os prefixos de 250 ms extraídos dos ensaios de 500 ms dessa configuração. Os dez arquivos escritos diretamente a 250 ms coincidiram ainda com os dez SHA-256 calculados pelo verificador a partir dos prefixos de 500 ms. Portanto, a diferença histórica observada independe da extensão da janela e da reconstrução dos cabeçalhos NPY. Os controles com OpenBLAS Haswell, Sandybridge e AVX-512 desativado no NumPy, feitos com SciPy 1.15.3, também divergiram da referência de 18 ms.

A alteração controlada de SciPy 1.15.3 para 1.17.0, com os demais pacotes fixados, foi suficiente para reproduzir os resultados históricos. O experimento identifica a distribuição de SciPy como fator de reprodução nessa configuração. A rotina interna responsável pela diferença ainda está em aberto.

## Configuração reproduzida

Linux x86-64 e Python 3.12.14, com NumPy 2.2.6, SciPy 1.17.0, Numba 0.61.2 e llvmlite 0.44.0. Usar `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1` e `NUMBA_NUM_THREADS=2`. O ZIP físico tem SHA-256 `1d279241b7effc9704539c98987efd775eb937c369efcc2d3438354525570192`. A impressão digital das bibliotecas e os SHA-256 individuais estão na evidência da execução.

## Revalidação de 500 ms

A execução de 500 ms publicada em `6326618` foi feita com SciPy 1.15.3. A auditoria física e a retomada passaram nessa execução. O critério histórico reprovou. Para reavaliar o resultado completo, executar `private_run_500ms.py` do checkpoint `19fb367` em diretório novo, com a configuração reproduzida acima e pelo menos 12 GiB livres no volume de trabalho. A reprodução de 250 ms preserva a referência histórica. A aceitação em 500 ms depende dos resultados da nova execução dos três casos.
