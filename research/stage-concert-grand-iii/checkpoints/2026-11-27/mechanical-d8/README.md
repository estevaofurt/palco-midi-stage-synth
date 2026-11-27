# G3 — Referência d8 da interface mecânica
Continuação de a7db87c. Mecânica sintética de oito coordenadas, acústica física arquivada de 369 portas, 127.825 estados. Tampo constante por bloco (d1 embutido). 61 entradas de manifestos verificadas.
Três novos ensaios d8 de 64 blocos cada, ruído/pulso/seno 2 kHz, balanço integrado máximo 9,59132e-15, solução simultânea 1,46508e-15. Nenhum trabalho acumulado exterior negativo. Reutilizados seis ensaios d3/d7 anteriores.
Audit.py resolve separadamente abertura fina de 289 incógnitas por subpasso para o fluxo superior prescrito obtido do circuito d8. Máximos fluxo 3,20666e-15, carga mecânica média 9,12063e-16, continuidade fina 7,64934e-14, energia 9,25880e-17, trabalho 1,37504e-15. Não é segunda resolução mecânica independente.
Observadores b64: 2439 taps, chegadas 559/1679 subpassos, 2950 amostras por convolução de 512 fluxos finos; conferência direta máxima 3,95605e-15. Filtro Kaiser 617 taps, corte 22 kHz, decimação 8.
| Caso | Pior receptor fino d3 % | d7 % | Pior receptor filtrado d3 % | d7 % |
|---|---:|---:|---:|---:|
|Ruído|0,715431|0,108952|0,00401029|0,000350864|
|Pulso|0,258264|0,032058|0,000787650|0,0000392962|
|Seno 2 kHz|0,638929|0,054040|0,00113024|0,000134060|
Aprovação exploratória <1% somente para esta fixture. Janela 1,333 ms precede chegadas de ambos receptores; fluxo zero depois dela, não cauda natural. Sem revogar resultados anteriores, sem render ou aprovação geral.
Reprodução no pacote G3_Interface_Mecanica_D8.zip (25 entradas SHA256SUMS, ZIP verificado). Uma thread BLAS/OMP/Numba, Python 3.13.5, numpy 2.3.5, scipy 1.17.0, numba 0.65.1. Executar verify_bridge.py com --orders 8 --blocks 64, audit.py com raiz restaurada e pastas G3_Acoplamento_369, G3_Interface_Mecanica, G3_Observadores_369. Código e relatório publicados, binários e módulos irmãos completos permanecem locais. Gate mecânico retorna 2 por seis arquivos ausentes; recuperar os três pacotes originais antes de integrar tampo, cordas e martelos. Sem alterar main.
