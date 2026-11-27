# G3 — Enriquecimento temporal de 369 portas

Continuação de G3_Observadores_369. 55 entradas verificadas (5 insumos + 20 acoplamento + 18 referência fina + 12 observadores). 127.825 estados, 80 fluxos superiores prescritos em d3, 289 inferiores, 48/384 kHz. Q6 contém Q3; projeção por congruência, LU da submatriz inferior ativa. Sem alteração de polos ou amortecimento. Janela de 64 intervalos (512 subpassos, 1,333 ms), somente lags alcançáveis. Seleção fixa de 144 direções pelo maior resíduo quadrático fino d3 nos primeiros 16 blocos do ruído arquivado (98,2352% da norma quadrática desse trecho). Ruído arquivado não é independente da seleção. Novo ruído independente, seed 271131, normal nos coeficientes superiores d3, amplitude 0,1; referência d8 recalculada causalmente com 289 incógnitas por subpasso.

9 ensaios projetados novos (misto/d6 em quatro casos cada, d3 em um) e uma referência d8. Seis ensaios iniciais repetidos na execução final. Máximos dos 9 casos: energia 1,509605e-16, trabalho 6,325202e-16, continuidade ativa 2,722500e-15; nenhum mínimo acumulado negativo. Referência d8 independente: continuidade fina 2,214442e-14, energia 1,238088e-17, trabalho por prefixo fino 9,528036e-16.

| Caso | Pressão projetada d3 % | Mista % | d6 % |
|---|---:|---:|---:|
| Ruído arquivado | 1,027642 | 0,233976 | 0,067825 |
| Pulso | 0,001012 | 0,000193 | 0,000055 |
| Alta | 0,048411 | 0,010754 | 0,002938 |
| Ruído independente | 1,215957 | 0,230758 | 0,075245 |

Ruído independente: pressão fina combinada 3,783489/0,931393/0,821930%; pior receptor fino 4,242757/1,093189/0,986052%; pior receptor projetado 1,761516/0,295560/0,098481% (d3/misto/d6). Fluxo inferior 6,853969/2,235182/1,906405%; carga superior projetada 0,164383/0,036207/0,031720%. Incógnitas 867/1299/1734, condição 1,122856/1,148022/1,149286. Misto executa internamente d6, portanto a economia de incógnitas não demonstra ganho computacional. Pressão por convolução com observadores recuperados, fluxo zero depois da janela; não é cauda livre nem avaliação audível. Continuidade fina dos modelos projetados não medida. D6 passa o critério exploratório de 1% de pressão individual nos casos testados, misto falha fino no novo ruído, d3 falha em ruído. Não aprovação geral.

Decisão: d6 candidato de precisão para transientes; misto alternativa de custo potencial; d3 baseline; d8 referência. Validar janelas longas, novas excitações, continuidade fina e otimizar implementação espacial mista. 12 dependências de regeneração pendentes, sem integração mecânica, benchmark controlado, render ou promoção. Parâmetros definidos nesta etapa.

Reprodução no pacote G3_Enriquecimento_369.zip (25 entradas no SHA256SUMS), Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Numba 0.65.1, uma thread. Verificar manifestos antes de executar. Comando:
```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python enrich.py /raiz/restaurada /pasta/G3_Acoplamento_369 /pasta/G3_Referencia_Fina_369 /pasta/G3_Observadores_369
```
Este commit registra relatório e hashes dos arquivos locais. Pacote completo, scripts e sinais binários continuam no ZIP local.
