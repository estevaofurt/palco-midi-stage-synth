# G3.10q — piloto de precisão estendida por subbloco

Controle escalar 45728458385 concluído: 30 graus reversão float64 9.89582408e-4, longdouble 9.73717467e-9; mudança 40/48 1.60533854e-7. 55 graus reversão 1.44679144e-6 vs 6.37004502e-12; mudança 1.62589782e-10. Resultados locais, não convergência matricial. Reprodução de 55 graus não binária, norma completa 7.2183e-13.

Refinamento superior combinado 55 graus aprovado: captura .99805304867, pior indicador .02235397403, malha 50/200/32. 30 graus ainda em execução.

Estender controle ao subbloco 11 completo do par 0/4 em 30 Hz (30 graus) e 80 Hz (55 graus), ordens 40/48/56. Reutilizar kernel longdouble por bloco de linhas para todas as colunas de borda; verificar reversão e entrada independente via soma escalar. Manter base/pesos double. Registrar duas aprovações consecutivas, sem alteração de tolerância. Gate do workflow significa execução diagnóstica; edgeEdgeConsecutiveGate é separado. Não promover operador parcial nem substituir refinamento em execução. Arquivo matricial em float64 é apenas diagnóstico; métricas calculadas antes da conversão. Main preservada.
