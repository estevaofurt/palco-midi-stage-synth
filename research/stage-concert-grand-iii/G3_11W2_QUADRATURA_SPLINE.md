# G3.11w2 — corrigir quadratura de projeção estrutural

Run 45735244983: três testes unitários passaram, referência seca e autovetores alcançaram a etapa de projeção, mas quadratura global 30/42 falhou antes de exportar. Não há coeficientes aprovados.

A superfície usa splines cúbicas por células. Quadratura global cruza nós internos. Reusar LocalBasis.patches e integrar cada polígono recortado com ordens 8/12; acumular Gram e lado direito, calcular resíduo diretamente na segunda passagem. Preservar tolerância do mapa 1e-5 e equações normais 1e-8, verificar área 1e-10 e estabilidade do resíduo agregado 1e-8. Registrar diagnóstico mesmo se falhar. Teste unitário com campo polinomial e função cúbica por partes. Nenhuma alteração em massa/rigidez/amortecimento nem relaxamento de critérios. Quatro campos e amortecimento diagonal permanecem hipóteses não validadas. Main preservada.
