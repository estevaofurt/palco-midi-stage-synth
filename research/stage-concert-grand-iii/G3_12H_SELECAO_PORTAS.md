# G3.12h — seleção robusta de portas e referência densa

G3.12g run 45741529339: replay 3.7719069276616166e-08, massa 1.439525945501297e-15; 10 cordas, 4 notas. Treino 72/80/88/104/120: 0.028080349333325514 / 0.00014390945437076932 / 1.711827774191064e-05 / 1.2968531517675777e-06 / 7.36916177793669e-07. Seleção 72 reprovada na validação 0.07590477099748114. Não promover. A falha antiga de lift não foi reproduzida no novo runner; diagnóstico arquivado <=4.64e-9, causa exata não confirmada.

Nova seleção: 31 pontos de desenvolvimento (16 originais + 15 antigos de validação), 15 pontos internos a 1/4 dos intervalos logarítmicos, 15 novos externos a 3/4. Critério <=5% em treino e interno, selecionar menor rank, congelar antes de prova externa. Gate físico separado da execução.

G3.12e run 45741529235: passividade e otimização aprovadas, ajuste físico reprovado: interno 0.1970769297964232, treino 0.20183941210515538, validação 0.1634712505617903. Não incorporar. Referência densa anterior run 45730538297 concluída success (4 lotes e 2 consolidações). Ativar caminho dense no push do workflow regularized-fit, mantendo verificação de conclusão e hashes; manual ainda permite fine. Referências quatro campos e 72 campos distintas. Sem promoção ao motor. Main preservada.
