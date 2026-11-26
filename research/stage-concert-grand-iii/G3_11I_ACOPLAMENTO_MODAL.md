# G3.11i — acoplamento modal temporal de baixo rank

G3.11h piloto esparso: otimizador e passividade aprovados, fidelidade reprovada. Treino 1.001673873 / 1.009550863, máximo validação interna 4.905824353 / 2.508479491 (30/55). Não promover. Densificação em andamento. 

Estender a estrutura de G3.06d (inertância + osciladores) a R+sM+K/s+osciladores e massa, rigidez e amortecimento estruturais diagonais. Acoplamento recíproco A, sem duplicação de energia; ponto médio implícito e orçamento de trabalho/dissipação. Usar fatoração de Woodbury da atualização de rank <=4, inclusive quando H singular, e comparar com Cholesky denso. Teste puramente sintético, 32/64/128 modos estruturais, 44.1/48/96 kHz, fechamento <=1e-9, estados contra solução densa <=1e-8. Benchmark de Python por amostra com 32/64/128/256 modos, fatoração prévia; não medir motor de áudio. Modos estruturais não são notas MIDI. Não usar coeficientes físicos rejeitados, não integrar cordas ou gerar áudio. Main preservada.
