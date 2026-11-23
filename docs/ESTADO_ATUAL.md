## Qualificação científica das referências sonoras (22/11/2026)

A comparação E0 de 33 amostras foi revisada: falta sincronização de dinâmica física, mic, sala e condições de gravação; **não tratar seus valores em dB como nota de realismo nem usar como único alvo de DSP**. Foram localizadas fontes experimentais mais apropriadas: **BiVib Yamaha cauda/vertical, 10 velocities × 88 notas, WAV 96k/24b e metadados binaurais/calibração**; **RWC Yamaha/Steinway/Bösendorfer reais, 3168 sons com estilos/pedal e três dinâmicas**; **MAPS Yamaha Disklavier real com close/ambient**; **MAESTRO** para desempenho musical e pedais. Todas exigem respeitar licença de uso não comercial e restrições próprias; nenhum novo áudio foi baixado nem incorporado.

Catálogo com fontes, critérios e o plano E1: docs/AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md. A P1 continua isolada; v1.9.5 está preservada, sem mudanças nos motores A/B/C.

---

## E0 — comparação de áudio real dos quatro pianos (22/11/2026)

Na branch de pesquisa E0 foi implementado um procedimento de CI que **baixou e analisou efetivamente 33 gravações isoladas** de Yamaha C5, Steinway B, Felt Fuchs & Möhr e Upright Knight (amostras AIFF/WAV/AAC em /tmp somente). Nenhum sample foi incorporado ao GitHub, à aplicação ou ao artifact: somente proveniência e métricas JSON. A análise foi comparada a todos os motores A/B/C em 48 kHz, sem FX, mantendo DSP original e a v1.9.5. O resultado aponta forte diferença de amplitude relativa de parciais nos graves B/C, mas não é uma avaliação subjetiva de realismo; pp/mf/ff e níveis AAC não representam um velocity MIDI comum. Notas com menos de três parciais detectáveis têm estimativa de B nula. A nova observação espectral curta de ataque busca reduzir falsos negativos em C6 sem tratá-la como rigidez de corda.

Detalhes e cautelas: docs/ANALISE_AUDIO_REAL_E0.md. A meta 32/64, áudio real em PC/Moto g04s e o experimento isolado P1 permanecem sem homologação.

---

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

## Pesquisa aprofundada de física de piano (22/11/2026)

Estudo científico/arquitetural de martelo, cordas rígidas e acopladas, ponte/tampo, radiador e amortecedores: docs/FUNDAMENTOS_MODELAGEM_FISICA_PIANO_2026-11-22.md. **Sem alterações do DSP ou do aplicativo.** O experimento P1 de duas seções allpass continua isolado no PR #2 e não é versão integrada. A próxima implementação exige calibração com notas secas licenciadas e comparação auditiva, preservando v1.9.5/32–64 notas.

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

## Pesquisa P0 — baseline acústica A/B/C (branch experimental, 22/11/2026)

Na branch research/piano-acoustic-metrics-v124, derivada do main bcfb40a8, foram adicionados analisador FFT/inharmonicidade/decaimento, testes unitários, diagnóstico reproduzível de 108 casos A/B/C e workflow CI; consultar docs/BASELINE_ACUSTICA_V124.md. **Não há alteração de DSP, interface, presets nem publicação do aplicativo.** Os 5 testes locais isolados do analisador passaram; a suíte integrada, artefato de diagnóstico e teste em hardware dependem de conferência do workflow. A v1.9.5 permanece a referência relatada sem estalos; não promover a branch automaticamente.

---

# Atualização do aplicativo principal — Stage Synth v1.12.4 (22/11/2026)

**Confirmado no código publicado:** o módulo Piano Acústico possui três implementações selecionáveis em **Motor do piano**, sem módulos ou links extras.

- **A · Claude (modal):** implementação modal adaptada já presente em `piano-worklet.js`. O código externo original do Claude não foi recuperado independentemente.
- **B · Stage físico anterior (v1.9.5):** arquivo histórico de DSP `experimental/physical-v1.9.5/physical-piano.js`, incluído como `physical-piano-legacy.js` num AudioWorklet próprio (somente o identificador do processador mudou). É a base com estabilidade relatada no PC.
- **C · Novo Stage mecânico:** motor integrado v1.12.3, com ponte/tampo/cordas simpáticas. Seleção `physical` antiga continua apontando para C.
- A síntese clássica continua disponível para compatibilidade.

**Não confundir B com o Novo Stage original v1.11.0 de outra conversa:** a fonte exata da v1.11.0 continua ausente deste repositório. A inclusão de B fornece uma comparação verificada, não reproduz a versão externa.

Testes locais: **84 testes Node aprovados**, testes de seletor em navegador simulado desktop/Android aprovados, sem novo módulo. O ambiente de Chromium bloqueou navegação localhost para validar os três AudioWorklets reais. O desempenho e a fidelidade ainda exigem validação no PC e Moto g04s.

Os WAVs de referência permanecem privados. As versões experimentais anteriores não foram apagadas.

---

# ATUALIZAÇÃO CONFIRMADA — 22/11/2026: v1.12.3 integrada ao aplicativo principal

O código da **raiz de main** agora é **v1.12.3**, com seleção A/B no **módulo Piano Acústico → Motor do piano**. Substitui o diagnóstico anterior de raiz v1.8.4 (mantida no histórico Git). A, modal derivado da linha Claude; B, motor físico **baseado na v1.9.5 + mecânica v1.12.2**. Não se trata da fonte original da linha separada Novo Stage v1.11.0.

A v1.9.5 experimental permanece a **referência estável comprovada pelo usuário sem estalos**. A nova v1.12.3 exige verificação auditiva e de latência no PC e Moto g04s. Nenhum novo módulo ou link externo foi acrescentado; atalhos anteriores removidos. 79 testes de lógica aprovados e interface testada em Chromium simulado, sem homologação do AudioWorklet real.

---

# Stage Synth — estado real do projeto

**Última conferência:** 22/11/2026. Verificar novamente o GitHub antes de começar qualquer nova tarefa; este documento não é uma consulta automática ao HEAD.

## Mapa das linhas de desenvolvimento

| Linha | Local no repositório | Estado |
|---|---|---|
| Site principal | raiz de `main` | `package.json` = **v1.8.4**; app principal publicado pelo GitHub Pages a partir da raiz. Perfil móvel originalmente limita a 8 vozes nesta linha. |
| Piano físico estável para o usuário | `experimental/physical-v1.9.5/` | O usuário relatou **eliminação dos estalos no PC**. É estabilidade **relatada em campo**, não garantia de desempenho em todos os dispositivos. |
| Piano físico v1.9.6 | `experimental/physical-v1.9.6/` | Novo ataque de martelo experimental; a fidelidade ainda foi considerada insuficiente. Auditoria acústica apontou problemas fundamentais. |
| Pesquisa acústica posterior | `experimental/mechanical-resonance-v1.12.1/` | **Protótipo independente**, com ponte/tampo/cordas simpáticas e retorno limitado às cordas. Não é um piano completo nem foi integrado ao Novo Stage. |
| "Novo Stage v1.11.0" de outra conversa | **Fonte ainda não localizada neste repositório** | Há relato de tampo estéreo com duas zonas de escuta/excitação, mas o código-fonte daquela linha precisa ser obtido/identificado antes de integrar módulos. Não inventar uma integração. |
| Outras versões de piano | `experimental/physical-v1.9.0/` a `physical-v1.9.4/` | Histórico de experimentação e comparações. Não substituir nem apagar. |

**Distinguir:** "versão principal" (raiz), "versão sem estalos segundo o usuário" (v1.9.5 experimental) e "experimento de DSP mais recente no repositório" (v1.12.1). Não há uma v1.12.1 pronta para tocar neste momento.

## Escopo funcional conhecido

O aplicativo possui seis módulos: Piano Acústico (Japanese, American, Felt, Upright), Piano Elétrico, Órgão, Synth, Leitor SF2 e rack de FX, além de recursos MIDI e controles de performance. Histórico e diferenças por versão estão nos respectivos `README.md` e `CHANGELOG.md`. **A presença de uma função numa pasta experimental não prova sua presença no site principal.**

## Requisitos de áudio confirmados

- **O problema prioritário atual é a falta de fidelidade dos quatro pianos acústicos.**
- Os estalos do PC foram relatados como resolvidos na v1.9.5; preservar essa base enquanto novos modelos são comparados.
- **Mínimo desejado: 32 notas. Meta: 64 notas.** São critérios de aceitação, não capacidades confirmadas em todos os modos.
- O Moto g04s é alvo de otimização; o desempenho do AudioWorklet completo ainda exige validação nesse dispositivo real.
- O usuário considera o som de corda isolada insuficiente: faltam martelo, mecanismo, amortecedores, interação entre cordas, ponte/tampo e caixa/radiação.

## Evidências técnicas disponíveis

- `docs/VERIFICACAO_CLAUDE_PIANO_V196_2026-11-22.md`: auditoria externa reproduzida; v1.9.6 físico **2/5** no scorecard acústico aproximado, modal **5/5**, mas o modal nessa implementação fica limitado a 32 vozes; critérios não provam realismo.
- `docs/PLANO_FIDELIDADE_PIANOS_APOS_V195.md`: diagnóstico do motor e orçamento de desempenho.
- `docs/CAPTURAS_QUATRO_PIANOS_2026-11-22.md`: WAVs sincronizados Japanese/American/Felt/Upright, **com efeitos originais**, usados para referência do som final; não são medições secas de notas isoladas.
- `docs/CAPTURAS_NOVE_PIANOS_ELETRICOS_2026-11-22.md`: referências de 9 elétricos, também sem publicar os WAVs.
- `experimental/mechanical-resonance-v1.12.1/README.md`: limitações e testes do acoplamento. Os benchmarks representam **cordas de teste simplificadas**, não 64 vozes reais do aplicativo.

## Últimos fatos confirmados nesta organização

- A raiz de `main` possui `package.json` **1.8.4** e a pasta `experimental/` contém as versões 1.9.0 a 1.9.6 e o protótipo 1.12.1.
- Workflow do GitHub Pages da versão anterior a esta organização concluído com sucesso; confirmar novamente os próximos deploys.
- Não foi feito merge do núcleo mecânico v1.12.1 para o sintetizador principal.
- Estes documentos de governança **não alteram o DSP**, o visual, presets ou MIDI.

## Como atualizar este arquivo

Após uma entrega, acrescentar: **versão/pasta + commit SHA + mudança real + testes executados + teste em hardware (se houver) + link de publicação confirmado + limitações abertas**. Não apresentar benchmark offline como desempenho garantido no celular.

## Atualização experimental v1.12.2 — 22/11/2026

- **Novo experimento executável:** `experimental/physical-mechanics-v1.12.2/`. É uma integração do núcleo `mechanical-resonance-v1.12.1` no AudioWorklet físico **baseado na v1.9.5**, não um merge no Novo Stage v1.11 de outra conversa (fonte ainda ausente do repositório).
- **Integração:** feedback mecânico limitado devolvido à corda no próximo sample, 88 estados de amortecedores, CC64, corpo estéreo, cordas simpáticas e seletor A/B `Acoplamento mecânico`.
- **Validação:** 76 testes automatizados de lógica passaram; interface validada em desktop e Android simulado. Testes de 32 e 64 notas sem clipping offline; bypass A/B com saída original idêntica quando desligado. Benchmark Node offline aproximado: 32 vozes 77→91 ms/1s; 64 vozes 219→246 ms/1s. São números de computador de testes, **não** homologação em hardware do usuário.
- **Pendente:** Chrome AudioWorklet real bloqueado neste ambiente (localhost `ERR_BLOCKED_BY_ADMINISTRATOR`), comparação auditiva com as quatro referências, testes reais no PC/Moto g04s e obtenção do código do Novo Stage v1.11.
- **Não houve substituição da raiz v1.8.4 nem da base estável relatada v1.9.5.**


## Correção de acesso ao experimento v1.12.2 (22/11/2026)

O aplicativo principal na raiz ainda é v1.8.4; a implementação do acoplamento mecânico **não está incluída nesse motor**. Para eliminar confusão, foi adicionado na página principal um link explícito para `experimental/physical-mechanics-v1.12.2/acesso-motor-v1.12.2.html` e, no experimento, um botão **Ativar piano mecânico** que seleciona a síntese física, ativa acoplamento, abre o editor do piano e tenta iniciar o AudioWorklet.

O endereço separado também evita reutilizar a página anterior do navegador. A existência do botão e o estado selecionado foram testados em Chromium simulado; a inicialização real do AudioWorklet ficou bloqueada pela origem de teste. A ativação em Chrome real e a audição no PC/Moto g04s continuam pendentes de confirmação do usuário.
