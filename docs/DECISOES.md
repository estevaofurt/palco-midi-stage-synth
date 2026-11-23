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
