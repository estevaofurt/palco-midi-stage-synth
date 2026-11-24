# C3X — roteiro vinculante F0–F13 (correção de sequência)

**Decisão do titular, 23/11/2026:** o avanço V1–V10 / 11A–11C é pesquisa computacional, **não substitui** a conclusão da física F1–F9. O próximo marco ativo é **F1**. Não iniciar novas entregas de otimização/portabilidade V11D, incorporação de DSP no site, ou afirmar fidelidade Yamaha C3X enquanto gates anteriores não forem satisfeitos.

## Estado por fase

| Fase | Escopo | Estado | Critério de aceite |
|---|---|---|---|
| F0 | Especificação de física, arquitetura e testes | **Concluída conforme plano do titular** | Plano aprovado e versionado; manter rastreabilidade de requisitos |
| F1 | Piano de referência e parâmetros físicos | **Pendente — fase ativa** | Identidade e condições documentadas, valores com fonte/medição, unidades, incerteza, licença/proveniência |
| F2 | Infraestrutura numérica, unidades, balanço de energia, integradores | Pendente de validação | Conservação/dissipação e convergência demonstradas com referência independente |
| F3 | Cordas: tensão, rigidez, dispersão, perdas | Pendente | Parciais/decadências comparados com medidas por corda/nota |
| F4 | Martelo: feltro viscoelástico, histerese, reação | Pendente | Força-contato e rebote reproduzidos; parâmetros identificáveis |
| F5 | Ponte: movimento e energia bidirecional | Pendente | Mobilidade/impedância e balanço de energia, com validação |
| F6 | Tampo: madeira ortotrópica, nervuras, modos espaciais | Pendente | Modos espaciais e amortecimento identificados e verificados |
| F7 | Radiação do tampo/superfícies ao ar | Pendente | Transferência complexa validada, sem confundir pressão acústica com velocidade modal |
| F8 | Conjunto físico do Dó4 compartilhando a ponte | Pendente | Modelo acoplado e ensaios do Dó4, sem ressonadores de sala embutidos |
| F9 | Primeira avaliação auditiva completa do Dó4 | Pendente | Protocolo nivelado e cego quando possível; titular aprova |
| F10 | Expansão graves/agudos | **Bloqueada por F9** | Validação física/auditiva por registro |
| F11 | 88 teclas, uníssonos, pedais, ressonância e acordes | **Bloqueada por F9** | Ensaios de instrumentação e tocabilidade |
| F12 | Otimização para execução em tempo real | **Bloqueada por fidelidade** | DSP validado + carga CPU/latência/dropouts em hardware |
| F13 | Integração segura ao Stage Synth | **Bloqueada por validação** | Regressão, licença comercial, audição e hardware aprovados |

## Provas existentes ≠ encerramento de fase

- V1 é **referência subjetiva interna do próprio sintetizador**, não um registro fisicamente medido de C3X; preserve-a para A/B.
- V10 Python e seu áudio são **protótipos offline estimados**. Testes matemáticos, notas A440 e igualdade de parâmetros JS/Python não provam física Yamaha.
- Laboratório F2/F3/F4/F5 tem trechos úteis (métodos, código, testes) mas **não há prova documental suficiente** para aceitar essas fases.
- Onze modos sintéticos do tampo não equivalem a ortotropia espacial e nervuras físicas (F6).
- Som "dry" sem reverb não equivale a solução calibrada da radiação da superfície para o ar (F7).
- Testes de CPU/AudioWorklet (11A–11D) ficam **arquivados como pesquisa antecipada**, não como avanço F12. Nenhuma alteração pública.
- Critérios de evidência independentes do Stage Synth **R-GATE-1..7 seguem 0/7 aprovados integralmente**, conforme documentação existente; licença de fontes para uso comercial continua obrigatória.

## Regras de avanço

1. Trabalhar **apenas F1** agora. Análise de dados e documentação são permitidas; não alterar o timbre do Stage.
2. Para cada fase, registrar: entrada e fonte, método reproduzível, tolerâncias, resultados, limitações, hash/proveniência e decisão explícita de aceite. **Sem aceite, não promover.**
3. F8/F9 concentram primeira validação física e escuta em Dó4 antes da expansão 88 teclas.
4. O PR de importação V10 permanece **draft e não mesclado**, contendo código de pesquisa útil e **não homologado**. A árvore experimental 11D não foi publicada na branch.
5. A aplicação atual, os motores legados, efeitos e preset padrão ficam intocados.

Próxima leitura: [F1 — plano de identificação e medições](C3X_F1_PIANO_REFERENCIA_E_MEDICOES.md).
