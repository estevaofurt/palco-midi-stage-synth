# Stage Synth — auditoria industrial Yamaha 2026, ação de tecla e acoplamento estrutural

**Data:** 23/11/2026. **Escopo:** documentação/pesquisa, sem DSP, MIDI, UI, FX, samples ou presets.
**Base lida antes da pesquisa:** `main` SHA `353f516906ad718f3b6eb0661d41a853098cbcf2`, `package.json` v1.12.4; referência estável relatada pelo usuário: v1.9.5. **P1/P2 bloqueados; R-GATEs 0/7 aprovados integralmente.**

## Resultado em uma frase

Novas fontes independentes confirmam a importância de **contato viscoelástico, excitação comandada pela ação, interação bidirecional entre cordas/ponte/corpo e radiação espacial**. Encontramos dados brutos públicos do movimento de tecla/martelo e um estudo industrial da Yamaha com captação real CFX, **mas não encontramos conjunto comercialmente liberado de F_contato(t), polarizações H/V e mobilidade complexa da ponte do mesmo piano**. Portanto, a evidência **NÃO libera implementação de novo motor**.

## Novas fontes e seu alcance verificável

| Código | Fonte primária e evidência | Novo valor técnico | Acesso/direitos: conclusão |
| --- | --- | --- | --- |
| I01 | Eiji Tominaga e Masanao Sato (Yamaha Corporation), *Time-Domain Simulation using Component Mode Synthesis for a Piano*, preprint Research Square de **06/04/2026**, DOI https://doi.org/10.21203/rs.3.rs-9307819/v1 ; PDF https://assets-eu.researchsquare.com/files/rs-9307819/v1_covered_cba9e127-f049-43ed-8d2d-6287ed216ebe.pdf | Formulação conjunta de martelo viscoelástico tipo Maxwell em duas camadas, cordas rígidas e geométrica/espacialmente não lineares, condições anisotrópicas de apoio, FEM do corpo de madeira, BEM do ar e redução por modos complexos/CMS. Inclui realimentação da ponte sobre as cordas, não apenas uma reverberação após a síntese. | **Preprint não revisado por pares**; artigo CC BY 4.0, **não autoriza por si o uso comercial de todos os dados privados ou de gravações suplementares**. Os autores dizem explicitamente que dados completos não são públicos, apenas mediante solicitação e restrições proprietárias. O estudo **não demonstra nosso objetivo de 32–64 vozes em Web Audio real**. |
| I02 | Mesmo preprint I01: seção *Supplementary materials* e *Data availability* | Descreve áudio suplementar **Yamaha CFX acústico real** em WAV estéreo 44,1 kHz/24 bit: *Online Resource 1*, escala cromática nos graves gravada, e variantes simuladas 2–4 para testar dispersão e não linearidade geométrica. | Identificação autoral e especificação **no artigo**, não é arquivo WAV baixado/CRC/hash verificado por este trabalho. Separar direito de ler paper, ouvir comparações e incorporar dados/amostras ao produto. Não somar ao acervo de 50 arquivos originais já auditados. Não alegar que dispõe de áudio CFX seco em arquivo liberado. |
| I03 | Fioretti, Bergamino, Gabrielli, Ciattaglia e Spinsante, *Comparing acoustic and digital piano actions*, DAFx 2025: https://www.dafx.de/paper-archive/2025/DAFx25_paper_38.pdf ; registro: https://iris.univpm.it/handle/11566/352941 ; dados públicos: https://github.com/fiorettimichael/piano-dafx25 | Duas medidas de acelerometria sincronizada (tecla e martelo) a **20 kHz**, 72 toques em quatro dinâmicas, usando uma ação de tecla de demonstração/treinamento. A velocidade **instantânea** da tecla pouco antes de *let-off* prediz a velocidade de impacto do martelo melhor que a média entre dois contatos digitais no estudo. O artigo também expõe limitações na inferência do toque por simples MIDI velocity. | No GitHub, **quatro CSV em RawData**, tamanhos verificados por listagem de diretório: 63.769.221, 59.257.859, 54.356.818, 52.013.842 bytes, **total 229.397.740 bytes**. Não foram baixados, lidos, hashados ou executados. **Não há arquivo LICENSE na raiz verificada**: acesso público NÃO significa licença para uso comercial do dataset. Não é força martelo–corda F(t), nem ação instalada no Yamaha CFX. |
| I04 | Miranda Valiente et al., *Modelling the una-corda effect in pianos* (2024): https://eprints.soton.ac.uk/499445/ | O toque de una corda desloca lateralmente a ação e muda quais cordas de um uníssono são percutidas. A corda não percutida também passa a vibrar por acoplamento na ponte; o efeito não é redutível a EQ/volume. | Pesquisa teórica e experimental para orientar M03/M06; nenhum conjunto bruto pareado/licença comercial foi confirmado nesta auditoria. |
| I05 | Miranda Valiente, *Modelling of sound generation in pianos*, tese de Southampton (2025): https://eprints.soton.ac.uk/504922/ ; projeto ativo da universidade: https://www.southampton.ac.uk/research/projects/echoes-of-the-past-advanced-sound-synthesis-of-early-pianos | Modelo conjunto martelo/cordas/tampo e funções de resposta para radiação; projeto institucional prevê medições multidirecionais, resposta do tampo e posterior implementação C++ em tempo real. | Fonte metodológica, **não** corpus calibrado comercialmente pronto e não demonstra equivalência com o Stage Synth. |
| I06 | `mgth/unsampled-piano`, projeto Rust: https://github.com/mgth/unsampled-piano ; licença https://github.com/mgth/unsampled-piano/blob/main/LICENSE | Implementação pública de referência: 1–3 cordas/nota, dois planos, ponte e tampo, radiador, pedais e perfis de qualidade. É útil para **comparar escolhas arquiteturais** e a organização dos testes, sem inferir desempenho no nosso Android/AudioWorklet. | **Código GPLv3**, não importar, adaptar ou incorporar no Stage comercial fechado sem avaliação jurídica de obrigações copyleft. Analisar apenas conceitos publicados e técnicas independentes. Nenhum código copiado. |

## Lacunas físicas mais bem delimitadas

**L01 — Martelo:** não basta aplicar uma função arbitrária de força. O preprint Yamaha propõe material viscoelástico com memória e camadas de feltro distintas; contudo, seus próprios autores pedem validação futura direta contra ciclos medidos de força–compressão. Para Stage, **M01 continua pendente**. Não inferir contato a partir da aparência espectral de um WAV.

**L02 — Polarizações / apoios / uníssonos:** a anisotropia dos apoios da corda junto a pinos da ponte pode transferir energia entre planos horizontal e vertical, produzindo vibrações acopladas e decaimentos múltiplos. O comprimento duplex traseiro e modos longitudinais podem contribuir ao caráter metálico, mas sua importância auditiva deve ser medida por ablação. Para Stage, reforçar M02/M03 sem exigir resolver FEM 3D em tempo real.

**L03 — Ponte / tampo / radiador:** a relação fisicamente importante é *força da corda na ponte ↔ velocidade da ponte* com fase, frequência e posição; daí, *pressão radiada por microfone/posição*. Um corpo modal compartilhado sem admitância calibrada **não é automaticamente** equivalente a esse acoplamento. Para Stage, M04/M05 continuam determinantes. O trabalho Yamaha é uma direção de redução de modelo, **não um algoritmo já demonstrado leve para navegador**.

**L06/L18 — ação e expressividade:** MIDI velocity 0–127 não equivale a velocidade real do martelo em m/s. A medição DAFx explicita que a própria posição temporal de leitura da velocidade da tecla muda a correlação com o impacto; teclados MIDI de dois/três sensores medem informações diferentes de sensores contínuos de posição. Evitar prometer resposta idêntica em todo controlador MIDI. Inserir ensaio futuro **M09** abaixo, sem implementar novos recursos enquanto congelado.

**CC67 / una corda:** num cauda, deslocar a ação pode alterar **quais cordas recebem impacto e como as cordas não impactadas vibram por meio da ponte**. Não simplificar a meia-pedal binária ou equalização fixa na hipótese física. No vertical, a alavanca "soft" opera de modo diferente; tratar por instrumento.

## M09 — extensão proposta ao protocolo físico (pesquisa, NÃO executada)

**Objetivo:** mapear comando de teclado para evento físico de contato e medir repetição/escapamento.

- Em um piano e controlador identificados, coletar MIDI note-on/note-off, velocity MIDI e timestamps; quando possível, posição/velocidade/acceleração da tecla, instante de *let-off*, velocidade física do martelo no impacto, nota, dinâmica, repetição e número de sensores.
- Medir toques pp/mp/mf/ff, repetidos com e sem retorno completo da tecla e passagens rápidas; relatar incerteza e atraso entre MIDI e contato.
- Guardar canais sincronizados, calibração, mapa de transformação por instrumento e diferenças entre teclados. Não concluir correlação universal a partir das 72 observações de uma ação de treinamento.
- Se o dataset DAFx I03 for útil para **pipeline comercial**, obter autorização escrita e confirmar características/bytes/hashes dos quatro CSV ANTES de adquiri-los para calibração. Até lá, usar o paper apenas como referência teórica.

## Estratégia para a futura calibração reduzida (não autoriza código)

1. **Referência científica offline de alta fidelidade:** formular hipóteses separadas para contato viscoelástico, polarizações e acoplamento de ponte; usar literatura como método, com parâmetros específicos medidos depois.
2. **Redução causal e passiva:** representar resposta da ponte e radiador por poucos modos ou funções racionais com coerência física. Monitorar energia e estabilidade de malha fechada.
3. **Separação de cadeias A/B/C:** distinguir núcleo seco, resposta acoplada de corpo e saída estéreo completa, equiparando ganho, FX e condições para teste cego.
4. **Orçamento de processamento:** custo de atualização por corda e por modo compartilhado, com alocação 32/64 e testes p95/p99 de callbacks no Chrome/PC/Moto g04s. Não extrapolar benchmarks Node para hardware sem teste.
5. **Ablation/escuta:** só manter complexidade (duplex traseiro, modos longitudinais, frame/rim, anisotropia fina) quando a contribuição para percepção for demonstrável.

## Novas pendências e critérios objetivos

- [x] Confirmar preprint industrial Yamaha **2026**, sua condição de preprint, arquitetura e indisponibilidade pública dos dados físicos completos.
- [x] Localizar a menção autoral a **CFX real** no suplemento e diferenciá-lo de áudio já adquirido.
- [x] Identificar dataset **DAFx25** de movimento sincronizado e seus quatro CSV públicos, sem baixar ou usar por falta de licença explícita.
- [x] Examinar documentação e licença **GPLv3** de motor externo como referência arquitetural, sem copiar código.
- [ ] Verificar licença comercial específica e arquivo original do suplemento CFX, caso haja acesso; não tratar mero link como arquivo pronto.
- [ ] Solicitar autorização comercial expressa para CSV da ação DAFx antes de usá-los no pipeline Stage.
- [ ] Contratar/coletar dados **M01–M09 no mesmo instrumento**, priorizando F(t), polarizações H/V e Y_ponte(f) complexa, com direitos autorais explícitos.
- [ ] Testar e validar estimador Stage E1.1 e cadeia de renderização comparável E1.0, ainda sem mudar o motor.
- [ ] Completar R-GATE-1..7; preservar base v1.9.5 e meta 32–64 até homologação.

**Resultado deste ciclo:** teoria industrial avançou; a biblioteca permanece **50 gravações originais verificadas, seis pianos**, sem somar suplementos não baixados. **0/7 R-GATEs aprovados integralmente; nenhum protótipo integrado ou DSP modificado.**
