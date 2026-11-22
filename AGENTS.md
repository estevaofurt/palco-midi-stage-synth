# Stage Synth — Instruções compartilhadas para IAs e colaboradores

**Projeto:** `estevaofurt/palco-midi-stage-synth`  
**Idioma de trabalho:** português (Brasil).  
**Data de adoção deste protocolo:** 22/11/2026.

## Objetivo

Desenvolver um instrumento MIDI com módulos de piano acústico, elétrico, órgão, sintetizador, SoundFont e efeitos. Priorizar **fidelidade sonora, estabilidade em tempo real e consumo compatível com hardware modesto**, especialmente Moto g04s.

Este repositório é a **fonte de verdade para código e decisões documentadas**, mas **não sincroniza automaticamente conversas do ChatGPT, Claude ou de outros assistentes**. Qualquer mudança decidida em outra conversa só passa a ser compartilhada ao ser registrada nos arquivos corretos e, quando aplicável, implementada e verificada no código.

## Antes de propor ou editar código

1. Conferir o HEAD atual, a estrutura do repositório e `package.json`, identificando o código servido pela raiz e o código em `experimental/`.
2. Ler `docs/ESTADO_ATUAL.md`, `docs/DECISOES.md`, `docs/PROXIMAS_ETAPAS.md` e a documentação técnica relevante.
3. Confirmar o que está **implementado**, **testado**, **publicado** e **validado em hardware**; não confundir esses estados.
4. Examinar alterações e branches/commits posteriores aos documentos. Se houver divergência, atualizar a documentação antes de partir de suposições.
5. Diferenciar o **Stage Synth principal na raiz**, os experimentos `physical-v1.9.x`, o protótipo `mechanical-resonance-v1.12.1` e quaisquer fontes externas da linha "Novo Stage". **Não presumir que o código v1.11 esteja neste repositório.**
6. Verificar requisitos de migração, dados/presets já armazenados em navegadores, compatibilidade, UI existente e rotas de publicação.

## Regras de implementação

- **Preservar o comportamento estável:** o usuário relatou desaparecimento dos estalos no PC ao testar a v1.9.5 experimental. Não introduzir regressões; não promover uma nova versão à principal sem validação.
- **Polifonia:** mínimo funcional desejado de **32 notas** e meta de **64**, com teste no PC e Moto g04s. **Os limites atualmente implementados variam por versão e perfil** — não anunciar garantia de 32/64 em todos os dispositivos sem medição real.
- **Realismo de piano:** priorizar ataque de martelo, inarmonicidade, perdas/decadência por parcial, cordas acopladas, abafadores, ponte, tampo, ressonância simpática e radiação sonora; evitar compensações arbitrárias com EQ ou um único harmônico.
- **Custo do DSP:** evitar alocações por bloco do AudioWorklet, criar FX pesados sob demanda, limitar realimentação, fazer testes de clipping, underrun/estalos e MIDI com sustain e acordes densos.
- **Experimentos isolados** até comparação A/B e regressão. Não sobrescrever a versão que o usuário consegue tocar.
- **Testar antes de afirmar:** usar `npm run check`/`npm test` nas pastas pertinentes e testes no navegador quando disponíveis; declarar explicitamente o que não pôde ser testado.
- **Áudio de referência:** arquivos `Japanese.wav`, `American.wav`, `Felt.wav`, `Upright.wav` e nove elétricos foram fornecidos para comparação, com efeitos originais; **não enviar os WAVs ao repositório público** nem embuti-los como samples sem direitos explícitos. São referências do timbre final, não automaticamente de uma nota seca.
- **Publicação:** verificar SHA de commit, execução do workflow de Pages e, quando possível, URL pública real antes de declarar "publicado". Um link 404 ou uma ação em fila não é publicação validada.
- **Controle de versão:** preservar histórico, criar backup versionado quando houver entrega e atualizar documentação na mesma mudança.
- **Alterações em GitHub:** revisar head atual antes de gravar; usar commits pequenos/atômicos ou PRs. Nunca substituir arquivos de outro experimento por engano.

## Após cada trabalho

Atualizar, conforme aplicável:
- `docs/ESTADO_ATUAL.md`: o que foi implementado, versão, commit, testes, lacunas e status de implantação.
- `docs/DECISOES.md`: decisão de produto/arquitetura duradoura e sua justificativa.
- `docs/PROXIMAS_ETAPAS.md`: prioridades, bloqueios e próximos critérios de aceite.
- `CHANGELOG.md` no código efetivamente alterado, quando houver mudança de comportamento.

Se a IA não puder escrever no GitHub, apresentar o texto/patch para registro posterior; **não afirmar que a documentação está sincronizada**.

## Documentos de referência

- `docs/PLANO_FIDELIDADE_PIANOS_APOS_V195.md`
- `docs/VERIFICACAO_CLAUDE_PIANO_V196_2026-11-22.md`
- `docs/CAPTURAS_QUATRO_PIANOS_2026-11-22.md`
- `docs/CAPTURAS_NOVE_PIANOS_ELETRICOS_2026-11-22.md`
- `experimental/mechanical-resonance-v1.12.1/INTEGRACAO_NOVO_STAGE.md`
