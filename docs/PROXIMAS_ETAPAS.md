# Pesquisa externa concluída — 22/11/2026

- [x] Referências científicas/comerciais/código aberto reunidas e mapeadas para os motores **A (modal), B (físico v1.9.5) e C (mecânico)**.
- [x] Documento: [`REFERENCIAS_EXTERNAS_FIDELIDADE_MOTORES_2026-11-22.md`](REFERENCIAS_EXTERNAS_FIDELIDADE_MOTORES_2026-11-22.md).
- [ ] **Próxima implementação P0:** suíte acústica de múltiplas notas/velocities com B, cents, dois tempos de decaimento, ganho por parcial, brilho por força e teste de clipping.
- [ ] **P1 B/C:** corrigir inarmonicidade insuficiente com dispersão allpass calibrada e filtro de perda por frequência; não compensar H2 apenas com ganho artificial.
- [ ] **P2 A:** ampliar capacidade modal 32→64 vozes somente se os testes de realismo/desempenho justificarem.
- [ ] **P3–P4:** modelo de ataque comutado + tampo/pedal compartilhados; validar benefícios audíveis e custo de CPU.
- [ ] Não promover novo DSP antes de comparação A/B nivelada e teste real no PC/Moto g04s. A v1.9.5 continua disponível para regressão.
- **Nesta entrega foi feita apenas pesquisa/documentação; nenhum DSP, seletor ou preset foi alterado.**

---

# Atualização da comparação v1.12.4 (22/11/2026)

- [x] A modal, B Stage físico histórico v1.9.5 e C Stage mecânico selecionáveis no mesmo módulo Piano Acústico.
- [x] B usa arquivo DSP independente recuperado, sem duplicar o motor C.
- [x] Manter preferência salva e disponibilizar alternativa clássica.
- [x] 84 testes automatizados e regressão de interface PC/celular simulados.
- [ ] Recuperar **código exato do Novo Stage v1.11.0**, original de outra conversa; não confundir com v1.9.5.
- [ ] Testar AudioWorklets reais, troca de motores e MIDI em Chrome do usuário, com FX e sustain.
- [ ] Calibrar inarmonicidade, contato do martelo e ressonância com notas isoladas; não promover apenas por scorecard.
- [ ] Medir 32 notas no Moto g04s e 64 no PC, sem estalos.

---

# Atualização de execução — v1.12.3 integrada (22/11/2026)

- [x] Integração do motor B físico + acoplamento mecânico ao app principal, selecionável no módulo Piano Acústico.
- [x] Comparação A (modal derivado da linha Claude) / B (Novo Stage mecânico) no mesmo editor.
- [x] Retirados novos banners e links externos; sem módulos adicionais.
- [x] Testes automatizados (79) e testes do seletor em navegador simulado.
- [ ] Testar **AudioWorklet real**, estabilidade e latência no PC e no Moto g04s; não confundir simulação com homologação.
- [ ] Recuperar e comparar código original da linha Novo Stage v1.11.0, que não foi usado nesta implementação.
- [ ] Corrigir inarmonicidade, decaimento espectral e realismo do timbre, mantendo estabilidade comprovada da v1.9.5.

---

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
