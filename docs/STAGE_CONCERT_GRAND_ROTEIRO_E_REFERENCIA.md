# Stage Concert Grand — decisão de referência e especificação inicial (24/11/2026)

**Decisão do titular:** "vamos utilizar as características conhecidas dos pianos Yamaha para criar um timbre próprio que mantém a indentidade da marca". Novo objetivo: piano de cauda original do Stage Synth, inspirado no caráter acústico Yamaha CX/CFX/C5, sem alegação de réplica fiel, endosso ou afiliação. Stage Concert Grand é nome provisório próprio.

## Isolamento e governança
Nova branch research/stage-concert-grand a partir de df468f03ed6ea474ea4cf79873328a5af9dd462d (F1.11). C3X F1 permanece PENDENTE na rota original, preservada em research/import-c3x-v10-20261123; os gates R do produto continuam 0/7 integralmente homologados. Esta decisão altera o escopo de pesquisa, não retroativamente o estado do C3X. O novo roteiro abaixo rege apenas research/stage-concert-grand; o roteiro C3X anterior continua válido no seu escopo. Nenhuma alteração em main, V10, UI, motores, efeitos, presets ou integração. Sem samples na síntese do novo instrumento. Referências de áudio somente análise/escuta com direitos aplicáveis; não embutir PCM ou IR extraída de terceiros.

## Referências e identidade
- Yamaha CX: https://usa.yamaha.com/musical-instruments/pianos/products/grand-pianos/cx-series/ e https://usa.yamaha.com/products/musical_instruments/pianos/grand_pianos/cx_series/cx-series.html — descrição qualitativa do fabricante: clareza, caráter percussivo e brilhante, sustentação, riqueza harmônica, nuance de dinâmica; tampo com coroa e ligação ponte/nervuras/tampo, feltro adaptado por modelo.
- Yamaha CFX: https://europe.yamaha.com/en/musical-instruments/pianos/grand-pianos/cfx-01/ — referência qualitativa de graves potentes, riqueza de cores e clareza. Não são curvas espectrais ou parâmetros físicos medidos.
- C5 Salamander Grand Piano V3, Alexander Holm, CC BY 3.0, https://github.com/sfzinstruments/SalamanderGrandPiano commit 3382bf9496bba2486f5ab0de55a264d1dfc38404. C4 v1/v8/v16, dados numéricos arquivados C5_C4_verified_numeric_report.json, blob 63e893d8cfff79c247c0ea76b944885669a8249f; aquisição original CI https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45313270498. Camadas não são velocidades medidas; posição de microfone limita inferência. A/B com V10 também obrigatório.
- F1.9–F1.11: métodos de consistência da corda, catálogo nominal Röslau e literatura de outros pianos apenas para plausibilidade; nenhuma escala de Steinway ou Yamaha copiada. Não usar BiVib NC em produto sem autorização.

Objetivo perceptivo próprio: graves definidos e encorpados; médios ricos sem caráter de violão; agudos claros sem ruído/metal excessivo; ataques naturais e dependentes de intensidade; pp delicado, ff potente, sustentação musical, batimentos e decaimento multitemporal, ressonância acoplada, separação entre notas. São metas a avaliar, não resultados. Timbre deve emergir de física e radiação, não EQ por parcial, ruído decorativo, samples ou IR artificial para mascarar problemas. FX do produto continuam opcionais e separados.

## F1 do novo projeto — baseline inicial C4
Hipóteses autorais: fio circular maciço com apoios ideais, L=0,650 m, d=0,960 mm, E=200 GPa, rho=7850 kg/m³; f1 alvo 261,6255653 Hz. L e d escolhidos próximos do exemplo hipotético de F1.9 e arredondados para aproximar B do C5; não medidos em nenhum Yamaha, não otimizados em todos os registros, nem instruções de fabricação/afinação real. T calculada a partir de mu geométrica e EI, não inversamente forçando mu para acertar f1. A=pi*d²/4, I=pi*d⁴/64, mu=rho*A, EI=E*I, T=4L² mu f1² - pi² EI/L². B=pi² EI/(T L²).
Resultados: T=657,083171860 N; mu=0,005682010137 kg/m; EI=0,008338440354 N m²; B=0,000296440484; massa vibrante por corda=0,003693306589 kg; impedância transversal característica de corda flexível sqrt(T*mu)=1,932240472 N s/m (aproximação de baixa frequência, não mobilidade da ponte). f1=261,6255653 Hz. Tricórdio é hipótese de projeto a validar futuramente; não simulado agora.
Com o mesmo critério F1.8, ajustar somente f1 de ambos modelos fixos em parciais 2–8 e comparar 28 picos elegíveis 9–12 em 8 janelas. RMS agrupado V10 17,012224 cents; novo candidato 0,873673 cents (melhor em 8/8). Uma janela suave excluída, sem pico reservado. Comparação retrospectiva no mesmo corpus usado para escolher B, NÃO validação independente, nem renderização, nem melhora auditiva demonstrada. Reservar novas tomadas/camadas não usadas na escolha para teste posterior, com protocolo predefinido.
12/12 verificações em JavaScript V8 antes da gravação; helpers recuperados diretamente do GitHub. Reproduzir `node research/stage-concert-grand/c4-design.test.mjs`. Commits 27a99f0abc49aeea9073fd7ddaa3c1c89f6f6053 e 91a5925c227182325a36c076c30576cbde7dd628. Sem CI novo/hardware.

## Roteiro exclusivo da linha original
| Fase | Escopo e critério | Estado |
|---|---|---|
| F0 | Escopo original, arquitetura, critérios e preservação | Direção aprovada pelo titular; documentada |
| F1 | Referências qualitativas, C5 acústico, hipóteses SI, proveniência, baseline C4 | Baseline de corda estabelecido para pesquisa; parâmetros de ação/corpo ainda hipóteses a declarar; não homologado |
| F2 | Infraestrutura numérica offline; conservação de energia, força/velocidade conjugadas, dissipação não negativa, convergência dt e regressão | Próxima |
| F3 | Corda rígida dispersiva e perdas passivas; frequências teóricas e energia, sem ajuste ad hoc por parcial | Pendente |
| F4 | Contato unilateral feltro viscoelástico, reação, histerese e toque contínuo | Pendente |
| F5 | Ponte móvel com troca bidirecional, impedância e transferência entre cordas | Pendente |
| F6 | Tampo ortotrópico e nervuras; modelos modais fisicamente motivados, convergência espacial e energia | Pendente |
| F7 | Radiação do movimento superficial ao ar; geometria, fase e pressão relativas; não confundir com IR de sala | Pendente |
| F8 | Primeiro C4 completo; tricórdio, amortecimento, toque e soltura; gerar WAV original somente quando o conjunto existir | Pendente |
| F9 | Comparação auditiva C5/V10/novo, ganhos comparáveis, dados independentes e aprovação do titular | Pendente |
| F10 | Expandir por regiões e registros, incluindo transições de cordas enroladas | Bloqueado por F9 |
| F11 | 88 teclas, pedais, repetição, acordes, ressonâncias compartilhadas | Bloqueado por F9 |
| F12 | Otimização sem perda sonora, 32–64 vozes em hardware real, medir CPU, latência e dropouts | Bloqueado por fidelidade |
| F13 | Integração com regressão, licenças e aprovação; preservar versão estável | Bloqueado |

O requisito de metrologia de um C3X específico deixa de bloquear a pesquisa da linha autoral; não se elimina a exigência de física consistente, evidência acústica independente ou aprovação. F2 pode iniciar isoladamente no novo escopo, mantendo fases sequenciais e critérios de parada. Nenhum aceite automático por contagem de testes. F1 é baseline inicial de projeto, não validação de instrumento real; documentar novos parâmetros com classes de evidência e incertezas/limitações antes de utilizá-los. Não promover antes de F9/F12/F13. Próxima ação F2: verificar os solvers passivos existentes, medir convergência e energia com soluções independentes e construir somente o que faltar.
