# Stage Synth — auditando evidência do martelo, mobilidade cruzada da ponte e modelo físico reduzido (23/11/2026)

**Estado:** pesquisa documental, sem nova implementação. **Base consultada:** `main` SHA `a6f76e97c237d9e0921e5df1b4c7a69c92bd5f56`, `package.json` v1.12.4, `AGENTS.md`, `docs/ESTADO_ATUAL.md`, `docs/PROXIMAS_ETAPAS.md`, `docs/PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md` e `docs/RADIACAO_TAMPO_TOQUE_FONTES_COMERCIAIS_2026-11-23.md`. B v1.9.5 continua referência histórica de estabilidade relatada; A/B/C são protótipos sem homologação física. **Todos os sete R-GATEs permanecem bloqueados**, P1/P2/DSP/FX/MIDI/UI/presets congelados por pedido do titular.

## 1. Novas fontes primárias verificadas e o que efetivamente entregam

| ID | Fonte | Constatação documentada (T/P) | O que NÃO temos (D/V) e cautela comercial |
|---|---|---|---|
| F01 | **Yanagisawa & Nakamura**, *Dynamic compression characteristics of piano hammer felt*, J. Acoust. Soc. Japan **40(11), 725–729 (1984)**, DOI https://doi.org/10.20697/jasj.40.11_725 ; https://www.jstage.jst.go.jp/article/jasj/40/11/40_KJ00001453633/_article/-char/en | Mediram **força martelo–corda F(t)** e deslocamentos de corda e madeira do martelo para obter compressão do feltro `δ(t)`; o andamento de rigidez aparente ao longo da colisão rejeita hipóteses de rigidez fixa. Fonte primária de **histerese/memória de contato**, não uma sugestão estética de timbre. | Página J-STAGE explicitamente mostra **0 suplementos**; sem série numérica original `F(t)`, `δ(t)` licenciada para Stage. Artigo disponível para leitura, não banco de calibração identificado. |
| F02 | **D. Russell & T. Rossing**, *Testing the Nonlinearity of Piano Hammers Using Residual Shock Spectra*, **Acustica 84, 967–975 (1998)**, PDF hospedado na Penn State https://www.acs.psu.edu/drussell/Publications/pianohammer.pdf | Publicação mostra instrumentação por transdutor de força, velocidades antes do impacto e martelos de pianos Steinway. **Exemplo estritamente da amostra do estudo:** martelo A3 duro a 4 m/s gerou pico de **183 N** e semilargura de pulso **0,24 ms**; pulso assimétrico dependente do feltro. Haste/voicing/dinâmica alteram resultado. | Exemplo de amplitude/escala de contato **não** é parâmetro universal, nem do motor Stage; gráficos publicados não são `F(t)` brutamente fornecido e licenciado. Não ajustar os quatro pianos do Stage para esses números. |
| F03 | **Anders Askenfelt**, *Measuring the motion of the piano hammer during string contact*, **STL-QPSR 32(4), 19–34 (1991)**, KTH https://www.speech.kth.se/qpsr/1991/1991_32_4_019-034.pdf | Medição óptica de deslocamento em **dois eixos** (na direção de impacto e ao longo da corda) perto da cabeça do martelo, para diferentes dinâmicas e articulações; mostra que a trajetória do martelo não é um impulso escalar invariável. | PDF legível e figuras, mas nenhum arquivo de séries sincronizadas ou licença de dados comercial foi constatado; não interpretar movimento horizontal do martelo como medição H/V das cordas. |
| F04 | **Kerem Ege & Xavier Boutillon**, *Synthetic description of the piano soundboard mechanical mobility*, ISMA 2010 / arXiv 1210.5688, https://arxiv.org/abs/1210.5688 | Método de síntese de **mobilidade mecânica média da ponte** a partir de descritores globais **massa M, densidade modal n(f), fator médio de perdas η(f)**. No **upright específico do artigo**, autores reportam `M=9 kg`, `n≈1/19,5 modos/Hz`, `η≈2%` no regime aproximado de placa e uma mudança estrutural por confinamento entre nervuras perto de **1,1 kHz**, embora a transição seja dependente do ponto. Mostra que o corpo pode receber um modelo reduzido disciplinado pela física. | Esses números caracterizam **um vertical estudado** e a mobilidade média predominantemente normal ao tampo, NÃO Yamaha/Steinway/felt universais, NÃO uma FRF complexa completa em cada ponto da ponte. PDF/paper != sinais brutos calibrados. Valores apenas candidatos para ensaios **offline de plausibilidade**, sem alterar DSP. |
| F05 | **Pablo Miranda Valiente, Giacomo Squicciarini & David Thompson**, *Modelling of piano string vibration using coupled mobilities and a state-space approach*, INTER-NOISE 2022 / 2023, DOI https://doi.org/10.3397/IN_2022_0561 ; origem do trabalho (Southampton) https://www.southampton.ac.uk/people/668t9f/doctor-pablo-miranda-valiente ; resumo https://papertik.app/p/W4324145020 | O modelo explica **duplo decaimento em uma corda** por movimentos em dois planos **e pelas mobilidades cruzadas da ponte**, usando uma matriz **complexa 2×2** para os dois graus de liberdade transversais no ponto de ligação. Isso evidencia uma **lacuna concreta do protocolo M04 atual**, que exige apenas mobilidade normal escalar. | Artigo/relatório publicados, não matriz Y2x2(f) de um piano-alvo com amostras brutas e direitos comerciais comprovados. Esse experimento não entrega um modelo Stage de 64 vozes. |
| F06 | **Miranda Valiente et al.**, *Influence of soundboard modelling approaches on piano string vibration*, **JASA 155, 3213–3232 (2024)**, DOI https://doi.org/10.1121/10.0025925 ; https://pubmed.ncbi.nlm.nih.gov/38742965/ | Comparação de quatro modelos de corpo, incluindo **5 modos reduzidos**, FE detalhado, elemento Kelvin–Voigt e limite rígido. Confirma que reduzir a estrutura pode preservar certas respostas de corda, mas altera decaimento, força de contato ponte e radiação em outros aspectos. | Não demonstra que **cinco modos** bastem por registro/instrumento/posição de mic ou que 64 notas rodem em navegador. Nenhuma mobilidade numérica de instrumento completo fornecida a esta auditoria. |
| F07 | **Corradi, Miccoli, Squicciarini & Paolo Fazioli**, *Modal analysis of a grand piano soundboard at successive manufacturing stages*, **Applied Acoustics 125, 113–127 (2017)**, DOI https://doi.org/10.1016/j.apacoust.2017.04.010 ; https://re.public.polimi.it/handle/11311/1022091 | Estudo **em tampo de cauda de fabricação Fazioli**, compara etapas livre/com ponte/com estrutura e medições de mobilidade local na ponte com FEM; reporta concordância modal até 400–450 Hz e mobilidade até **4 kHz**. Acima de cerca de **200 Hz** certas condições de montagem apresentaram mobilidades próximas naquele experimento. | Repositório oferece postprint 12,83 MB com **direitos reservados**, não dados brutos `F/v` disponibilizados com permissão comercial. O tampo de Fazioli NÃO pode ser usado como se fosse de Yamaha CFX/Steinway. |
| F08 | **Simionato, Fasciani & Holm**, *Physics-informed differentiable method for piano modeling*, **Frontiers in Signal Processing**, publicado 2024, DOI https://doi.org/10.3389/frsip.2023.1276748 ; https://github.com/RiccardoVib/Physics-Informed-Differentiable-Piano | Artigo revisado por pares: síntese híbrida diferenciável de parciais inarmônicas e envelopes, aprendidos de gravações de notas individuais. Os autores reconhecem que **não modela ruídos** e **não inclui a interação simultânea entre teclas pela ponte**. É referência válida sobre identificação de espectro, não solução de corpo físico completo. | Inspeção DIRETA do GitHub externo: código tem `LICENSE.txt` **LGPLv3** e `COPYRIGHT.txt` com referência; dataset externo no Kaggle https://www.kaggle.com/datasets/riccardosimionato/pianorecordingssinglenotes **não teve direitos comerciais nem arquivos originais inspecionados**. Licença do código, do artigo e de áudio/weights **não devem ser confundidas**. Não copiar nem treinar a partir disso sem revisar direitos. |

**Regra de evidências:**
- **T** teoria publicada; **P** parâmetros com unidade/escopo do experimento; **D** série bruta, hash, local, unidade, sensor, condição e autorização comercial para nosso uso; **V** validação do Stage pelo mesmo caminho acústico. F01–F08 oferecem avanços T/P, mas **não atendem conjuntamente D/V** de um piano medido.
- “Open access”, repositório GitHub público ou artigo CC BY **não confere** automaticamente direito de utilizar arquivos e dados externos associados para calibração comercial.
- Nenhum WAV/CSV foi baixado, distribuído ou embutido. **Acervo Stage inalterado: 50 arquivos originais, seis pianos, 173.943.136 bytes previamente verificados**.

## 2. Novo requisito físico crítico — M04 deve considerar resposta cruzada

A mobilidade mecânica é definida por `Y(f)=v(f)/F(f)`, mas **v e F são vetores**. Para dois planos transversais relevantes da corda (normal `T` e paralelo `P` ao tampo), a hipótese de pesquisa correta é:

```text
[v_T(f)]   [Y_TT(f) Y_TP(f)] [F_T(f)]
[v_P(f)] = [Y_PT(f) Y_PP(f)] [F_P(f)]
```

`Y_TP` e `Y_PT` representam transferência **entre os dois eixos**. Um modelo com `Y_TP=Y_PT=0` por conveniência **não explica todo o acoplamento e o duplo decaimento** sem outras hipóteses. A matriz **não pode ser reconstruída** a partir de um único ensaio com martelo normal à ponte.

**M04.1, medição proposta a profissional:** em ao menos um ponto documentado em cada região (graves, tenor e agudos) quando viável, aplicar força de entrada instrumentada em direções independentes `T` e `P`, medir respostas de velocidade/aceleração em `T` e `P`, com fase, sincronização e calibração. Estimar e arquivar `Y_TT, Y_TP, Y_PT, Y_PP` complexas, espectro de força original, magnitude, fase, coerência, erro/ruído, unidades e geometria dos eixos. Verificar reciprocidade aproximada **somente** nas hipóteses físicas/sistema linear e condições correspondentes, sem impor por força um resultado. Trabalhar com segurança de instrumento e instrumentação especializada. O ensaio atual M04 escalar continua sendo etapa inicial mínima, mas **NÃO** permite reivindicar que o acoplamento completo H/V esteja identificado.

**Alternativa de contingência a evidências indisponíveis:** usar somente uma mobilidade escalar normal ou um modelo estatístico de Ege/Boutillon em estudo offline e declarar **explicitamente** perdas de acoplamento e impossibilidade de garantir realismo de aftersound/uníssonos; não marcar R-GATE-2 concluído nem promover P2. Se o produto não puder obter matriz completa, avaliar perceptualmente a ablação futura e aceitar ou não, com consciência do limite.

## 3. Novo requisito de ensaio de martelo — M01 deve registrar memória/histerese

M01 deve pedir **ambas as fases de compressão e relaxamento do feltro**, não apenas pico máximo: `F_h(t)`, deslocamento da cabeça do martelo e da corda, `δ(t)`, velocidade real ao impacto, duração total do contato, perdas em cada ciclo, condições de voicing/feltro e repetição. O estudo F01 comprova que uma lei **sem estado** não descreve integralmente os dados. O estudo F02 demonstra o quanto a largura/forma do pulso variam.

Se não houver F/δ medidos, pulsos parametrizados por registro e intensidade são **proxies de síntese** e devem ser marcados como hipótese, nunca martelo físico calibrado. Usar literatura para definir plausibilidade e forma de ensaio, não atribuir os valores experimentais de Steinway a um Yamaha/vertical.

## 4. Quadro de decisão metodológica antes de novo DSP

### P0 — primeiro pacote de dados de UM instrumento identificado
- Marcar **origem/cadeia de direitos** em contrato e arquivos brutos.
- M01: martelo e curva tempo-força/deformação em ao menos notas graves, médias e agudas com níveis/replicações documentados;
- M02: uma corda, dois planos, parâmetros de frequência e amortecimento por parcial;
- M03: cordas do mesmo uníssono desligadas/ativas, sem danificar instrumento;
- M04/M04.1: mobilidade complexa da ponte por posição/direção, incluindo pelo menos estimativas e limites de cross-mobility;
- M05: radiador em microfones L/R e sala documentada.

Não exigir todos os modelos de fabricantes no primeiro **piloto de aquisição**, mas **não liberar os sete R-GATEs nem alegar quatro pianos calibrados** por completar um piloto.

### P0 — metodologia de comparação
Separar **(a) martelo/corda secos, (b) ponte/corpo e (c) radiação/microfones**. Alinhar f1 real, velocity física versus MIDI, pitch e pedais; validar o medidor E1.1 com B conhecido. Só depois usar uma métrica de fidelidade A/B/C, complementada por escuta cega. Reversibilidade e testes de base são requisitos independentes.

### P1 — hipótese de arquitetura reduzida, **não implementação**
Candidatos a comparar futuramente: mobilidade modal passiva local por regiões, corpo com estatística modal medida (F04), e propagação simplificada do contato obtida da solução offline (F01/F02). Não tratar a coincidência de uma única curva ou de um timbre ouvido como prova de um piano realista. Testar separadamente o custo por voz e compartilhado; objetivo ainda é 32 mínimo, 64 desejado, **sem homologação de PC/Moto g04s**.

## 5. Lista de ações possíveis sem mudar motores

1. Registrar em `docs/PROTOCOLO_MEDICOES_FISICAS_PIANO_COMERCIAL_2026-11-23.md` que M04.1 com 2×2 e M01 carga/descarga devem constar da especificação de medição e eventual contrato; **não houve contratação/captura**.
2. Preparar pedido de dados originais/autorização ao titular de medições científicas de ponte/ação **somente para eventual envio aprovado pelo usuário**; não enviar contatos automaticamente.
3. Exigir planilha de direitos por artefato: artigo, figuras, waveform, dataset, modelos treinados e código. Dar preferência a medição própria com direitos de exploração comercial expressos.
4. Se dados numéricos de instrumento não forem obtidos, formalizar limites da solução substituta e **não forjar “validação física”**.
5. R-GATE-1..7 permanecem **0/7 globalmente aprovados integralmente**; preservar v1.9.5, isolamento P1/P2, DSP/UI/MIDI/FX/presets e hardware de destino.

**Conclusão:** não faltam fórmulas; falta a **medida vetorial complexa da ponte e força/deformação do martelo no mesmo instrumento**, mais um caminho objetivo para testar a redução modal. Esta investigação é documental, não entrega engenharia ou áudio integrado.
