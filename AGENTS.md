## ESCUTA E1.4 REPROVOU GANHO PERCEPTIVO DO MARTELO GRAVE D v1.12.7 (23/11/2026)

**Veredicto do proprietário:** depois de ouvir WAVs reais 48k/24-bit de D v1.12.6 e D v1.12.7, inclusive versão intercalada por nota, **“não existem diferenças perceptíveis entre os dois modelos”**. **Tratar como hipótese sonora REPROVADA**, apesar da diferença transitória −4,38 dB nos primeiros 12 ms do C2 mf: corpo e cauda praticamente inalterados. O motor D ainda faz saída direta da soma modal + corpo wet e **não realimenta os modos por `PianoResonanceBody.reaction`**, embora o corpo calcule esse estado. Esta lacuna deve orientar a próxima pesquisa sobre acoplamento físico/radiação, sem alegar causalidade perceptiva demonstrada. **Não repetir versões que só troquem o ataque, não reintegrar PR #26 “wood”/longitudinal, não promover D 1.12.7 como melhor timbre**. [Relatório completo](docs/REPROVACAO_PERCEPTIVA_MARTELO_D_V127_2026-11-23.md). Manter DSP/versão atual e histórico 1.12.6, outros motores, C4–C6, MIDI/FX/presets/UI intactos até referência física/comercial e ganho sonoro validado; **0/7 R-GATEs**, 32–64 vozes não aprovadas em hardware.

---

## E1.2 — IOWA 15/15: NÃO HÁ ERRO DE OITAVA COMPROVADO, PRESERVAR DSP (23/11/2026)

Após E1.1, a auditoria focada da matriz de **15 AIFF originais Steinway B/Iowa** confirmou hash/tamanho/codec e testou rótulo de nota independentemente por **YIN temporal em duas janelas** e **FFT harmônica**. [CI 45178612159](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45178612159): **157/157 testes Node**, 6/6 YIN e 4/4 harmônicos; **12/15 consistente nos dois métodos** e **3 inconclusivos** (C2 pp/ff, C6 pp). Zero erros de oitava corroborados. Nenhum dado físico de martelo/ponte, acústica de madeira ou realismo foi demonstrado; não alterar notas/seletores, parâmetros D ou propriedades de piano por conjectura. [Relatório](docs/AUDITORIA_AFINACAO_IOWA_ORIGINAIS_2026-11-23.md). Motores A/B/C/D, versão pública v1.12.7, C4–C6, MIDI, CC64, FX, UI/presets e v1.12.6 histórico imutáveis; PR #26 reprovada; 0/7 R-GATEs, 32–64 vozes não homologadas no hardware.

---

## E1.1 — ESTIMATIVA RADIATIVA OFFLINE, SEM DADOS MEDIDOS E SEM NOVO TIMBRE (23/11/2026)

Após validar o solver passivo compartilhado na PR #28, a próxima etapa foi preparar um **estimador H1 de resposta complexa da aceleração de ponte (m/s²) à pressão aérea (Pa)** em `research/bridge-radiation-h1.mjs`. Testes com **sinais sintéticos**, sem qualquer instrumentação Yamaha/Steinway ou bytes de terceiros. O método usa Welch/coerência, rejeita frequências inválidas e exige que **sincronização, calibração e direitos comerciais** sejam comprovados externamente. H_pa NÃO é mobilidade mecânica `v_ponte/F_ponte`, nem autoriza inferir madeira/pressão completa a partir de `boardVelocity` normalizada. CI [E1.1 147/147 + 6/6](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45175445690), [baseline aprovado](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45175445415). [Documento](docs/VERIFICACAO_TRANSFERENCIA_RADIATIVA_H1_E11_2026-11-23.md). **Não alterar motores A/B/C/D/Clássico, DSP, UI, MIDI, FX, presets, versão nem licenças; Stage v1.12.7 permanece público, v1.12.6 para A/B, PR #26 reprovada, R-GATEs completos 0/7.** Meta 32–64 vozes só após testes em hardware real.

---

## PESQUISA DE PONTE/TAMPO PASSIVO COMPARTILHADO — SEM NOVA VERSÃO SONORA (23/11/2026)

Feedback recente do titular: quatro modelos A/B/C/D muito semelhantes, componente agudo parece ruído, som ainda "redondo" e lembra violão. **Não integrar PR #26**, que ficou como draft. O novo estudo está documentado em [docs/PRONTIDAO_PONTE_TAMPO_PASSIVO_V128_2026-11-23.md](docs/PRONTIDAO_PONTE_TAMPO_PASSIVO_V128_2026-11-23.md), implementado **somente em `research/`**, com testes e benchmarks. NÃO MUDAR `physical-piano-hybrid.js`, outros motores, painel, UI, MIDI, presets nem `package.json`; v1.12.7 permanece pública e v1.12.6 preservada para comparação.

O laboratório implementa `M x''+C x'+K x=F` com parâmetros positivos, integração de ponto médio implícito, balanço discreto energia-força-amortecimento e transferência corda→ponte→outras cordas. Otimizado para **dois modos de tampo compartilhados** e solução O(N) via complemento de Schur. CI 139/139 testes + 12/12 testes mecânicos dedicados, benchmark isolado p95 para 64 notas **0,156ms compartilhado vs 1,494ms por placa/nota**, **não** AudioWorklet real. **NÃO equivale a som melhor ou resposta de madeira identificada**: massas, rigidez e frequência de placa não medidas; saída é velocidade generalizada, **não pressão acústica**. Sem licença confirmada nos dados de Plath/IR Yamaha, não importar gravações ou parâmetros desses conjuntos. R-GATEs completos **0/7**.

---

## D v1.12.7 DISPONÍVEL SOMENTE COMO EXPERIMENTO DE GRAVE (23/11/2026)

O titular autorizou prosseguir com o plano depois da auditoria de algoritmo. O experimento v1.12.7 **altera apenas o motor D em MIDI 21–48**, com força de contato temporal por ressonadores e crescimento de radiação de grave, sem qualquer alteração ao caminho C4–C6 (MIDI >=49) nem A/B/C/Clássico, FX, MIDI, interface ou presets. A página histórica `v1.12.6.html` agora utiliza `acoustic-v126.js` e snapshots congelados do D v1.12.6 para **comparação auditiva verdadeira**; a v1.12.7 mantém uma única opção D no módulo Piano.

**Resultados originais Iowa (15 AIFF, SHA256) são MISTOS**: melhora de erro do envelope 0–12ms em C2/C3, **3,58→2,96dB**, mas piora no espectro integrado 3,23→4,30dB e espectro posterior 9,38→10,49dB. Portanto **não afirmar melhora geral, piano realista, modelo físico medido ou liberação comercial**. A avaliação auditiva do usuário com FX desligados é determinante para continuar ou reverter a v1.12.7. [Documento específico](docs/EXPERIMENTO_D_MARTELO_V127_2026-11-23.md). A/B/C e a v1.12.6 preservados. CPU 32/64 em hardware ainda não homologada; R-GATEs **0/7**.

---

## AUDITORIA DE ALGORITMO ANTES DE v1.12.7 (23/11/2026)

**Pedido atual:** revisar profundamente algoritmo físico e custo computacional, com fontes primárias, **sem prosseguir com DSP ainda**. Resultado e decisões: [docs/AUDITORIA_ALGORITMO_MOTOR_D_2026-11-23.md](docs/AUDITORIA_ALGORITMO_MOTOR_D_2026-11-23.md). Preservar explicitamente o D v1.12.6 nos médios/agudos, seus motores A/B/C/Clássico, UI, FX, MIDI e default. Não chamar regressão numérica de fidelidade sonora.

Principais lacunas confirmadas: vibrações longitudinais não modeladas, martelo tratado como ponderação inicial, ponte sem retorno físico ao modo e com unidades não calibradas; divisão de uníssono sem normalização coerente da potência; `bodyDivisor` eco declarativo mas ignorado; `v.brightness` sem efeito após note-on; PRNG calculado mesmo com ruído já decaído. **Antes de acrescentar processamento** usar benchmark Node `scripts/benchmark_piano_d_cpu.mjs` e **depois** perfil no browser Android/PC; os primeiros são só pistas de custo, não comprovação de 32/64 notas em tempo real. Gates integrais **0/7**.

---

## PROTEÇÃO DO TIMBRE MÉDIO-AGUDO / PLANO GRAVES D v1.12.7 (23/11/2026)

O titular ouviu D v1.12.6: **médio-agudo passou a parecer com piano real, mas grave ainda parece violão**. Preservar explicitamente o avanço de C4–C6 e os motores A/B/C/Clássico. A solicitação atual é **TERMINAR A PREPARAÇÃO** para a próxima versão, não substituir motores, adicionar menu, publicar versão nova ou mexer em DSP/FX/MIDI/UI/presets. Criar somente instrumentação, testes, documentos e CI com fontes verificadas; a v1.12.6 principal permanece intacta.

Diagnóstico/roadmap compacto: [docs/PRONTIDAO_GRAVES_MOTOR_D_V127_2026-11-23.md](docs/PRONTIDAO_GRAVES_MOTOR_D_V127_2026-11-23.md). Diferenciar primeiro choque 0–12ms, evolução dos parciais e radiação da ponte. **NÃO chamar 16.384 amostras @48 kHz de primeiros 18ms**: a FFT dura aproximadamente 341ms. Código confirmável: martelo atual não resolve força em tempo real; `PianoResonanceBody.reaction` não retorna a modos D; `single=key<37` tem fronteira fixa sem mapa de cordas confirmado. Essa é hipótese prioritária, não uma certeza subjetiva de causa. Sem importação de áudio e sem reutilização NC/AGPL, **0/7 R-GATEs fechados**, 32–64 apenas alocação.

---

## ITERAÇÃO V1.12.6 — REFINO DO D APÓS REPROVAÇÃO SONORA PELO TITULAR (23/11/2026)

Depois de ouvir o v1.12.5, o titular declarou que **o timbre ainda não se parece com um piano real** e pediu continuidade cuidadosa e máxima qualidade. A autorização específica anterior do D inclui **refinar somente o D experimental a partir de evidências verificáveis**, sem mexer em A/B/C, FX, MIDI, presets ou adicionar outros módulos. A v1.12.6 usa **15 AIFF originais Iowa/Steinway B com SHA256 conferido** para perfis NUMÉRICOS de radiação/ataque por registro/velocidade, no arquivo próprio `piano-hybrid-calibration.js`, sem armazenar samples.

As 15 mesmas referências usadas para calibrar mostram melhora do **erro de espectro de ataque 20,30→3,23 dB**, mas isso é in-sample e **não autoriza declarar piano realista, parâmetros físicos medidos, homologação comercial nem 32–64 vozes garantidas no hardware**. A versão permanece experimental, **0/7 gates completos**. Criar e passar testes de regressão, comparar com original e obter escuta do usuário antes de promover versão estável. Registro do [diagnóstico](docs/DIAGNOSTICO_TIMBRE_D_IOWA_15_2026-11-23.md), perfil [calibrado](piano-hybrid-calibration.js) e [documentação](docs/MOTOR_D_HIBRIDO_EXPERIMENTAL_2026-11-23.md).

---

## AUTORIZAÇÃO POSTERIOR E LIMITADA — MOTOR D EXPERIMENTAL (23/11/2026)

**Nova instrução expressa do titular:** “Vamos gerar um motor com o que temos até aqui”. Essa autorização posterior **permite desenvolver, integrar e testar somente um motor de piano experimental original**, selecionável **dentro do módulo Piano Acústico** ao lado de A Claude, B v1.9.5 e C Novo Stage; **não criar módulos/categorias/links adicionais**, não substituir A/B/C, não alterar o padrão de sessões antigas. Identificação de release: **Stage v1.12.5, D · Stage híbrido**. Documentar hipóteses e limites, executar regressão Node e baseline offline. Não usar dados NC nem copiar código AGPL de terceiros.

**Os sete R-GATEs NÃO estão automaticamente aprovados** e nenhum desempenho de 32/64 vozes em hardware ou fidelidade acústica real está demonstrado. Essa autorização pontual **supera o bloqueio anterior apenas para o protótipo D**, mas não libera alterações indiscriminadas a DSP dos motores A/B/C, presets, efeitos, MIDI ou demais módulos. O trabalho posterior deve continuar por etapas com GitHub/CI e escuta real do usuário antes de promover D a motor estável.

---

## NOVA PRIORIDADE: FECHAR, NÃO AMPLIAR A PESQUISA (23/11/2026)

Plano operacional curto: `docs/PLANO_ENXUTO_FECHAMENTO_LACUNAS_2026-11-23.md`. **15 AIFF originais Steinway Model B (Iowa)** nas notas C2/C3/C4/C5/C6 × pp/mf/ff passaram por download oficial, codec, SHA256 e eliminação dos bytes na auditoria GitHub [run 45111873583](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45111873583). Manifesto completo `research/commercial_audio/iowa_steinway_b_verified_original_sha256.json`. **Acervo total agora: 65 gravações originais verificadas em sete fontes instrumentais de piano**, mas *pitch independente, pedal/soltura, física interna e homologação* ainda pendentes.

O gate físico original **R-GATE-2 autoriza aproximação de ponte passiva justificável e calibrável**. Não tornar mobilidade 2×2, histerese instrumentada ou seis pianos pré-requisitos absolutos para a etapa mínima de preparação. **0/7 gates integralmente aprovados**; nenhum DSP/P1/P2/FX/UI/MIDI/preset alterado ou autorizado. Preservar v1.9.5 como referência histórica de estabilidade e medir meta de 32–64 vozes no hardware após autorização.

---

## ÚLTIMA SITUAÇÃO: FELT ORIGINAL VERIFICADO, IMPLANTAÇÃO PROIBIDA (23/11/2026)

O criador **Tom Guder** publicou \`FuchsUndMoehrSamplesWAV16bit.zip\` (Fuchs & Möhr Felt, Public Domain declarado). O ZIP original do Drive, de **648.995.046 bytes**, foi indexado seletivamente: **264 WAVs, 88 notas × 3 camadas**. Quinze WAVs originais nas cinco regiões MIDI 36/48/60/72/84 × piano/mezzo/forte receberam CRC32/PCM WAV 48kHz/16bit/2 canais e SHA256. Evidência https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45105332553 ; SHA256 permanentes em research/commercial_audio/felt_original_verified_sha256.json; nenhum WAV enviado ao GitHub/app.

**Acervo acumulado:** 50 gravações comerciais originais de seis pianos acústicos, 173.943.136 bytes. **Física continua não calibrada**: não há par antes/depois felt no mesmo instrumento, força de martelo, duas polarizações e mobilidade de ponte medida. O protocolo de medições próprio/comercial está em docs/PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md. **TODOS os sete gates globais ainda NÃO integralmente aprovados.** Congelamento de novo DSP/P1/P2/alteração de timbre, MIDI, FX, interface e presets **OBRIGATÓRIO** até o usuário expressamente autorizar após evidências.

---

## REFERÊNCIAS COMERCIAIS ATUALIZADAS — 35 ORIGINAIS, DSP CONGELADO (22/11/2026)

A partir do último piloto: **sete WAVs originais Steinway Model D Princeton CC BY 4.0** foram obtidos diretamente do Internet Archive (sem baixar ZIPs inteiros), verificados integralmente e receberam SHA256. São cinco notas/camadas Piano Bar e duas C4v8 correspondentes em Binaural/Harp Omni; áudio foi eliminado, somente metadados persistiram. Somando 28 arquivos anteriores, **35 originais / cinco instrumentos reais / 103.753.348 bytes**, mas **sem medir parâmetros físicos internos**. CI https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45103239343 ; manifesto research/commercial_audio/steinway_d_verified_wav_sha256.json.

Tom Guder Fuchs & Möhr Felt: autoria e declaração Public Domain do ZIP WAV no fórum confirmadas, porém ZIP autoral NÃO adquirido/validado, nem existe par antes/depois felt controlado. **R-GATE-1..7 permanecem não aprovados integralmente (0/7).** Manter congelamento expresso do DSP e P1/P2, sem alterações em A/B/C, presets, interface, MIDI ou FX. Detalhes docs/PRINCETON_STEINWAY_D_FELT_FONTES_COMERCIAIS_2026-11-22.md.

---

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
