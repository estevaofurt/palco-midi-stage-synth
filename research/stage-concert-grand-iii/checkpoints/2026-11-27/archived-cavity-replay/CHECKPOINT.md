# G3 — Revalidação temporal da cavidade arquivada

## Escopo e decisão
Usar os operadores físicos já congelados, sem regenerar a geometria. Manter G3, d3 a 48 kHz, oito subpassos a 384 kHz e a normalização corrigida. A cavidade possui 127.825 estados físicos. Nenhum render sonoro, alteração na main ou promoção de versão.

A partir do `adaptive_candidate.npz` e dos kernels com `idx` e `scale`, recuperou-se a incidência superior como `T*sqrt(area_celula)/scale` e a inferior como direção DCT unitária com sinal de paridade. A área celular é 0,0025244444444444446 m², recuperada da escala do modo inferior constante. As escalas inferiores obedecem aos fatores sinc de integração da malha 30×30; as normas superiores são unitárias após a correção (tolerância relativa 1e-13). É uma reconstrução algébrica a partir dos operadores arquivados, não uma validação independente da geometria original.

O runner reutiliza as definições originais Cavity, basis, block_kernel, cavity_markov e simulate por extração AST, evitando dependências de montagem geométrica. Execute apenas sobre fontes previamente verificadas pelo manifesto de restauração. Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0; BLAS/OMP 1 thread. Os parâmetros de teste seguem o simulate histórico.

## Execuções
```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python replay.py /caminho/restored --blocks 128 --ports 6 12
# preservar results.json como results-6-12.json antes do segundo comando
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python replay.py /caminho/restored --blocks 128 --ports 24 48
```
6/12 portas: b16, d2 e d3; 24/48: b64, d3. Ruído, pulso senoidal amortecido, seno de 7851,2 Hz. 128 blocos (2,667 ms) por caso. 18/18 ensaios concluídos e critérios de resíduo 1e-10 e trabalho acumulado não negativo dentro de 1e-10 aprovados. A comparação de 6/12 usa a normalização corrigida; não substitui a repetição de toda a grade harmônica contínua.

| Métrica máxima (18 casos) | Resultado |
|---|---:|
| Energia da cavidade | 2,0835004677314666e-16 |
| Trabalho da interface | 1,4700000987321134e-15 |
| Continuidade projetada | 1,6124889848247734e-15 |
| Reprodução da saída da cavidade | 2,1684237458123098e-14 |
| Reprodução dos receptores | 1,305985082944548e-15 |
| Exponencial modal independente (amostra) | 3,1931651490819134e-14 |
| Mínimo normalizado de trabalho acumulado | 0 |

Uma execução de 64 blocos (512 subpassos) falhou no critério relativo de receptor porque o primeiro tap não nulo aparece em 558/559 subpassos; a referência FFT contém apenas resíduo de arredondamento antes da chegada. Preservada em short-window-failure.*. A janela foi aumentada sem relaxar o critério. Um primeiro comando de 128 blocos foi interrompido por timeout e substituído pelas duas execuções completas acima. Não constitui medição de cauda ou ataque, validação de continuidade instantânea fina, certificação de passividade global ou tempo real. O caso d3 de 48 portas chegou a 5,944 s para 128 blocos, sem otimização de desempenho.

## Próximos passos
A auditoria anterior ainda aponta 12 dependências ausentes para regenerar a geometria completa e reproduzir a referência contínua. Revalidar a grade harmônica de 6/12 portas, medir continuidade fina versus d8, construir o operador exterior completo de 369 portas e executar acoplamento temporal. Os binários permanecem fora do GitHub; o runner e relatório não substituem os ZIPs originais.
