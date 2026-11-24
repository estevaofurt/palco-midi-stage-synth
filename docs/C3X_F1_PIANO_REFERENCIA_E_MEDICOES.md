# C3X — F1: identificação do instrumento e registro de parâmetros

**Situação:** PENDENTE. Nome de modelo Yamaha C3X escolhido como referência nominal; **nenhum exemplar físico específico documentado e medido neste projeto**. Medidas externas publicadas não substituem medições de corda/ponte/tampo nem autorizam afirmar timbre fiel.

## 1. Identidade e rastreabilidade

Para cada exemplar/gravação/medição registrar:
- Fabricante, modelo, revisão/ano aproximado e instrumento identificado (número de série em registro restrito se confidencial).
- Técnica e data da afinação, A4, stretch medido; idade/estado das cordas, martelos, abafadores e pedais.
- Sala (dimensões e materiais), posição da tampa, microfones, posições/ângulos/distâncias, cadeia de áudio, resposta dos sensores e calibração; minimizar a sala e **registrar o resíduo**, não remover ressonância natural do instrumento.
- Propriedade dos dados, consentimento, autorização **comercial**, fonte primária, data de aquisição, SHA-256 e versão. Separar referência legítima de amostras para reprodução.

## 2. Matriz de parâmetros: medir, obter de fonte legitimada ou declarar desconhecido

| Família | Evidências desejadas | Unidade/observação |
|---|---|---|
| Encordoamento C4 inicial | quantidade de cordas no uníssono, comprimento vibrante, diâmetro/encordoamento, massa linear, tensão, afinação por corda, posição de excitação | m, kg/m, N, Hz; medições com incerteza |
| Modos das cordas | frequências de parciais, inarmonicidade B, taxas de decaimento por parcial, duas polarizações e batimentos | Hz, B adimensional, s |
| Martelo/feltro | massa efetiva, velocidade de impacto real, compressão, força x deslocamento/velocidade, retorno e histerese | kg, m/s, N, m; não equiparar velocity MIDI a m/s |
| Ponte | mobilidade complexa e, onde possível, resposta cruzada a força; direção/local do ponto de contato | (m/s)/N, magnitude e fase |
| Tampo/nervuras | orientação da madeira, espessuras aproximadas, nervuras, condições de contorno e modos espaciais amortecidos | m, Hz, razão modal; distinguir dado de estimativa |
| Radiação | medições sincronizadas de superfície/ponte e pressão em posições documentadas, resposta relativa com fase | m/s², Pa, Hz; excluir respostas de sala quando possível |
| Dó4 seco | notas isoladas pp/mf/ff com velocidades **físicas** documentadas ou proxy claramente identificada; nota solta, pedal e notas vizinhas | PCM original, sem normalização variável, metadados e hashes |

Não inventar números ausentes. Anotar cada campo como `medido`, `fonte primária pública`, `estimado` ou `desconhecido`, com incerteza e rastreabilidade.

## 3. Marcos de F1 (execução ordenada)

1. **F1.1** — Identificar exemplar C3X real acessível ou conjunto de medições original comprovadamente correspondente ao C3X, autorizado comercialmente; documentar acesso indisponível se for o caso.
2. **F1.2** — Abrir inventário de campos e coletar metadados de instrumento, captação, afinação, medições acessíveis, licença e SHA-256.
3. **F1.3** — Priorizar Dó4: obter sinais isolados, parciais/batimentos e parâmetros físicos mínimos para iniciar F2–F8 sem assumir geometria sintética como verdade.
4. **F1.4** — Documentar ausência de campo, erro/incerteza, método de estimação aceito e plano experimental de complemento, sem falsear validação.
5. **F1.5** — Auditoria de licença comercial e aprovação explícita do usuário para avançar a F2.

## Entregáveis necessários para aceite

- Identificação e provenance do **mesmo instrumento** para os ensaios fundamentais.
- Tabela de parâmetros com valores, unidades, origem, incerteza/intervalo e lacunas destacadas.
- Conjunto reprodutível das referências de Dó4 ou sua localização autorizada, com SHA-256 e direitos compatíveis com a finalidade comercial.
- Protocolo de validação que diferencie parâmetros inferidos de parâmetros medidos, e relatório de limitações.
- **Aceite explícito:** somente então mudar o estado de F1 de pendente para concluída.

Sem dados físicos C3X, é possível continuar pesquisa metodológica, mas não declarar F1 completa nem avançar com a identificação de outro instrumento como se fosse um C3X.
