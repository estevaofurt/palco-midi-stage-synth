## AVANÇO DE REFERÊNCIAS COMERCIAIS — NÃO LIBERAR DSP (22/11/2026)

Há um **piloto de proveniência aprovado**: 28 arquivos originais de piano real (8 WAV VCSL CC0; 15 FLAC Salamander Yamaha C5 CC BY 3.0; 5 FLAC Kawai Upright KW CC0), SHA256 individual, fonte pinned por SHA Git e codec verificado em CI. Ver research/commercial_audio/verified_source_sha256.json e docs/PREPARACAO_FONTES_COMERCIAIS_PILOTO_2026-11-22.md. Os arquivos não são distribuídos nem guardados no repositório.

**Não confundir** esse avanço com parâmetro físico pronto: Steinway VCSL normalizado, Yamaha v1/v8/v16 não é hammer velocity em m/s, Kawai contém loops graves. **Ainda 0/7 R-GATEs integralmente aprovados** e projeto comercial; manter PROIBIDA a implantação de P1/P2 ou alteração de DSP, MIDI, UI, FX e presets, até referência física e licença completa e aprovação explícita do usuário.

---

## FINALIDADE COMERCIAL — restrição obrigatória de fontes e código (22/11/2026)

**Decisão expressa do titular:** o Stage Synth é um **produto destinado à comercialização**, não um instrumento acadêmico/pessoal. Essa finalidade prevalece sobre classificações antigas da pesquisa.

- **Não usar** áudios, MIDI, dados de calibração ou código de terceiros com licença **NC/research-only/uso pessoal** no pipeline do software comercial sem **autorização comercial explícita** e comprovada. LER artigos e aprender princípios científicos continua permitido; não confundir artigo com direito de usar o dataset.
- Priorizar corpus próprio com contrato de uso comercial, **CC0, CC BY 3.0/4.0** com atribuições, domínio público comprovado e permissões explícitas para qualquer projeto (por exemplo, texto do acervo Iowa). Cada arquivo exige prova de origem/licença e revisão do caso concreto.
- **BiVib, RWC, MAPS e MAESTRO NÃO estão liberados** para calibração do produto sob as condições NC conhecidas. Não aceitar a ausência dos arquivos no pacote final como prova de autorização para treinamento ou calibração.
- Software comercial não significa automaticamente **código fechado**; a licença do próprio Stage é decisão do titular. Não existe LICENSE na raiz nesta auditoria e a propriedade/licença de cada dependência, código adaptado, modelo e recurso sonoro ainda precisa ser revisada.
- Não usar marcas (Yamaha/Steinway) ou modelos como se houvesse endosso do fabricante, nem copiar amostras de produtos comerciais sob EULA. Nenhum DSP/P1/P2 novo enquanto os sete R-GATEs não estiverem efetivamente comprovados e o usuário não autorizar retomada.

**Fonte da política:** docs/POLITICA_COMERCIAL_DADOS_LICENCAS_2026-11-22.md. Manter inalterado o bloqueio anterior de implementação.

---

# Stage Synth — Instruções compartilhadas para IAs e colaboradores

**Projeto:** `estevaofurt/palco-midi-stage-synth`  
**Idioma de trabalho:** português (Brasil).  
**Data de adoção deste protocolo:** 22/11/2026.

## BLOQUEIO EXPLÍCITO — fontes ainda não preparadas (22/11/2026)

**Pedido mais recente do usuário:** NÃO prosseguir com programação, alterações de timbre, nova arquitetura P2 ou merge de P1 no módulo Piano enquanto não estiverem reunidas e verificadas as referências essenciais para as lacunas de modelagem física.

**Estado atual: NÃO PRONTO**, conforme docs/PRONTIDAO_REFERENCIAS_PIANO_FISICO_2026-11-22.md (22 referências/famílias auditadas, 18 lacunas relacionadas, 7 critérios R-GATE-1..7 ainda não aprovados). É permitido realizar **somente pesquisa, auditoria de metadados/licenças, organização e aquisição legítima de dados originais e documentação** até o usuário expressamente autorizar retomada após a checagem completa.

DOI/artigo encontrado não significa sinal original verificado; não assumir como prontos BiVib/RWC/Plath/QMUL/bitKlavier, nem afirmar que parâmetros estão identificados apenas por uma gravação. **NÃO integrar P1/P2, não alterar A/B/C, presets, módulos, MIDI e efeitos** durante o congelamento. Mantemos a referência histórica B v1.9.5 preservada.

---

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
