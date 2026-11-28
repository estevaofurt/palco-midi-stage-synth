# G3.02 — Balanço de impulso e energia de captura no feltro intermediário

Auditoria derivada dos resultados físicos arquivados no commit 310296fa0cad4c2c0b66d96d718bdcf99f8d7d57. Não houve nova integração física. As fontes de dados e as fórmulas constam em `g3-02-energia-captura-intermediario.json`. A massa é o prior CD2012 usado no modelo (não medição Yamaha): 5,775724 g (Si7) e 5,713376 g (Dó8). A recorrência de Impact atualiza a velocidade do martelo por -h*sum(F)/m e, ao capturá-lo, registra 0,5*m*v² e zera a velocidade. Logo a velocidade antes da captura pode ser reconstruída de v_in - J/m, com arredondamento de soma.

| Caso | Energia incidente mJ | Energia cinética de captura inferida mJ | Fração da energia capturada original / intermediário / graduado | J/Fpico intermediário ms |
|---|---:|---:|---:|---:|
| 107-24 | 1.283047 | 1.252522 | 96.299% / 97.621% / 97.389% | 0.648460 |
| 107-76 | 17.453601 | 16.472500 | 92.080% / 94.379% / 93.655% | 0.401990 |
| 108-24 | 1.269197 | 1.237490 | 96.023% / 97.502% / 97.317% | 0.650894 |
| 108-76 | 17.265192 | 16.281374 | 91.633% / 94.302% / 93.781% | 0.398741 |

O candidato intermediário retorna uma fração maior de energia cinética ao martelo que os outros dois em todos os casos. A diferença de pressão acústica em 300–650 Hz já observada não deve ser interpretada como aumento global da eficiência energética: o balanço restante (energia armazenada e todas as demais perdas) é menor. Não se identifica energia das cordas isoladamente nem coeficiente de restituição experimental a partir desses dados. J/Fpico dá a largura de um pulso retangular equivalente e um limite inferior da duração de força positiva, mas não mede a extensão temporal do contato real.

## Confronto externo

Askenfelt e Jansson, 1990, [String contact duration and dynamic level](https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html): contato reduz com dinâmica e chega a menos de 1 ms no registro agudo extremo; depende de massa relativa e posição de ataque. Não se deve comparar diretamente o tempo lançamento-captura com esse contato. Hall, [Comparison with measurements](https://www.speech.kth.se/music/5_lectures/hall/compare.html): medições em Grotrian-Steinweg de 2 m, alterações do espectro com dinâmica e voicing, distinção entre impactos sobre corda e parede rígida. Chaigne, 2016, [Reconstruction of piano hammer force from string velocity](https://doi.org/10.1121/1.4965965), e [relatório FWF PAPA](https://www.fwf.ac.at/en/research-radar/10.55776/M1653): método de reconstrução de força a partir da velocidade da corda; não recuperada curva diretamente comparável de Si7/Dó8 nas velocidades do modelo. A tese de Niko Plath (2019), [dissertação](https://ediss.sub.uni-hamburg.de/bitstream/ediss/6308/1/Dissertation.pdf), reproduz a figura de contato relativo de Askenfelt/Jansson, mas não foi possível verificar a imagem da página; não usamos estimativas gráficas como dados numéricos.

## Próxima ação

Executar os quatro casos de 128 parciais com os mesmos insumos, usar o comparador de contato, registrar a perda de captura diretamente no ledger do Impact e comparar com a reconstrução por impulso; separar perdas no feltro, estrutura/cavidade/exterior e energia restante. Não aumentar artificialmente a transferência de energia nem escolher feltro com base em pressão de uma única banda. A seleção do material e o gate G3.02 continuam abertos. Nenhum parâmetro alterado. Ambiente local indisponível; sem novas simulações, sem teste de escuta, sem mudança na main.
