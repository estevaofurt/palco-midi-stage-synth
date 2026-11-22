# Stage Synth — prioridades e próximos passos

**Atualizado em:** 22/11/2026. Este arquivo é um plano, não confirma implementação.

## Prioridade 0 — Preparar integração correta entre conversas e código

- [x] Adotar GitHub como referência central.
- [x] Criar `AGENTS.md`, `docs/ESTADO_ATUAL.md`, `docs/DECISOES.md` e este plano.
- [ ] Identificar onde está o **código completo da linha "Novo Stage v1.11.0"**, caso exista fora do repositório. Não assumir que o protótipo pode ser integrado diretamente na raiz v1.8.4.
- [ ] Verificar diferenças entre linhas `main`, `physical-v1.9.5`, `physical-v1.9.6` e a fonte verdadeira do Novo Stage; escolher e documentar uma **base concreta** para a próxima implementação.
- [ ] Criar rotina de atualização dos quatro documentos após cada commit relevante, com verificação de HEAD e testes.

## Prioridade 1 — Estabelecer baseline que não volte a estalar

- [ ] Rodar testes de lógica e navegador da v1.9.5; guardar configuração de áudio e referência de desempenho.
- [ ] Medir áudio real no PC e no Moto g04s, incluindo 32 e 64 vozes, sustain, reverb e camadas; registrar o limite observado.
- [ ] Identificar eventuais diferenças de latência entre navegador, motor e configurações.
- [ ] Preservar revert/backups ao introduzir mudanças.

## Prioridade 2 — Recuperar fidelidade acústica

- [ ] Integrar seletivamente o acoplamento mecânico de v1.12.1 na **base escolhida**, após revisar a estabilidade numérica e a API de voz existente.
- [ ] Evitar adicionar o novo tampo como reverb paralelo sobre outra simulação de tampo; medir ganho, caudas e feedback por nota.
- [ ] Implementar rigidez/dispersão adequada e inarmonicidade B em vários registros; comparar com auditoria de v1.9.6.
- [ ] Fazer ataque de martelo responsivo a velocity e amortecimento espectral independente por parcial.
- [ ] Modelar 1–3 cordas acopladas por tecla conforme registro e orçamento de CPU, com ressonância simpática condicionada a abafadores/sustain.
- [ ] Calibrar Japanese, American, Felt e Upright separadamente. As quatro referências atuais incluem efeitos originais: não usar caudas reverberantes como constantes de corda.
- [ ] Fazer comparação A/B nivelada e auditiva; se o modelo soar como violão, sino ou órgão, não promover para a versão estável.

## Prioridade 3 — Testes mensuráveis antes de nova versão

- [ ] Reusar ou aperfeiçoar `timbre_scorecard.py` e `piano_partials.py` da auditoria Claude disponível no projeto; validar inarmonicidade, brilho por velocity e decaimento por parcial.
- [ ] Cobrir graves/médios/agudos e toque suave/médio/forte com notas isoladas **quando existirem referências secas confiáveis**; as capturas de apresentação não são equivalentes.
- [ ] Medir RMS, picos, clipping, notas presas, mensagens MIDI (incluindo CC64), CPU por bloco e estouros de prazo de áudio.
- [ ] Passar pelos testes existentes e testar em PC/Moto g04s real.
- [ ] Publicar versão experimental isolada para avaliação, com URL/commit verificados; promover apenas se estabilidade e timbre forem melhores.

## Trabalho posterior (não prioritário até estabilizar piano)

- [ ] Recalibrar Rhodes MK I/II, Wurly 140B/200A, Clavinet, CP70 e E. Piano 1/2/3 com as nove capturas.
- [ ] Confirmar migração da nomenclatura dos elétricos em qualquer eventual atualização do app principal.
- [ ] Instrumentação de desempenho visível ao usuário (redução de ganho, carga de áudio/voz), desde que não piore a CPU.

## Como fechar uma etapa

Registrar em `docs/ESTADO_ATUAL.md`: **commit, pasta, mudança real, testes executados, resultado em hardware, risco restante e local de publicação**. Se faltar uma evidência, declarar pendência, não marcar como concluída.

## Próxima ação técnica recomendada

**Localizar a fonte exata do Novo Stage e comparar sua arquitetura com o protótipo mecânico v1.12.1 antes de fazer merge**, mantendo a v1.9.5 como regressão de estabilidade. Se a fonte não estiver disponível, estudar/adaptar a integração em uma nova pasta experimental baseada em código realmente acessível, sem chamá-la de integração ao Novo Stage.

## Execução em 22/11/2026 — acoplamento em base acessível

- [x] Criar experimento **v1.12.2** baseado na v1.9.5 com ponte, tampo e cordas simpáticas processados no mesmo AudioWorklet, com realimentação limitada e bypass A/B.
- [x] Integrar CC64, estados de amortecedores e testes de notas repetidas; rodar 76 testes e benchmark offline com 32/64 vozes.
- [ ] Validar Audioworklet real no navegador do usuário e ouvir A/B em PC e Moto g04s; confirmar que não surgiram novos estalos.
- [ ] **Recuperar a fonte exata do Novo Stage v1.11.0** para portar a integração sem quebrar seu comparador Claude/Stage.
- [ ] Corrigir inarmonicidade e decaimento dependente da frequência; pontuação do scorecard anterior não demonstra realismo.
- [ ] Calibrar auditivamente com notas secas e os quatro WAVs disponíveis como referência final (efeitos originais inclusos).
