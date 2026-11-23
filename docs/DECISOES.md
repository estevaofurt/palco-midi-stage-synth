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

**Decisão:** a busca fixa por picos de ±2,5% de n×f_ET no tests/piano_acoustic_metrics.mjs é insuficiente quando B cresce. Analiticamente, B=0,0012 e n=8 produzem deslocamento relativo de +3,707%; o medidor pode tomar outro pico ou não encontrar a parcial física. Uma taxa mínima de três picos não prova correspondência física. Além disso, mono L/R e velocidades diferentes limitam a fidelidade das comparações de 33 áudios E0.

**Ação:** testar primeiro com sinais sintéticos conhecidos (f1, B até 0,003, envelope por parcial, cordas duplicadas, ruído, ataque curto), implementar E1 STFT/peak tracking e registrar intervalos de incerteza. Reprocessar 33 referências sem apagar a baseline original. **Não afirmar melhora ou piora do timbre por esses escores sozinhos.**

**Proveniência:** docs/AUDITORIA_LACUNAS_MODELAGEM_FISICA_E1_2026-11-22.md. Nenhum DSP ou método de medição foi alterado nesta decisão.
