# G2.01-M — parâmetros físicos essenciais, versão de consolidação
Referências G2.01-M e G1, verificação documental 2026-11-25. Não são parâmetros escolhidos para G2. Dados publicados pontuais não são intervalos estatísticos nem especificações CFX.
| Componente | Candidato ou controle | Estado e limites |
|---|---|---|
| Tampo Sitka | rho 392 kg/m³, EL 11.5 GPa, ER .47 GPa, GLR .50 GPa, nuLR .3 | tabela 1 Boutillon/Ege 2013; madeira de referência, umidade/incerteza não estabelecidas nesta consulta |
| Tampo Norway spruce | rho 440, EL 15.8, ER .85, GLR .84, nuLR .3 (mesmas unidades) | mesma tabela; não afirmar CFX medido |
| Ponte maple | rho 660, EL 10, ER 2.2, GLR 2, nuLR .3 | mesma tabela; geometria, junta e perdas desconhecidas |
| Aço núcleo | G1 7850 kg/m³, E 200 GPa; Euphonics Broadwood usa 7800 kg/m³, E 210 GPa | hipóteses de referência plausíveis; não intervalo universal nem medição do fio específico |
| Cobre | rho 8960 kg/m³ | valor nominal de Euphonics; modelo de enrolamento, atrito e EI efetivo não identificados |
| Martelo | F=K*C^alpha com histerese opcional; m efetiva, K em N/m^alpha, alpha adimensional | lei candidata, depende de registro, velocidade e feltro; sem K/m/alpha selecionados; G1 como controle |
| Tampo/costelas | G1 1.4x1.1m, 8mm uniforme, rho 430, E 11/.8 GPa, G .65, nu .3 | geometria hipotética G1; não usar como G2 definitivo; comparar materiais completos com geometria fixa |
| Perdas | sigma em s^-1, fator de perda adimensional, mobilidade m/(N s) | separar fio, juntas, corpo, ar; valores desconhecidos, calibrar com dados pertinentes; não inferir de RMS gravado |
| Aro/armação/abafador | rigidez N/m, massa kg, dissipação Ns/m, feltro não linear | parâmetros ainda não identificados; simplificar/avaliar quando fase exigir |
| Ar | G1 rho 1.204 kg/m³, c 343 m/s | hipóteses ambiente homogêneo; não resposta de sala |
Fontes: https://doi.org/10.1016/j.jsv.2013.03.015 ; https://www.sciencedirect.com/science/article/pii/S0022460X12007936 ; https://euphonics.org/12-2-1-parameter-values-for-piano-simulations/ (usa medições Broadwood + valores de literatura; algumas massas estimadas, Q fixo apenas ilustração, EI do núcleo; CC BY-NC-SA, não importar áudio/figuras/dados de licença incompatível); https://pubmed.ncbi.nlm.nih.gov/10790050/ (medidas de força/compressão e flexão da haste); https://iris.univr.it/handle/11562/342223 (síntese modal transversal/longitudinal, convolução ou filtros de segunda ordem). 
## Interfaces mínimas a comparar G2.04 (não decisão de arquitetura)
Excitação: força N, posição/área, velocidade m/s, estado de contato. Corda/ponte: força e velocidade conjugadas, potência W, energia J, perdas >=0 quando passivo. Corpo: mobilidade complexa e observação de pressão Pa ou saída relativa explicitamente calibrada; não aplicar filtro de saída como perda mecânica. Ação: fonte separada somente se justificável, evitar duplicar impacto. Áudio 48 kHz inicial, teste convergência e banda. Modelo G1 offline como controle; modal reduzido e waveguide/híbrido candidatos. Não selecionar antes de G2.03.
## Limite
Consolidação de hipóteses suficiente para planejar pilotos, não biblioteca de materiais completa. K/m/alpha, perdas, escala e geometria ainda precisam ser decididos na fase apropriada. Não são bloqueadores para escrever especificação, mas são bloqueadores para afirmar calibração física ou promover motor. Sem alteração G1/main.
