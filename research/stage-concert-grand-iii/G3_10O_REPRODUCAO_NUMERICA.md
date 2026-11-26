# G3.10o — reprodução numérica e controle bilateral de precisão

Execução 45726986653 falhou antes da avaliação longdouble: igualdade binária de forward versus arquivo. Não foi medido o erro desta reprodução, portanto a causa exata (ambiente, BLAS, base ou outro fator) ainda não está demonstrada.

Auto-interações dos dois ângulos aprovadas (7/7 cada, jobs 139594986577 e 139594986601); contatos 5/5; cavidades e suave aprovados. Restam blocos disjuntos, 5/16 e 6/16 aprovados originalmente. Não reiniciar FEM nem auto-interações.

Corrigir exclusivamente gate de reprodução do diagnóstico escalar: norma completa e polinomial <=1e-10, reportar igualdade binária e todos os desvios relativos, inclusive subblocos pequenos. Selecionar a entrada pela comparação local de mesma base e mesmos nós. O resultado não certifica a reprodução dos subblocos nem autoriza promover matrizes. Manter gate de quadratura 1e-8 inalterado. Executar 30 e 55 graus, pois 30 apresentou maior sensibilidade. Preservar experimentos anteriores.
