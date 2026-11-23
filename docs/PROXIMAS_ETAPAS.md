## Referências sonoras verificadas para os quatro pianos (22/11/2026)

Catálogo detalhado em [REFERENCIAS_SONORAS_YAMAHA_STEINWAY_FELT_UPRIGHT_2026-11-22.md](REFERENCIAS_SONORAS_YAMAHA_STEINWAY_FELT_UPRIGHT_2026-11-22.md).

- Yamaha: Salamander Grand Piano **Yamaha C5 real**, 16 intensidades CC BY 3.0; **CFX** GSi Venice Grand apenas para referência perceptiva até conseguir arquivos brutos licenciados.
- Steinway: Universidade de Iowa **Model B**, notas AIFF individuais pp/mf/ff e site de permissão sem licença SPDX; Ivy Piano in 162 com 5 camadas, 2 posições e pedal up/down, uso de amostras limitado aos termos da biblioteca.
- Felt: Fuchs & Möhr felt upright de Tom Guder, 3 camadas WAV estéreo, declarado domínio público pelo autor.
- Upright: FreePats Kawai KW, 2 intensidades, CC0 1.0; graves editados com loop, **não adequados para T60 real**.
- [ ] Adquirir e verificar localmente pequenos subconjuntos de notas, medir metadados e licenças. NENHUM arquivo de som foi incluído no GitHub.
- [ ] Alinhar C2/C4/C6 e intensidades reais dos bancos, sem atribuir velocities MIDI fictícias a pp/mf/ff. Medir canais, ataque, parciais, B e decaimentos, verificando reverb e loops.
- [ ] Comparar A/B/C com áudio nivelado e laboratório de CPU antes de qualquer modificação de timbre.

**Nenhum DSP, interface, módulo, preset, áudio de terceiros ou conteúdo privado do usuário foi alterado/publicado nesta pesquisa.**

---

# Estudo aprofundado de modelagem física — pesquisa, sem DSP (22/11/2026)

Documento: [FUNDAMENTOS_MODELAGEM_FISICA_PIANO_2026-11-22.md](FUNDAMENTOS_MODELAGEM_FISICA_PIANO_2026-11-22.md).

- [x] Revisar literatura fundamental sobre colisão do martelo, rigidez/damping da corda, duas polarizações, acoplamento de uníssono, prompt/aftersound, ponte, tampo, abafadores, ressonância simpática e radiação acústica.
- [x] Analisar arquitetura modal de Bank (2010), simulação acoplada de Chabassier (2014) e documentação do Unsampled Piano (2026); diferenciar código aberto GPL de informações públicas comerciais.
- [x] Auditar lacunas existentes nos motores A/B/C; confirmar que o P1 em PR #2 permanece fora de main.
- [ ] **E0:** obter referência seca autorizada por nota, velocidade e estado dos pedais; as capturas atuais com FX não são suficientes para identificar constantes físicas.
- [ ] **E1:** medir por nota B, cents, amplitudes e decaimentos por parcial com método mais robusto que uma FFT fixa.
- [ ] **E2:** prototipar contato martelo-corda com solução offline e famílias **sintéticas** de força por velocity, medindo custo e dinâmica.
- [ ] **E3:** testar 1–3 cordas, duas polarizações e ponte compartilhada em pequena prova física, com diagnóstico de energia/passividade e double-decay.
- [ ] **E4:** comparar tampo/radiação por regiões e localização de microfones, separando corpo e reverb de sala; validar controles CC64/release.
- [ ] **E5:** comparar arquiteturas modal, waveguide e híbrida em áudio nivelado, sem promover motor por um único scorecard.
- [ ] **E6:** homologar 32/64 notas em Chrome real, PC e Moto g04s, com efeitos, MIDI, pedal, picos e estabilidade.
- Nenhum novo link, módulo, motor ou preset foi integrado ao aplicativo. Nesta etapa, **apenas pesquisa e documentação**.

---


## Resultados P0 verificados no GitHub Actions (22/11/2026; UTC da execução em 23/11)

- Commit de diagnóstico: 2b27cf51ed921ab2254ed3a5af2b26126752c063.
- Workflow: https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45094083550 — **90/90 testes Node aprovados, 0 falhas**.
- Matriz completa: **108/108 combinações renderizadas**, sem clipping ou amostras não finitas no sinal seco médio (FX desligados). JSON disponível como artifact do workflow por 14 dias.
- Japanese / velocidade 80: estimativa B por FFT em C2, C4, C6:
  - A modal: 0,00024496; 0,00035775; 0,00148165.
  - B waveguide v1.9.5: 0,00005294; 0,00010944; 0,00027679.
  - C acoplado: 0,00005478; 0,00011025; 0,00027700.
- B e C têm estimativas de inarmonicidade e níveis RMS muito semelhantes nessa condição; **o acoplamento mecânico não resolveu a dispersão original das cordas**. Isso não prova que os sons sejam perceptualmente idênticos.
- Não declarar B-alvo universal com base nesses números: FFT finita, ajustes de modelo, perfis de registro, batimentos e sinais fracos podem enviesar a estimativa. É necessário comparar com referência seca autorizada e escuta nivelada.
- **Recomendação P1:** modificar dispersão e perdas dependentes de frequência **em branch experimental isolada**, mantendo B v1.9.5 e A/C atuais como referência. Atingir 32/64 vozes em hardware continua pendente.

---

# P0 em implementação isolada — baseline acústica (22/11/2026)

- [x] Criar branch separada sem modificar os DSPs estáveis.
- [x] Adicionar medidas FFT de cents, B estimado, parciais, ataque, decaimento, clipping e amostras não finitas; 5 testes unitários locais passaram.
- [x] Preparar comparação reproduzível de 108 casos A/B/C × 4 pianos × C2/C4/C6 × velocity 32/80/120.
- [x] Conferir workflow de regressões: 90/90 testes; 108/108 renders concluídos; 0 clipping/NaN no sinal seco, artifact preservado.
- [ ] Examinar números do JSON por registro e dinâmica; B é estimativa e não alvo universal.
- [ ] P1: corrigir dispersão/perdas por frequência **somente num experimento isolado**, reexecutar regressões e comparação sonora nivelada.
- [ ] Testes em Chrome real, PC e Moto g04s, com 32/64 vozes, MIDI/CC64 e FX; não anunciar homologação antes.

Documentação: docs/BASELINE_ACUSTICA_V124.md. Não há alteração de motor/presets no aplicativo.

---

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
