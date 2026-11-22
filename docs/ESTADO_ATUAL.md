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
