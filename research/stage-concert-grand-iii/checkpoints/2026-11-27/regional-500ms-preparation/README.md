# G3 — Preparação da validação regional de 500 ms (não executada)

Continuação do checkpoint físico 750400edac818a4af56e791ffa13a79c0098006c. Não é um resultado de simulação: ambiente local Python/container indisponível nesta sessão. Foram lidos os códigos e manifestos originais pelo GitHub e verificadas 10 propriedades estáticas. Não há evidência nova de conservação, convergência ou som em 500 ms.

## Protocolo

384 kHz, 192000 passos/caso, sete notas, 18 cordas, 1360 coordenadas adaptativas vs 2384 uniformes, 369 portas, 127825 estados acústicos, coeficientes refinados. Cronograma histórico de 250 ms mantido integralmente; nenhum novo evento. Todos os abafadores fechados após 200 ms. A extensão observa a cauda fechada; não é teste de sustain aberto.

Três casos: contínuo misto, contínuo uniforme, misto retomado em 22000 (durante repetição segundo captura histórica), 96000 e 153600 passos. Total planejado 576000 passos. Drivers copiados da referência; apenas escolhas de duração/rate alteradas. Integradores, matrizes, coeficientes, eventos e métodos de contato permanecem nos módulos originais do ZIP verificado. Não há redução acústica nesta fase.

## Gates

Auditoria original de energia, dissipação, causalidade, pressão e bandas; todas as dez janelas de 50 ms e pressão completa devem passar. Verificar que após 200 ms não há forças de martelo, injeção ou abafador aberto. Comparar cinco arrays e 18 indicadores físicos mais comandos, snapshots e hashes de prefixo em retomada. Verificar os dez hashes arquivados dos NPY de 250 ms por reconstrução do cabeçalho NPY e prefixo dos novos arquivos; divergência exige inspeção, inclusive possível diferença apenas de cabeçalho, não relaxamento automático. Resultado completo exige todos os gates, inclusive retomada. --skip-restart é execução parcial.

## Executar

Com Python 3.11+, NumPy, SciPy e Numba compatíveis com o ambiente histórico e pelo menos 12 GiB livres, obter G3_Continuidade_Regional_250ms.zip (SHA-256 1d279241b7effc9704539c98987efd775eb937c369efcc2d3438354525570192) e esta pasta de código do GitHub.

```
python reproduzir_500ms.py --package /caminho/G3_Continuidade_Regional_250ms.zip --workdir /caminho/novo-diretorio
```

O executor confere o ZIP e suas 182 entradas, usa uma cópia isolada, grava logs, executa os três casos, conserva snapshots e escreve acceptance-500ms.json. Não usar Python -O. Se interrompido, preservar diretório e logs; as opções --resume/--stop-step do driver permitem retomada de snapshots existentes para a mesma configuração. Não há garantia de igualdade entre versões distintas de bibliotecas. Não sobrescrever referência de 250 ms.

## Status

Preparação publicada, sem execução dos scripts Python novos ou aprovação do piloto. Referência de 250 ms intacta. Redução acústica, cauda com pedal aberto, expansão a 88 teclas, tempo real e validação sonora continuam pendentes.
