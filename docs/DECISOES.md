# Stage Synth — registro de decisões compartilhadas

**Criado em:** 22/11/2026. Este documento registra acordos obtidos das conversas e dos arquivos existentes; onde faltam evidências, o status é explicitado.

## D-001 — GitHub como fonte central de código e decisões

**Decisão:** manter regras compartilhadas em `AGENTS.md` e usar `docs/ESTADO_ATUAL.md`, `docs/DECISOES.md` e `docs/PROXIMAS_ETAPAS.md` como passagem de contexto entre chats e IAs.

**Ressalva:** o GitHub não sincroniza automaticamente conteúdos das conversas. Cada chat/IA deve ler o repositório e gravar decisões e mudanças verificáveis. Créditos de Work não são requisito para a existência desses arquivos.

## D-002 — Preservar a estabilidade da v1.9.5

**Decisão:** preservar `experimental/physical-v1.9.5/` como referência **relatada pelo usuário** livre de estalos no PC. Alterações ambiciosas de DSP devem permanecer isoladas até demonstrar fidelidade e desempenho sem regressão.

**Não significa:** que a raiz `main` executa a v1.9.5, nem que a v1.9.5 foi homologada em todos os dispositivos.

## D-003 — Fidelidade dos pianos antes de novas compensações cosméticas

**Decisão:** orientar a evolução por modelos de martelo, cordas com inarmonicidade, decaimento espectral, acoplamento de cordas, amortecedores, ponte, tampo e ressonância simpática. Equalização global isolada não resolve a mecânica.

**Critério de aceitação:** testes acústicos multirregistro/multivelocidade, comparação A/B auditiva com referências e preservação de estabilidade.

## D-004 — Meta de polifonia e dispositivos

**Decisão:** 32 notas simultâneas são **mínimo exigido**, 64 são a **meta ideal**. Otimizar para computadores modestos e Moto g04s. Medir o motor completo e os efeitos em hardware real antes de declarar a meta alcançada.

## D-005 — Referências sonoras são privadas

**Decisão:** as quatro capturas acústicas e nove elétricas servem de referência de calibração, não de banco de samples e não devem ser publicadas no GitHub sem confirmação de direitos. Capturas acústicas mantiveram os efeitos originais, por isso representam o **timbre final** e não necessariamente uma nota seca.

**Japanese Grand:** referência adicional de Yamaha CFX fornecida pelo usuário; documentos em `docs/REFERENCIA_JAPANESE_GRAND.md`.

## D-006 — Nomes de pianos elétricos

**Decisão confirmada pelo usuário:** usar **CP70** em vez de CP80; `E. Piano 1 = Full Tines`, `E. Piano 2 = Dino EP`, `E. Piano 3 = Ballad Keys`.

**Implementação conhecida:** mudanças e migração de presets registradas na pasta experimental **v1.9.5**. Não presumir que a raiz v1.8.4 já foi atualizada.

## D-007 — Diferenciar linhas do projeto

**Decisão:** não confundir o motor `physical-v1.9.x`, o protótipo mecânico v1.12.1 e a linha externa "Novo Stage v1.11". Integrar somente depois de obter e comparar o código-fonte correto, mais testes.

## D-008 — Critérios de publicação

**Decisão:** registrar commit, teste, status de implantação e, quando possível, verificar o endereço público. Manter backups versionados e reversibilidade. Não afirmar que uma página funciona quando Pages ainda está na fila ou o URL responde 404.

## D-009 — Recursos existentes que não devem regredir

Manter os seis módulos, a seleção independente instrumento/preset, mudanças de parâmetros em tempo real quando fisicamente possíveis, endereçamento múltiplo de efeitos, bypass FX por instrumento, MIDI, sustain e compatibilidade com cenas/controles anteriores. Migração de presets salvos deve ser explícita.

## D-010 — Validação de análises externas

Diagnósticos de Claude ou outras IAs são insumos testáveis, não substitutos da avaliação musical. O scorecard reproduzido de v1.9.6 é útil, mas 5/5 não equivale a timbre realista. Conferir sempre com o código e registros de teste.

## Novas decisões

Usar formato: ID, data, decisão, motivo, impacto nas versões, evidência (commit/arquivo) e status. Não registrar como implementado aquilo que foi apenas sugerido.

## D-011 — Integração mecânica experimental, sem promover motor (22/11/2026)

**Decisão:** manter a v1.9.5 intacta e testar o corpo de ressonâncias v1.12.1 **dentro do AudioWorklet** do piano físico numa nova pasta `experimental/physical-mechanics-v1.12.2/`. A interação usa retorno mecânico limitado, não uma segunda convolução de reverb nem feedback entre AudioNodes. Deve haver bypass A/B em tempo real e testes de estabilidade com 32/64 vozes. **Não chamar de integração à v1.11**, pois o código dessa linha não está disponível no repositório central. A v1.12.2 ainda depende de avaliação auditiva e validação em hardware.


## D-011 — Novo motor deve ser selecionável dentro do Piano Acústico (22/11/2026)

**Decisão explícita do usuário:** não adicionar categorias, módulos, banners, links ou botões externos para acessar novos motores; usar a opção existente **Motor do piano** com **A · Claude** e **B · Novo Stage**. A síntese clássica permanece opção de compatibilidade. A v1.12.3 integra o B mecânico baseado em v1.9.5/v1.12.2 na raiz do aplicativo e remove os atalhos externos anteriores.


## D-012 — Comparação de motores A/B/C na mesma tela (22/11/2026)

**Decisão do usuário:** incluir o motor anterior do Stage e o modelo modal associado ao Claude para comparação, **dentro de Piano Acústico → Motor do piano**, sem categorias, botões ou links adicionais.

**Implementação v1.12.4:** A = modal derivado da linha Claude, B = código original da v1.9.5 (processador independente), C = Stage atual com mecânica integrada. O modo Clássico permanece. B NÃO é o Novo Stage v1.11.0 originalmente desenvolvido noutra conversa, cujo código não está disponível; esse item ainda requer localização/importação da fonte exata. Presets `physical` existentes continuam C.

**Critérios de aceite:** motores DSP diferentes, teste de seleção/persistência, regressão 32/64 nos físicos B/C, nenhum novo módulo; validar AudioWorklet no hardware do usuário. Teste acústico ainda não significa equivalência a piano real.

## D-013 — Medir a inarmonicidade e o decaimento antes de alterar o DSP (22/11/2026)

**Decisão:** começar a evolução acústica com uma suíte offline, reprodutível, sem tocar nos motores A/B/C. Medir C2/C4/C6, velocities 32/80/120 e quatro pianos; registrar picos, espectro, desvios, B aproximado e decaimento. O histórico B v1.9.5 não é alterado. **Limitação:** números de FFT não atestam timbre realista ou 32/64 vozes em hardware. Só comparar/potencialmente promover uma mudança de DSP depois de CI, testes de áudio em navegador e escuta real. Evidência: branch research/piano-acoustic-metrics-v124 e docs/BASELINE_ACUSTICA_V124.md.


## D-014 — Modelagem física requer coerência entre subsistemas, não acumulação de ressonadores (22/11/2026)

**Decisão de pesquisa:** a escolha entre síntese modal, waveguide e motor híbrido será feita com base em equações/medidas, resposta sonora e custo real. Na linha v1.12.4, modos adicionais e linha de atraso têm dispersão e perdas parcialmente independentes; o P1 mostrou que alterar só o guia não modifica proporcionalmente a saída completa. Não promover motor por aumento isolado de B, harmônicos ou ressonância.

**Base técnica:** Bank–Zambon–Fontana (2010), Chabassier–Chaigne–Joly (2014), Cheng–Dixon–Mauch (2015), documentação Unsampled Piano (2026). Síntese aprofundada em docs/FUNDAMENTOS_MODELAGEM_FISICA_PIANO_2026-11-22.md.

**Evidência de implementação:** somente documentação; nenhum DSP alterado. P1 permanece em PR #2 experimental/draft. A base v1.9.5 fica preservada.

## D-015 — Exigir identificação acústica e teste perceptivo antes de calibração de parâmetros físicos (22/11/2026)

**Decisão:** diferenciar gravações polifônicas com FX de notas isoladas secas; medir rigidez, decaimento por parcial, resposta à velocity, releases, ressonância simpática e função de transferência da ponte/tampo por registro. Usar instrumentos/referências licenciados e metadados claros. Gravações privadas não devem ser publicadas nem copiadas como samples.

**Validação:** medições observacionais, teste auditivo nivelado, CI e CPU em AudioWorklet real (PC e Moto g04s). Mínimo 32, meta 64; sem homologação por benchmark Node. Decisão de arquitetura depende da evidência, não do rótulo do motor.


## D-016 — Fontes de áudio identificadas por modelo, licença e condições de captura (22/11/2026)

**Decisão:** usar Yamaha Salamander C5 (CC BY 3.0), Steinway Model B University of Iowa (permissão pública sem SPDX), Felt Fuchs & Möhr (domínio público declarado pelo autor) e Upright Kawai FreePats (CC0) como **referências físicas diferentes**. Usar Yamaha CFX GSi somente como referência de escuta: o CFX não equivale ao Yamaha C5 e os WAVs brutos não estão licenciados para incorporação no Stage. O Ivy Audio Piano in 162 é fonte adicional para avaliação de pedal, microfone e dinâmica; distribuição de samples não é presumidamente autorizada.

**Controles:** baixar/manter áudios localmente, registrar hashes e condições, preservar originais, rejeitar trechos em loop/reverberação para inferir T60 de cordas. Validação requer nota isolada, mapeamento correto de pitch e intensidade e escuta nivelada; não supor que pp/mf/ff mapeiem diretamente para velocidades MIDI 32/80/120.

**Referência:** docs/REFERENCIAS_SONORAS_YAMAHA_STEINWAY_FELT_UPRIGHT_2026-11-22.md. **Alteração documental somente**; sem mudança nos motores A/B/C e sem upload de gravações.


## D-017 — Referências reais por instrumento e análise espectral não substituem audição controlada (22/11/2026)

**Decisão:** executar o protocolo E0 com notas isoladas de Steinway Model B Iowa (9 AIFF originais), Yamaha C5 Salamander (9 AAC de edição reduzida), Felt Fuchs & Möhr (9 WAV reempacotados, domínio público) e Upright Knight VCSL (6 AAC, CC0). Os 33 arquivos foram analisados em runner temporário do GitHub; o repositório e os artifacts guardam **somente códigos, proveniência/hashes e resultados numéricos**.

**Resultado:** diferenças sistemáticas de amplitude relativa dos parciais, especialmente no grave, foram maiores nos modelos Stage B/C que no modal A em muitos desses exemplos. Não é comprovante de superioridade perceptual; microfones, camadas de velocity, compressão e acústica da sala não são equivalentes. B/C mantidos sem mudanças.

**Exigência E1:** tratar B com menos de três parciais como inconclusivo, medir transientes agudos em janelas curtas sem chamá-los de B e desenvolver identificação por harmônico/tempo antes de qualquer ajuste de DSP. Referência: docs/ANALISE_AUDIO_REAL_E0.md. CI documentado na branch de pesquisa. Nenhum som de terceiro foi embutido.


## D-018 — Priorizar dados acústicos científicos com velocity controlada e fabricante identificado (22/11/2026)

**Decisão:** antes de qualquer nova modificação em timbre físico, promover a **qualidade das evidências**, não a complexidade do DSP. O BiVib Yamaha DC3 M4/DU1A (88×10 velocidades, 96 kHz/24 bit, calibração binaural/equipamentos) passa a ser a referência primária para dinâmica e radiador; o RWC Yamaha/Steinway/Bösendorfer (3×88×4×3) para fabricantes, pedal, repetição e articulação; MAPS ENSTDkCl/ENSTDkAm **somente** para captação do mesmo Disklavier real; MAESTRO para interpretação musical, velocity e pedais.

**Cautelas:** os dados anteriores E0 (33 casos) foram medidos corretamente segundo o método disponível, mas **não constituem padrões físicos controlados**: erros espectrais relativos e aumento de B não significam fidelidade perceptiva. As referências científicas BiVib/RWC/MAPS/MAESTRO usam licenças que incluem restrições NC; o uso interno e comercial, se houver, depende de revisão de termos e permissões apropriadas. Dados CFX específicos e referência Felt com gravação científica controlada continuam sem identificação confirmada.

**Evidência:** docs/AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md. Somente pesquisa; nenhuma gravação adicional baixada, sem alteração DSP/UI/MIDI/FX/presets. A v1.9.5 fica preservada.


## D-019 — Modelo D e CFX não são intercambiáveis com gravações Yamaha C5/Steinway B (22/11/2026)

**Decisão:** para American/Steinway Model D, incorporar à pesquisa o **bitKlavier Grand**, com áudio gravado em Princeton de **um Steinway D real**, 16 layers nas notas amostradas a cada terça menor, 9 pares de microfones e CC BY 4.0. O processamento incluiu denoise, recortes, fades e nivelamento das layers; adequado para comparar caráter timbral e radiador, mas **não** derivar relação física de velocity. Para Yamaha CFX, a biblioteca **Vienna Synchron Yamaha CFX** identifica o instrumento real, mas apresenta produto/amostras comerciais e processamento; usar apenas como referência de escuta mediante termos.

**Proteção:** CFX, C5 e Disklavier DC3 M4 são modelos distintos; Steinway Model D e Model B também. Não afirmar termos físicos equivalentes apenas por fabricante. Não importar gravações ao aplicativo nesta revisão. Evidências e fontes: docs/AUDITORIA_FONTES_CIENTIFICAS_PIANO_ACUSTICO_2026-11-22.md.


## D-020 — Lacunas P0 bloqueiam promoção de P1/P2 como motores realistas (22/11/2026)

**Decisão:** a auditoria de código e pesquisa acústica encontrou **18 lacunas**. As sete condições P0 são: colisão martelo–corda, cordas/uníssonos/polarizações, ponte/tampo e energia passiva, dispersão/perdas por parcial, medidor acústico robusto, referência física identificável e validação de CPU/escuta. **Nenhum novo motor deverá ser integrado em main somente com mais modos, filtros allpass ou mudanças de B.** O motor histórico B v1.9.5 permanece preservado e PR #2 continua experimental.

**Evidência verificável:** a pesquisa em docs/AUDITORIA_LACUNAS_MODELAGEM_FISICA_E1_2026-11-22.md confronta physical-piano.js, piano-resonance.js, piano-worklet.js, stage.js e acoustic.js com Smith, Weinreich, Bank, Chabassier e trabalhos experimentais. **Não são bugs sonoros conclusivamente reproduzidos**: P0 distingue mecanismo comprovadamente ausente de efeito perceptivo ainda não medido.

**Permissão de avanço:** podem ser iniciados **protótipos isolados**, instrumentação e medição E1.1–E1.5, sem alterar timbres públicos ou criar links/módulos. A escolha entre modal, waveguide e híbrido só será feita com resultados controlados e budget 32/64 notas.

## D-021 — Medidor E0 não pode certificar inarmonicidade para altos valores B (22/11/2026)

**Decisão:** a busca fixa por picos de ±2,5% de n×f_ET no tests/piano_acoustic_metrics.mjs é insuficiente quando B cresce. Analiticamente, B=0,0012 e n=8 produzem deslocamento relativo de +3,707%; o medidor pode tomar outro pico ou não encontrar a parcial física. Uma taxa mínima de três picos não prova correspondência física. Além disso, mono L/R e velocidades diferentes limitam a fidelidade das comparações de 33 áudios E0. **Não são cadeias equivalentes**: no aplicativo, A modal usa convoluções de cordas/corpo enviadas pelo output auxiliar de acoustic.js; o benchmark E0 lê apenas L/R direto do A, ao passo que C já incorpora corpo interno. E1.0 deve medir o núcleo seco e o aplicativo completo como trilhas separadas.

**Ação:** testar primeiro com sinais sintéticos conhecidos (f1, B até 0,003, envelope por parcial, cordas duplicadas, ruído, ataque curto), implementar E1 STFT/peak tracking e registrar intervalos de incerteza. Reprocessar 33 referências sem apagar a baseline original. **Não afirmar melhora ou piora do timbre por esses escores sozinhos.**

**Proveniência:** docs/AUDITORIA_LACUNAS_MODELAGEM_FISICA_E1_2026-11-22.md. Nenhum DSP ou método de medição foi alterado nesta decisão.


## D-022 — Congelamento da implementação do próximo motor por ausência de referências preparadas (22/11/2026)

**Pedido expresso do usuário:** não continuar implementação do novo modelo físico até ter todas as referências essenciais prontas e lacunas preenchíveis com dados e métodos confiáveis.

**Resultado da auditoria:** fontes primárias de modelagem foram identificadas, mas a prontidão geral é **NÃO PRONTA**. O inventário de **22 fontes/famílias** e 18 lacunas está em docs/PRONTIDAO_REFERENCIAS_PIANO_FISICO_2026-11-22.md, com **sete R-GATEs ainda não comprovados integralmente**. Obter um paper não equivale a ter parâmetro medido, WAV/CSV original, checksum, licença e uma comparação justa. BiVib (33,1 GB multipartes), RWC (14,2 GB ZIP), Plath/Hamburgo (4,6 GB CSV compactados), QMUL pedal (222,7 MB) e bitKlavier Model D não foram integralmente preparados.

**Descoberta:** Plath/Hamburgo publicou pressão binaural [Pa] e aceleração da ponte [m/s²] sincronizadas à força tecla–base [N]; é valioso para validar radiador, MAS a força não é aplicada diretamente na ponte e não permite inferir automaticamente sua mobilidade complexa. O grupo Plath/Bader mediu FRFs reais na ponte, mas os arquivos numéricos brutos não foram localizados. Liang/QMUL publicou som de pedal e trajetória contínua, que ainda requer direitos e análise.

**Restrições imediatas:** congelar novos motores P2, alterações de timbre e promoção de P1 (PR #2). **Permitir somente pesquisa, verificação de direitos/acesso, documentação, contatos a autores com autorização e preparação de conjuntos de referência e planos de testes**; não declarar GATE concluído sem demonstrar evidência original. Manter A/B/C e B v1.9.5 intactos e metas 32–64 notas.

**Liberação:** somente revisão explícita dos 7 R-GATEs, fonte e documentação atualizadas e aprovação da etapa de implementação após os requisitos estarem verificados.

## D-023 — Stage Synth é software destinado à comercialização (22/11/2026)

**Decisão expressa do usuário:** objetivo comercial do Stage Synth. Pesquisas, desenvolvimento, calibração, dados, recursos de áudio, código adaptado e eventual distribuição **devem respeitar licenças compatíveis com utilização comercial**. A prioridade científica de um dataset **não substitui** autorização legal para seu uso no produto.

**Reclassificação obrigatória:** **BiVib CC BY-NC-SA, RWC CC BY-NC, MAPS NC, MAESTRO CC BY-NC-SA** ficam fora do pipeline comercial de calibração/treinamento/teste sobre os arquivos até obter permissão específica. Referências científicas podem continuar sendo **lidas** para aprender métodos, sem usar arquivos restritos. Priorizar VCSL/CC0, Salamander Yamaha C5/CC BY 3.0, bitKlavier Steinway D/CC BY 4.0, Kawai KW/CC0, Fuchs & Möhr Felt com declaração PD do autor, Iowa Model B com permissão expressa sem restrição de projeto e **gravações/medições próprias com autorização para uso comercial**. Todos ainda requerem manifesto de origem, licença, hash, qualidade e condições experimentais; nenhum é automaticamente considerado pronto.

**Status de distribuição:** não foi encontrado LICENSE na raiz do repo; o dono deve decidir a licença do próprio código, conferir dependências e atribuições, bem como marcas/modelos comerciais sem alegar endosso. O projeto pode ser comercial e usar bibliotecas com atribuição, mas EULAs e direitos de terceiros devem ser revisados. **NÃO mexer no motor; congelamento de P1/P2 segue em vigor.** Documento: docs/POLITICA_COMERCIAL_DADOS_LICENCAS_2026-11-22.md.

## D-024 — Proveniência de 28 arquivos ORIGINAIS licenciados, sem incorporar áudio ao Stage (22/11/2026)

**Decisão executada:** preparar concretamente um pequeno corpus para desenvolvimento COMERCIAL sem utilizar datasets NC nem modificar motores. Verificados **28 arquivos de quatro instrumentos acústicos**: 8 WAVs VCSL CC0 (Steinway Model B e Knight upright), 15 FLACs Salamander Yamaha C5 CC BY 3.0 e 5 FLACs FreePats Kawai KW CC0. Os WAVs e FLACs foram transferidos somente para /tmp no GitHub Actions, comparados ao SHA1 Git blob do commit original, ao tamanho, SHA256 e estrutura WAV/FLAC; FLAC também passou teste integral de decodificação. **Nenhum áudio distribuído ou introduzido no aplicativo.**

**Proveniência permanente:** research/commercial_audio/vcsl_cc0_pilot_manifest.json, research/commercial_audio/cc_flac_pilot_manifest.json, research/commercial_audio/verified_source_sha256.json e docs/PREPARACAO_FONTES_COMERCIAIS_PILOTO_2026-11-22.md. CI principal: https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45101876490 (10/10 testes offline, 28 verificações). VCSL Steinway usa samples **normalizados**, Knight amostra tons inteiros, Kawai KW possui **loops graves** e o arquivo C4vH não existe; nenhuma camada é prova de hammer velocity física.

**Estado dos sete gates:** 0/7 integralmente aprovados. Fonte confiável e licença compatível não dispensam medição de ponte/martelo, controle de dinâmica, parametrização física, protótipos isolados e validação de hardware. P1/P2 e DSP permanecem congelados.


## D-025 — Steinway Model D Princeton CC BY 4.0: sete WAVs originais verificados; Felt autoral ainda não adquirido (22/11/2026)

**Executado:** três coleções autorais bitKlavier Grand do **Steinway Model D real**, gravado em Princeton, com posições **Piano Bar**, **Binaural** e **Harp Omni**, tiveram identidade do Archive, licença **CC BY 4.0**, tamanho e MD5 do ZIP verificados por metadados oficiais. Em seguida foram **baixados somente sete WAVs individuais selecionados**, diretamente das pastas virtuais dos ZIPs originais, verificados por PCM WAV 44,1k/16bit e SHA256 de todos os bytes, descartados ao fim do teste. **7/7 arquivos / 39.356.676 bytes**, 22/22 testes unitários da preparação; sem ZIP completo, gravações no repositório nem artifacts de áudio. SHA256: research/commercial_audio/steinway_d_verified_wav_sha256.json. Evidência CI: https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45103239343 .

**Ressalva:** o bitKlavier é editado, denoised e reequilibrado por velocity; não é força real do martelo/ponte. Essa evidência apenas melhora a preparação para calibração comercial e escuta.

**Felt:** foi identificado no fórum do criador Tom Guder o ZIP autoral FuchsUndMoehrSamplesWAV16bit.zip (WAV stereo, três camadas, domínio público declarado). Link do Google Drive está documentado, mas **nenhum ZIP autoral foi integralmente transferido ou conferido por SHA**; a E0 anterior usou arquivos de um espelho reempacotado. Falta ainda o mesmo piano com e sem feltro em condição controlada.

**Prontidão acumulada:** 35 fontes originais verificadas de **cinco pianos acústicos** (103.753.348 bytes), com permissões de uso comercial verificadas ao nível de acervo. **Zero dos sete R-GATEs globais integralmente aprovados**; P1/P2 e qualquer DSP permanecem congelados até autorização do usuário e referências físicas identificáveis. Detalhes em docs/PRINCETON_STEINWAY_D_FELT_FONTES_COMERCIAIS_2026-11-22.md .


## D-026 — Gravações FELT originais obtidas e verificadas seletivamente; física interna ainda não medida (23/11/2026)

**Execução comprovada:** o ZIP autoral de Tom Guder \`FuchsUndMoehrSamplesWAV16bit.zip\`, explicitamente declarado **Public Domain** na publicação do próprio criador, foi acessado por **HTTP Range** da origem Google Drive sem baixar seus 648.995.046 bytes integralmente. Índice do original contém **264 WAVs = 88 teclas × 3 camadas** (piano/mezzo/forte). Foram extraídos **15 WAVs originais nas notas MIDI nominais 36/48/60/72/84 × 3 camadas**, com integridade CRC32, PCM estéreo **48 kHz/16bits**, SHA256 por arquivo e descarte de áudio. A conferência transferiu 46.588.134 bytes compactados e examinou 70.189.788 bytes WAV. **36/36 testes** da preparação passaram: https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45105332553 .

**Manifesto permanente:** research/commercial_audio/felt_original_verified_sha256.json. Documento: docs/PREPARACAO_FELT_ORIGINAL_COMERCIAL_2026-11-23.md . Os arquivos de áudio não foram publicados no Git nem distribuídos no app. O digest inteiro do ZIP original ainda não está verificado, apenas os 15 membros e o diretório.

**Acervo comercialmente elegível preparado até aqui:** **50 WAV/FLAC originais / seis pianos reais / 173.943.136 bytes totais**. A declaração de domínio público do autor precisa de avaliação de direitos e condições de exploração comercial no lançamento, como as demais licenças.

**Atenção física:** Felt com/sem no mesmo piano ainda não medido; camadas p/m/f não são velocidades de martelo; faltam força F(t), duas polarizações e mobilidade complexa da ponte. O protocolo de ensaios foi formalizado em docs/PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md. **Todos os R-GATEs ainda NÃO integralmente aprovados (0/7), e P1/P2/DSP continuam congelados por determinação do usuário.**


## D-027 — Distinguir IR acústica, mobilidade mecânica e movimento de tecla na calibração comercial (23/11/2026)

**Decisão:** não interpretar IR do tampo medida por alto-falante de contato + microfones como admitância física complexa da ponte, nem `T60` de percussão do tampo como decaimento das parciais de uma corda. A calibração M04 exige `F_ponte(t)` e resposta no mesmo ponto, com amplitude, **fase**, posição e coerência; M05 mede radiação acústica separadamente. Nove ensaios M01–M09 permanecem planejados, sem nenhuma captura executada. Evidência e critérios em [RADIACAO_TAMPO_TOQUE_FONTES_COMERCIAIS_2026-11-23.md](RADIACAO_TAMPO_TOQUE_FONTES_COMERCIAIS_2026-11-23.md), a partir de Bader/Acoustics 2022, AudioLabs FAU 2023 e PNAS 2025.

**Dado externo novo:** `facebookincubator/Meta-open-sound` possui CC0 declarado e manifesto de **352 nomes de amostras Upright**, 88 notas × 4 velocities; **somente os textos, SFZ e manifestos foram verificados**. Não baixar, redistribuir ou considerar os arquivos plenamente verificados antes de conferir bytes, origem e condições acústicas. Não somar 352 às 50 gravações Stage com proveniência original e hashes já auditados. Artigos e dados com restrições NC ou licenças não esclarecidas ficam fora de calibração comercial.

**Proteções:** nenhum novo DSP ou integração P1/P2. `main` v1.12.4, motor histórico v1.9.5 preservado. Os **sete R-GATEs permanecem integralmente bloqueados**, e a homologação de 32–64 notas depende de hardware real.


## D-028 — Não reduzir contato do martelo a pulso fixo nem mobilidade da ponte a escalar sem declarar hipótese (23/11/2026)

**Decisão de pesquisa:** acrescentar à futura especificação de coleta **M01.1 — curva F_h(t)/δ(t) com compressão e recuperação (histerese)**; e **M04.1 — matriz complexa 2×2 de mobilidades da ponte**, `Y_TT/Y_TP/Y_PT/Y_PP`, captada por força-resposta calibrada em dois planos e pontos identificados. O escalar normal `Y_TT` é um piloto legítimo, **não identifica** por si a transferência entre planos e o duplo decaimento. Reciprocidade, causalidade, passividade, erro/fase e resposta radiada devem ser avaliados com dados adequados e não por coeficientes inventados.

**Evidência:** [EVIDENCIA_MARTELO_MOBILIDADE_CRUZADA_E_REDUTORA_2026-11-23.md](EVIDENCIA_MARTELO_MOBILIDADE_CRUZADA_E_REDUTORA_2026-11-23.md), fontes primárias Yanagisawa/Nakamura (1984), Russell/Rossing (1998), Askenfelt (1991), Ege/Boutillon (2010) e Miranda Valiente et al. (2022/2023, 2024). A literatura demonstra que modelos reduzidos são **plausíveis para investigação**, mas não prova fidelidade do Stage ou tempo real em dispositivo específico. Exemplo de parâmetro medido em outro piano não deve ser transferido como “calibrado” aos quatro timbres.

**Limite de direitos:** artigo científico ≠ arquivo de dados autorizado, nem licença de software de terceiros. Simionato et al. têm código **LGPLv3** e dataset externo de direitos não verificados; estudo conceitual não autoriza copiá-lo sem revisão de obrigações. Qualquer novo dado de calibração do Stage comercial exige autorização expressa.

**Status:** somente documentação e protocolo; nenhuma gravação física nova, implementação DSP/UI/MIDI/FX/preset ou merge de P1/P2; `main` v1.12.4 e v1.9.5 histórica preservadas, **0/7 R-GATEs completos** e 32–64 notas aguardando teste físico.
