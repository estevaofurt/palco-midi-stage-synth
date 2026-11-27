# G3 — verificação executável de infraestrutura de 500 ms

O ZIP de continuidade de 250 ms foi recuperado nesta sessão (18065854 bytes retornados pela biblioteca), porém a infraestrutura local de execução Python e terminal falhou novamente. O hash ainda precisa ser reconferido pelo executor. Nenhum passo físico de 500 ms foi executado.

A verificação de utilitários foi adicionada para execução no GitHub Actions, somente na branch de pesquisa. Testa cabeçalhos NPY 1.0 e 2.0, três formatos de array, detecção de alteração dentro do prefixo, invariância a alterações posteriores ao prefixo, rejeição de dimensão inválida, comparação dos cinco arrays, rejeição de snapshot corrompido, de sinal alterado e de comando de pedal alterado. Os dados são exclusivamente fixtures de teste de I/O, não um piano simplificado. O workflow também compila os fontes e verifica o CLI. Python 3.12 e NumPy 2.2.6 seguem o ambiente de CI histórico. Nenhum resultado de teste é presumido antes da execução do workflow.

Não há ZIP nem NPZ no Git tree da branch verificada. A transferência do ZIP da biblioteca para o executor GitHub ainda não está estabelecida. Não publicar binários físicos em repositório público sem verificar a autorização. O caminho local permanece documentado em README.md; o workflow novo não declara validação física e não altera main. Para executar a física completa é necessário um ambiente Python funcional com acesso ao pacote original e espaço em disco.

Última referência física aprovada: 750400edac818a4af56e791ffa13a79c0098006c (250 ms). Preparação física de 500 ms: 31d5d5dddc34c406492199c6ced38e2b1d2f3ffc. 
