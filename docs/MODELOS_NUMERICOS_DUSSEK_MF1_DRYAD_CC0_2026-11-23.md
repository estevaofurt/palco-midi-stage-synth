# Stage Synth — parâmetros físicos de terceiros, dados Dryad CC0 e licenças reais (23/11/2026)

**Classificação: pesquisa, não desenvolvimento de som.** A etapa não integra motores ou parâmetros externos e não baixa material para calibração. Confirmado antes de editar: `main` = `9d0030c916091081dbd51959d7948689d6f4c078`, app `package.json` v1.12.4 e `AGENTS.md` bloqueando P1/P2/DSP até 7 gates e liberação expressa. v1.9.5 continua referência histórica de estabilidade relatada. Ver `docs/PRONTIDAO_REFERENCIAS_PIANO_FISICO_2026-11-22.md`.

## 1. Resultado relevante: existem modelos numéricos de 88 notas legalmente documentados, mas derivados de ÁUDIO

### H01 — Dussek (Christian Friedrich Coors): código AGPL, instrumento com licença própria

- GitHub: https://github.com/ccoors/dussek , commit externo **`ea2f50071e7bb844c0c3956a6c8aa2cd65f2f864`**. Arquivos lidos diretamente pela integração GitHub: `README.md`, `LICENSE`, `data/SOURCES.md`, `docs/architecture.md`, `instruments/grand_b/LICENSE.md`, `instruments/grand_b/instrument.json`, `instruments/upright_c/LICENSE.md`; foram verificados metadados de árvore para `data.bin`.
- **Código fonte:** `LICENSE` contém **GNU AGPLv3**, e o README o classifica **AGPL-3.0-or-later**. Essa licença é *copyleft* forte, com obrigações especiais para interação por rede. **Não reutilizar, adaptar, transportar nem linkar código na hipótese de produto proprietário sem análise legal de obrigações e decisão expressa do titular.** Estudo conceitual e comparação de esquemas não exigem cópia de código.
- **Cada instrumento possui licença separada.** `grand_b/LICENSE.md` é **CC BY 4.0**, atribuído ao autor do projeto, deriva de gravações Iowa MIS de piano Steinway B, mais partes de Grand E (VCSL CC0) e Grand A (Salamander, liberado pelo autor). `upright_c/LICENSE.md` é **CC BY-SA 4.0** por incorporar a fonte LivingRoom Upright CC BY-SA: essa condição ShareAlike não deve ser confundida com CC BY 4.0.
- **Manifesto Grand B verificado estruturalmente:** `instruments/grand_b/instrument.json`, blob Git SHA `137b113db3e96ff33fa8d4722fb5224cc5641e35`, **189.279 bytes** na árvore, parse JSON com **88 objetos `notes` (MIDI 21–108)**, `format: 5`, campo `recorded: [22,104]`, `velocity.midi: [14,60,124]`, `velocity.speed: [0.6,2.1,7]`, `board` com referências de modos/atenuação `f/sigma/phi`, radiação L/R, dados de perdas e acoplamento de cada corda, parâmetros de martelo, amortecedores, pedal, simpática e correções por nota. Os metadados `data.bytes=514040` e `data.sha256=733789723faa71352584e49f816e422722681caee5da4b01500d35775c66cb9e` são **DECLARAÇÕES DO MANIFESTO**, não hash calculado nesta sessão. A árvore do Git confirma **`instruments/grand_b/data.bin` de 514.040 bytes**, blob SHA `1c9673992e33b96e6218bb2e74c75e41e3a5204b`; **não verificamos conteúdo binário por SHA-256 nem o renderizador em hardware**.
- **Natureza da informação:** esses valores foram **ajustados a partir de gravações** (Iowa MIS, fontes suplementares), e **não são medições diretas** `F_h(t)`, compressão `δ(t)`, velocidade H/V por corda ou mobilidade complexa 2×2 `Y_{bridge}(f)`. O campo `velocity.speed` do modelo **não prova medição de velocidade do martelo em m/s**. São parâmetros derivados e estimados de modelo, com dimensões físicas atribuídas, não calibração independente do piano.
- **Possibilidade a avaliar posteriormente:** os presets CC BY 4.0 podem ser material de referência de engenharia/comparação e eventualmente estudo legal de derivados com atribuição, sem importar AGPL do motor. Não presumir que licença dos números resolva validação física ou autorize alterar DSP durante congelamento.
- **Direito das gravações Iowa de origem:** fonte oficial https://theremin.music.uiowa.edu/MIS.html diz que as gravações podem ser usadas em quaisquer projetos sem restrições. A procedência do Piano é https://theremin.music.uiowa.edu/MISpiano.html. Permissão do Iowa não é licença do código AGPL nem licença de todos os presets Dussek.

### H02 — MF-1 Piano (Ian Butterworth): código MIT, medição extraída de espectros

- GitHub: https://github.com/IanButterworth/mf-1 , commit externo **`42b70291751e76bb0bda5ec81301fe77e1c60a2f`**. Arquivos lidos diretamente: `LICENSE` = **MIT** (blob `8f686b21706138e0231cc8ae142473dfb012db12`); `docs/piano.md` blob `18530fa1aac520c8d9cc6b28cbf59314847a150f`; `Sources/PianoCore/piano.c`, `Sources/PianoCore/tools/analyze.py`, `Sources/PianoCore/piano_tables.inc`.
- Piano baseado em gravações **Steinway B Iowa MIS, pp/mf/ff em intervalos de três semitons**, sem redistribuir os WAV. O arquivo de tabelas gerado declara **30 notas amostradas**, **970 parciais** e **38 componentes extra**, com afinação, B, batimentos e decadência de parciais. `docs/piano.md` relata **até 128 parciais por tecla**, **32 modos compartilhados do corpo**, e um limite de **384 osciladores ativos** geridos por prioridade. **384 osciladores ≠ 384 notas; também não significa 32 ou 64 notas completas.**
- O projeto reconhece **ausência de ressonância simpática física explícita**, falta de medição dos tempos reais de abafador e do ruído de amortecimento; testes no hardware FM-1 são limitados e carga real do pior caso de 384 osciladores ainda é estimada. Portanto não oferece solução para todos os M01–M09 ou certificação da meta Stage.
- O modelo de 32 modos é **ajustado ao resíduo acústico do ataque nas gravações**; não confundir com uma FRF mecânica 2×2 de ponte medidas com martelo instrumentado. A medição FF não separa fisicamente vibração de tampo de sala/microfone.
- O código é **MIT**, permitindo estudo e possível reutilização futura sob condições de notices/atribuição, **mas nenhum arquivo ou equação de implementação foi copiado** para Stage nesta rodada. Licença permissiva **não resolve** domínio de medições nem aceitação dos 7 gates.

### H03 — Ponto de atenção sobre a fonte Iowa (evitar calibrar com rótulos errados)

- O autor do Dussek declara, em `data/SOURCES.md`, **possíveis inconsistências de nota nos arquivos originais de Iowa** (nomes A0/Bb0/B0 e pp C1). O MF-1 relata seu próprio desvio de afinação do arquivo A0. **São relatos de autores externos**, não confirmação pelo nosso comparador; as interpretações não são perfeitamente equivalentes.
- Antes de usar gravações Iowa: baixar fontes originais autorizadas em processo isolado, verificar hash e fundamental/partials por nota, checar 3 intensidades, reportar mapeamento e desvios com instrumento/piano exato, SEM substituição automática de notas.
- A origem Iowa autoriza reutilização comercial de gravações, mas a variação de qualidade/erro de rótulo torna **medição cega de parâmetros por nome de arquivo inaceitável**.

## 2. Correção relevante de direitos — Dryad CC0 ≠ artigo CC BY-NC-ND

### H04 — *Motor origins of timbre in piano performance* (Kuromiya et al., 2025)

- Registro oficial Dryad: https://datadryad.org/dataset/doi:10.5061/dryad.95x69p8z3 ; publicação de **10/09/2025**.
- Conjunto de dados atualmente listado: **`Code_Data.zip` 29,36 KB** e **`README.md` 3,18 KB**; tamanho total anunciado **32,54 KB**. Conteúdo descrito: `data_study1.mat` (features das teclas, velocidade/aceleração em escapamento, ruídos, relação com avaliações), `data_study2.mat` (teste de escuta), JSON de **posição da tecla**; scripts MATLAB para figuras.
- **Verificação da política diretamente com o publicador:** https://datadryad.org/terms (item 1.a, 4.a–b) e https://datadryad.org/publication_policy (1.a, 2.2.a) declaram que **datasets publicados na plataforma são disponibilizados sob CC0**. Isso **corrige a interpretação conservadora anterior**, que transferia a licença NC-ND do **artigo** aos **dados**. Licença do artigo publicado **não se transfere automaticamente ao depósito Dryad**.
- A declaração CC0 é **relevante para uso comercial**, mas requer verificar os arquivos originais para componentes externos/terceiros e privacidade e fazer a revisão jurídica do produto; softwares ou anexos depositados em **Zenodo separado** podem ter outra licença.
- **Integridade/acesso não concluídos:** a página apresenta nomes/tamanhos, mas o download dos arquivos pelo navegador de pesquisa respondeu **403** e **nenhum ZIP/README foi adquirido, hasheado ou executado**. Não há áudio bruto nem contato F_h(t) ou Y_bridge(f) declarado. Se for útil ao Stage, seria **M09 perceptivo/de tecla**, não M01 martelo nem M04 ponte. Não acrescentar ao acervo de 50 áudios originais.

## 3. Fontes descartadas/retidas apenas como bibliografia, com motivo concreto

| Fonte | Conteúdo confirmado na página primária | Bloqueio |
| --- | --- | --- |
| Zenodo 11654054, *Acoustic cues of keyboard mechanics enable auditory localization of upright piano tones* (Fontana et al., 2024), https://zenodo.org/records/11654054 | 3 arquivos totalizando **206,7 KB**: `Piano localization dataset.pdf` (62,2 KB), `response.df.csv` (126,4 KB), `response.df.RData` (18,2 KB); estudo de percepção/localização de tecla e ruídos mecânicos | É **dataset de respostas de experimentos**, não gravações de ruído/impactos individualizados nem vibrações de cordas. Página web consultada não apresentou texto da licença de forma verificável; **não aprovado** para calibração comercial. |
| Zenodo 19825813, *Piano Sustain Pedal Acoustic Feature Dataset*, 2026 v2, https://zenodo.org/records/19825813 | **30.257 observações, 70 colunas** de descritores pareados, CSV **39,8 MB** e ZIP de áudios **368,4 MB**. Autor afirma origem em **piano VST** + MIDI a partir de obras de Chopin disponibilizadas por terceiro | Não é medição de **abafadores, ressonância simpática ou meio-pedal de piano real**. Licenças de VST, obras/performances/MIDI e derivados não verificadas; não baixar para calibrar Stage comercial. |
| Zenodo 15659089, ISMIR 2025 *High-Resolution Sustain Pedal Depth Estimation*, https://zenodo.org/records/15659089 | Features HDF5 de áudio real e renderizado com **Pianoteq 8** e MIDI **MAESTRO**; autores dizem ter obtido permissão para **distribuir as features conforme MAESTRO** | Permissão para o publicador disponibilizar **features** não prova autorização de usar como treinamento/calibração do nosso **produto comercial** nem como verdade física do pedal. Não incluir no pipeline. |
| Stulov, *Experimental and computational studies of piano hammers* (2005), https://www.ioc.ee/~stulov/actaa2005.pdf | Descreve dispositivo para força/deformação em superfície rígida, variando martelos, umidade, voicing e parâmetros de histerese | Texto científico útil para desenhar M01.1; **impacto contra corpo rígido difere do contato com corda**; sem sinais originais adquiridos/licenciados. |

## 4. Matriz de evidência: não inflar contabilidade

| Elemento | Estado após esta rodada |
| --- | --- |
| WAV/FLAC de pianos acústicos originais com hash verificado previamente | **50 arquivos / seis pianos, sem novos áudios** |
| Arquivos físicos originais F_h(t), δ(t), H/V das cordas, Y_ponte 2×2 | **Nenhum novo adquirido** |
| Modelos numéricos externos com origem/ licença textual verificada | **Dussek Grand B CC BY 4.0, 88 notas; MF-1 MIT com tabelas de notas amostradas**. Nenhum importado ou validado pelo Stage. |
| Dryad de movimento de tecla | **CC0 confirmado na política do repositório**, dois arquivos listados, bytes e conteúdo interno não verificados; apenas M09 |
| Licença do código externo AGPLv3 vs MIT | **Verificada nos arquivos LICENSE de cada projeto**, mas aplicação ao nosso produto exigiria decisão jurídica/arquitetural |
| R-GATE-1..7 | **0/7 globalmente completos** |
| Stage Synth P1/P2/DSP/UI/MIDI/FX/presets | **Nenhuma alteração autorizada ou executada** |
| 32–64 vozes em Chrome/PC/Moto g04s | **Não homologadas** |

## 5. Próxima ação com melhor relação esforço/benefício

1. **Priorizar dados numéricos de piano já licenciados:** antes de adquirir centenas de MB, validar `instruments/grand_b/data.bin` por SHA256 com fonte original e documentação de campos, sem copiar valores para o Stage; classificar quanto é **métrica extraída do áudio** vs assumido/ajustado, e se o modelo oferece reprodução verificável dos parâmetros.
2. **Dryad M09:** obter os dois arquivos originais por canal permitido, hash e inspecionar somente movimento da tecla/percepção; não usar a biblioteca de código e suas dependências sem revisão. Manter metadados e direitos separados das séries de sensores de martelo/ponte.
3. **Física independente continua P0:** buscar F_h(t) e matriz Y_ponte 2×2 em **um mesmo piano**, por instituição com direito comercial ou medição própria; nem Dussek nem MF-1 demonstram que a mediram.
4. **Preparar futuramente um laboratório offline independente** para comparar modelos hipotéticos e reportar erros, porém não criar ou integrar DSP, filtros, presets ou executáveis por conta do congelamento.
5. Consultar o titular antes de qualquer decisão de reutilizar código MIT/AGPL, parâmetros CC BY/SA ou contratar medições; todas as mudanças exigem preservar a v1.9.5 e obter validação real antes de promover A/B/C.

**Resultado científico:** as descrições de modelos completos podem orientar a nossa arquitetura e metodologia, mas as medições físicas críticas ainda não foram obtidas. O avanço mais relevante desta rodada é a distinção auditada **licença de código × licença dos presets × licença dos dados reais × licença do artigo**.
