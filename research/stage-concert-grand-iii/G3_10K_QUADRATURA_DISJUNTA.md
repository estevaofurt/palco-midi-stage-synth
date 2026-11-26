# G3.10k — quadratura reativa disjunta enriquecida

Execução 45725732251, job 139594986820: 5/16 blocos disjuntos de 429 modos aprovados a 30 graus. Exemplos 0/4: diferença 01=0.00436068, 11=0.00275119, bloco inteiro=1.47e-13; 1/4: 01=0.00106432, 11=0.00124167. Restrição polinomial aproximadamente 5e-14. Não interpretar o pequeno erro do bloco inteiro como aprovação de todos os subblocos.

Reusar artefato de ordem 48 com hash, inventário e restrição verificados; não recalcular cinco blocos aprovados. Para os onze restantes, testar 56/64/72, exigir duas comparações consecutivas <=1e-8 para todos subblocos e restrição polinomial. Registrar separadamente escala do subbloco e erro relativo ao bloco inteiro para investigar cancelamento/precisão. Não usar essas escalas para relaxar o gate. Resultado somente diagnóstico, sem substituir as matrizes na cadeia 429. Primeiro 30 graus (falha confirmada); repetir a 55 se necessário, após evidência correspondente. Nenhum ajuste físico.
