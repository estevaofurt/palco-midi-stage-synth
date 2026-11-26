# G3.10j — transferência espacial de 355 modos

Evidência 45726104119: menor configuração comum [55,55,55,45,45,55,45], 355 de 385. Máximos Z .00095006154, P superior .00107754658, P inferior .01087019175, P exterior .00145712633, fluxo .02910460017, velocidade .04330654064. Aos 30 graus 355 é mínimo; aos 55 graus 345 é mínimo isoladamente. Seleção retrospectiva.

Validação independente da malha: congelar configuração antes de ler 50/200/32, verificar hashes, frequência, estabilidade, captura e gate espacial; reproduzir matrizes 40/160/24 e 50/200/32; comparar 355/385 em ambas, 385 entre malhas, 355 entre malhas, e 355 grosseiro contra 385 fino. Limite 5% em cada métrica, sem somar erros ou modificar parâmetros. Se qualquer gate falhar, não promover. Workflow depende da prova combinada 45726103993. Não certifica convergência modal absoluta nem radiação.

429: execução 45725732251, suave 30/55 aprovada; reatividade disjunta 30 graus falhou (5/16 blocos aprovados, subblocos de borda não convergiram a 1e-8 embora restrição polinomial preservada). Próximo diagnóstico: investigar quadratura e piso numérico dos subblocos antes de retomar acoplamento; não relaxar tolerâncias. Main, G1/G2 e WAV preservados.
