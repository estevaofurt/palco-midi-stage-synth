# Stage Synth — Política de referências e licenças para SOFTWARE COMERCIAL

**Decisão do titular do projeto (22/11/2026): o Stage Synth é destinado a comercialização.**
**Base conferida:** \`main\` commit \`c85e3e8ab238d6a435af6cf55ffa850e4ea34a97\`, app v1.12.4.
**Status:** congelamento de DSP/P1/P2 mantido. Este documento altera exclusivamente critérios de pesquisa, legalidade e seleção de dados, não o motor.

## 1. Regra de trabalho obrigatória

1. Fonte científica aberta para **LER** e estudar a física **não é automaticamente um áudio/arquivo de dados autorizado para uso num produto comercial**. Podemos aprender métodos/equações dos artigos, com citações e sem copiar código ou tabelas protegidas em excesso.
2. Para baixar, copiar, adaptar, extrair características, usar no desenvolvimento/calibração/treinamento/testes de um software comercial, priorizar fontes que permitem explicitamente tal finalidade: **CC0; CC BY 3.0/4.0 com atribuição; domínio público do titular verificável; ou licença comercial específica por escrito**. Conferir arquivo e proveniência, não apenas o rótulo do site.
3. Conjuntos **CC BY-NC, CC BY-NC-SA, CC BY-NC-ND, research-only, personal-use-only, evaluation-only** ficam **NÃO APROVADOS para o pipeline comercial de desenvolvimento/calibração** enquanto não houver autorização adicional adequada. O fato de os samples não irem no produto NÃO é uma permissão automática para seu uso na etapa de calibração comercial. Esta política é prudencial, não conclusão judicial geral sobre todos os usos possíveis.
4. Bibliotecas comerciais sob contrato **não** autorizam automaticamente extração de samples, treinamento, reverse engineering do banco, distribuição de áudio ou calibração; revisar o EULA antes de qualquer uso além de escuta permitida.
5. Não confundir **licença de WAV/sample**, **licença do código do software**, **direitos sobre marcas/modelos** e **eventuais patentes**. Os nomes Yamaha, Steinway, Bösendorfer e outras marcas não devem implicar associação oficial, patrocínio ou endosso. Nomes de presets "Japanese/American" são genéricos, e o nome comercial futuro requer análise própria.
6. Aprender uma equação física não significa infringir a licença de um conjunto de gravações, mas copiar uma implementação GPL/AGPL para código proprietario sem análise de compatibilidade é outro risco. Não incorporar código externo sem registrar licença específica.
7. **Manter arquivo bruto, hash, versão de licença, atribuições, transformações e histórico de decisões** para todo dado elegível. Não copiar gravações privadas do usuário para repo nem versões redistribuíveis.

## 2. Licenças Creative Commons — condição verificada nos autores

- [Creative Commons CC0](https://creativecommons.org/publicdomain/zero/1.0/deed.en): permite copiar, modificar e explorar inclusive comercialmente; a declaração não elimina direitos de terceiros, marcas ou direitos de personalidade.
- [Creative Commons CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.en): permite uso comercial com atribuição adequada, aviso de licença, link e indicação de alterações; verificar também direitos de terceiros que não estejam licenciados. Para CC BY 3.0 conferir os respectivos termos.
- [Creative Commons CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): proíbe uso comercial no âmbito da licença; exigir autorização específica para usos comerciais.
- [Creative Commons CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en): restringe a uso não comercial e impõe condições de compartilhamento de adaptações.
- Publicação acadêmica/científica ou download de dados **não** equivale a sublicença comercial.

**Não é parecer jurídico.** Para lançamento pago, acordos de datasets, direitos conexos e uso de marcas, fazer revisão jurídica de distribuição no Brasil e em outros mercados-alvo.

## 3. Reclassificação dos acervos de pianos

| Acervo | Licença/termos verificados | Status para calibração comercial | Observação física |
|---|---|---|---|
| **VCSL Versilian** | [Fonte da criadora](https://versilian-studios.com/vcsl/) declara **CC0** e uso em *commercial software* | **CANDIDATO ELEGÍVEL**, conferir cada instrumento/arquivo de origem | Steinway B e Knight Upright originais WAV, camadas não controladas fisicamente |
| **VCSL Keys** | [Fonte da criadora](https://versilian-studios.com/vcsl-keys/), CC0 como derivado VCSL | **CANDIDATO ELEGÍVEL**, conferir conteúdo e origem | Banco de instrumentos de teclado; não necessariamente adequada física bruta |
| **Salamander Grand Piano Yamaha C5** | [Autor/distribuidor](https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html#Salamander) e [SFZ Instruments](https://sfzinstruments.github.io/pianos/salamander/), **CC BY 3.0** | **CANDIDATO ELEGÍVEL** com atribuição a Alexander Holm e controle da proveniência | Obter 48k/24b original WAV/FLAC, não AAC editado, 16 layers; C5 ≠ CFX |
| **bitKlavier Grand / Steinway Model D** | [Autor](https://bitklavier.com/the-bitklavier-grand/) declara **CC BY 4.0** | **CANDIDATO ELEGÍVEL** com atribuição/avisos | 16 layers, 9 pares estéreo, 96k/24b; amostras denoised/editadas/ganho ajustado; Model D ≠ B |
| **Fuchs & Möhr Felt / Tom Guder** | [Declaração do criador](https://www.polyphone.io/en/forum/your-creations/850-acoustic-felt-piano-upright-fuchs-mohr) como **public domain**, samples WAV em três layers | **CANDIDATO ELEGÍVEL**, arquivar prova da declaração e conferir cadeia de direitos do espelho | Não identifica física do feltro sem comparação mesmo piano com e sem feltro |
| **Upright Kawai KW FreePats** | [Autor/distribuidor](https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html#UprightKW), **CC0** | **CANDIDATO ELEGÍVEL** | Gravações de sala e loops nos graves — inadequado para calibrar T60 natural de cordas |
| **Steinway Model B Iowa** | [Universidade](https://theremin.music.uiowa.edu/MIS.html) permite usos amplos, mas não identificamos licença CC/SPDX formal explícita | **PENDENTE jurídico** para desenvolver/distribuir comercialmente; pedir esclarecimento se necessário | 9 arquivos AIFF E0, sala não anecoica; pp/mf/ff não são velocity calibrada |
| **BiVib Yamaha Disklavier** | [Zenodo](https://zenodo.org/records/2573232), artigo identifica **CC BY-NC-SA 4.0** | **NÃO APROVADO para calibração comercial** sem licença comercial escrita do titular | Alta qualidade científica; pode citar publicação sem usar áudio sob termos NC |
| **RWC Musical Instrument Sound DB** | [Autores/reedição Zenodo 2026](https://zenodo.org/records/17170844), **CC BY-NC 4.0** | **NÃO APROVADO para calibração comercial** sem licença específica | Yamaha/Steinway/Bösendorfer, articulações, dados originais ainda não preparados |
| **MAPS ENSTDkCl/ENSTDkAm** | [Telecom Paris](https://adasp.telecom-paris.fr/resources/2010-07-08-maps-database/), documentação anterior reportou licença NC de redistribuição | **NÃO APROVADO até conferir texto original e obter autorização comercial** | Só os subconjuntos ENSTD são acústicos reais; outro conteúdo é simulado |
| **MAESTRO v3** | [Google Magenta](https://magenta.tensorflow.org/datasets/maestro), licença **CC BY-NC-SA 4.0** | **NÃO APROVADO para calibração comercial** sem licença específica | Performances MIDI/audio para validação de expressão, não notas secas |
| **CCMusic** | [Espelho/autor](https://huggingface.co/datasets/ccmusic-database/pianos), reportou **CC BY-NC-ND 4.0** | **NÃO APROVADO** sem licença comercial autorizada e checagem de fonte original | Avaliações subjetivas e pianos variados |
| **Plath/Hamburgo bridge/pressure dataset** | [Zenodo](https://zenodo.org/records/3274772), **licença ainda não demonstrada textualmente nesta auditoria** | **PENDENTE até licença comercial escrita/clarificação** | Pressão e aceleração, mas força é tecla-base, NÃO driving point da ponte |
| **QMUL Liang et al. pedal contínuo** | [Zenodo](https://zenodo.org/records/3237929), **licença exata não verificada nesta auditoria** | **PENDENTE** para calibração comercial | Controle contínuo valioso mas áudio polifônico |
| **Yamaha CFX Synchron Vienna / GSi Venice CFX** | Produto e biblioteca **comerciais**, EULAs próprios, sem licença livre de samples | **SOMENTE escuta legal sob licença aplicável**; não copiar sample, reverberação/IR, mapeamentos nem conteúdo proprietário | CFX real, mas processamento e FX de demonstrações impedem inferência de parâmetros brutos |

Legenda: **CANDIDATO ELEGÍVEL ≠ pronto para produção**. Falta conferir versão, arquivo específico, atribuição, direitos conexos/terceiros, transformações, manifest e qualidade física. "Não aprovado" aplica-se ao **uso das gravações/dados no fluxo comercial**, não à leitura da literatura acadêmica.

## 4. O que pode ser feito sem violar o congelamento do DSP

- Montar um **corpus comercialmente seguro** a partir de WAV/FLAC originais da VCSL (CC0), Salamander (CC BY 3.0), bitKlavier (CC BY 4.0), Kawai KW (CC0) e WAVs do autor Felt com prova de PD; armazenar apenas onde direito e propósito estiverem corretos, sem upload ao GitHub.
- Priorizar **medições próprias** de piano acústico, gravadas com consentimento/licença contratual que autorize expressamente calibração e uso comercial de dados e de parâmetros derivados. Ideal: notas únicas com 5 ou mais regiões, 3 ou mais velocities observáveis, pedal, mic e sala documentados, mesmo piano com feltro e sem feltro, e medição de FRF ponte (força aplicada diretamente na ponte/velocidade).
- Solicitar **licença comercial** aos autores de BiVib/RWC caso seus dados sejam imprescindíveis; não estimar que autorização acadêmica valha para produto pago.
- Estudar artigos físicos de Smith, Bank, Weinreich, Chabassier, Plath/Ege e modelos passivos. **Escrever implementação original independente e registrar fórmulas/parâmetros com fonte** quando autorizado recomeçar o DSP.
- Preparar uma página de **ATTRIBUTIONS/THIRD_PARTY_NOTICES** para o produto antes de distribuir ou incluir qualquer WAV externo CC BY, com nomes, versão, URLs, licença e modificações.
- Obter avaliação de licenças dos **assets já versionados**, dependências e eventual código/procedência externa (adaptação de Claude, Bibliotecas GPL/AGPL). O repositório **não tem arquivo LICENSE na raiz** na consulta de 22/11/2026; a licença de distribuição do código do Stage deve ser decidida pelo titular antes de comercializar. O \`package.json\` contém \`"private": true\` (flag npm, **não** licença de uso).
- Avaliar marcas registradas Yamaha, Steinway e outras; não afirmar endosso de fabricantes nem usar logotipos sem direito.

## 5. Novo gate obrigatório de licenças COMERCIAIS

**R-GATE-3 se torna BLOQUEIO LEGAL COMERCIAL**:
- [ ] Todo corpus que será usado para desenvolver/calibrar/validar o Stage comercial tem origem e licença **explicitamente compatíveis com uso comercial**, ou permissão por escrito dos titulares;
- [ ] Nenhum conjunto NC/research-only será baixado para uso no pipeline do produto sem autorização/avaliação específica;
- [ ] Cada sample tem manifesto (arquivo/hash, origem, autor, versão, licença e atribuição);
- [ ] Distinção entre referência de escuta (produto comercial sob EULA), sinal de calibração, asset distribuído, método acadêmico e código;
- [ ] Direitos de reprodução/redistribuição e marcas definidos antes do lançamento pago.
- [ ] Nenhum novo motor ou fase de DSP é autorizado até liberar também R-GATE-1..7 e obter acordo explícito do usuário para retomar.

**Situação atual:** R-GATE-3 **NÃO APROVADO**, e a prontidão geral permanece **0/7 R-GATEs integralmente comprovados**.

## 6. Referências primárias

- CC oficiais: https://creativecommons.org/licenses/by/4.0/deed.en ; https://creativecommons.org/licenses/by-nc/4.0/ ; https://creativecommons.org/publicdomain/zero/1.0/deed.en
- VCSL: https://versilian-studios.com/vcsl/ ; VCSL Keys: https://versilian-studios.com/vcsl-keys/
- Salamander: https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html#Salamander
- bitKlavier Grand: https://bitklavier.com/the-bitklavier-grand/
- Felt Tom Guder: https://www.polyphone.io/en/forum/your-creations/850-acoustic-felt-piano-upright-fuchs-mohr
- RWC: https://zenodo.org/records/17170844
- BiVib: https://zenodo.org/records/2573232
- MAESTRO: https://magenta.tensorflow.org/datasets/maestro

**Decisão final:** referências acadêmicas NC permanecem úteis para estudar o conhecimento científico publicamente descrito, mas NÃO entram como fonte de calibração comercial enquanto faltar permissão. A pesquisa futura deve privilegiar CC0/CC BY/origem própria licenciada. O motor continua congelado.
