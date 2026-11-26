# G3.10n — controle pontual de precisão estendida

Diagnóstico 55° 45726759467 reproduz ordem 48 exatamente. Bloco 0/4: reversão erro inteiro 2.43e-16, subbloco 11 3.93e-6; subbloco 11 representa no máximo 2.20e-11 da norma do bloco. Bloco 1/4 também sensível à reversão. Não atribuir tudo à quadratura nem declarar convergência.

Selecionar no bloco 0/4 a frequência com maior erro relativo de reversão do subbloco 11 e entrada de maior diferença absoluta nessa frequência. Reavaliar somente essa entrada nas ordens 40/48, ambas orientações, em longdouble (kernel e soma; coordenadas, pesos e bases ainda double). Comparar mudança de ordem e reversão na mesma escala do subbloco. Controle pontual não certifica os blocos e não altera tolerâncias ou operador de referência. Não utilizar como substituto para o teste de 429 modos. Comparação 355/385/429 permanece condicionada.
