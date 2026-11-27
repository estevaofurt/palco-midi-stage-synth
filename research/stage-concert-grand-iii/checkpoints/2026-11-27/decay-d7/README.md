# G3 — Decaimento acústico e bandas de frequência
Continuação de bfd1125. 132 entradas dos manifestos verificadas. 369 portas, 127.825 estados, 48/384 kHz, tampo d3, abertura d6/mista/d7; d8 referência. Mesmo transiente seed 271134 e seleção de 144 direções. 106 intervalos excitados + 534 sem fluxo superior imposto. Quatro execuções de 640 blocos, 20.480 subpassos no total. Todos passam conservação: energia 2,01805e-16, trabalho 6,38865e-15, continuidade projetada 1,507e-15, fina d8 7,01972e-15. Nenhum trabalho acumulado negativo. Prefixos de fluxo/carga de 320 blocos idênticos aos arquivos anteriores.

| Modelo | Pior receptor fino completo % | Pior receptor fino prefixo % | Pior receptor abaixo de 24 kHz prefixo % | Pior receptor filtrado 48 kHz prefixo % |
|---|---:|---:|---:|---:|
|d6|1,733017|1,667291|0,00258921|0,00000499062|
|mista|1,207963|1,161283|0,00092767|0,00000032090|
|d7|1,203413|1,156819|0,00082915|0,00000019758|

Nenhuma aproximação passa critério histórico de 1% de pressão fina individual. DFT de janela retangular, 9 bandas e verificação Parseval: 98,973–99,546% do erro quadrático d7 no prefixo acima de 96 kHz. Filtro de referência FIR Kaiser 617 taps, corte 22 kHz, rejeição 99,60 dB desde 24 kHz, atraso 0,802 ms. Não constitui implementação em tempo real ou validação audível. Zerar fluxos aos 320 intervalos altera pressão d8 na janela 320–640 em 16,5952%; ainda existe fluxo inferior ao fim de 640. Convolução após 640 assume fluxo zero, não cauda real do piano.

Tempo de loop local d8 186,617 s; d6/mista/d7 24,387/24,130/23,399 s. Sem benchmark controlado, sem ganho misto demonstrado. Não alterar critério de precisão, manter d7 referência projetada/mista experimental/d8 fina. Retomar integração mecânica piloto e avaliação com excitação de cordas/martelos. Sem render ou promoção; geometria piloto, 12 dependências de regeneração pendentes, parâmetros de ensaio escolhidos nesta etapa.

Pacote local G3_Decaimento_D7.zip (40 arquivos no SHA256SUMS, integridade ZIP verificada) contém extend.py, módulos, band_audit.py, observer48_audit.py, cutoff_audit.py, resultados, sinais e logs. Este commit publica dois módulos de auditoria e relatório, não todos os scripts e binários. Reproduzir conforme CHECKPOINT.md do pacote, com uma thread BLAS/OMP/Numba.
