# Piano V4 — CATÁLOGO DE DADOS EXPERIMENTAIS REAIS PARA FECHAR LACUNAS

**23/11/2026.** Anexo à [auditoria das 18 lacunas](PIANO_V4_AUDITORIA_LACUNAS_CONHECIMENTO_2026-11-23.md). **Somente catálogo de pesquisa**: nenhum áudio de terceiros foi baixado, copiado ao repositório, utilizado na síntese ou incorporado ao motor. Identificar direitos de utilização ANTES de transferir arquivos e publicar derivados. Os autores mediram instrumentos específicos, não a escala universal de um piano.

## A. Opção prioritária para análise multissensor: Niko Plath / University of Hamburg

**Influence of Playing on the Tonal Characteristics of a Concert Piano — Dataset**, ISMA 2019, Zenodo https://zenodo.org/records/3271370 (v1.0.0, 2019; o registro aponta nova versão, mas não inspecionamos ainda as diferenças de versão). DOI 10.5281/zenodo.3271370.

**O que realmente existe nessa versão:**
- Notas individuais, até 5 tomadas, medidas antes e após um ano de execução do mesmo instrumento; teste de percepção com aproximadamente 100 pianistas, técnicos e construtores.
- CSV por nota/tomada com taxa **50.000 amostras/s** e **quatro canais simultâneos**:
  1. tempo em segundos;
  2. **força em N do impacto tecla–fundo de tecla**, sensor Kistler 9722A500 (NÃO é força de contato martelo–corda);
  3. **aceleração em m/s² na região da ponte**, sensor PCB 352C23, direção normal ao tampo (NÃO é pressão de microfone nem velocidade direta);
  4. **pressões acústicas em Pa**, canais esquerdo/direito da cabeça artificial HSU 3.2 na posição do pianista.
- Arquivo do registro inicial de **4,6 GB**, não baixado. Há versão posterior; revisar metadados e licença antes de obter dados.
- Nota sobre limite: o impacto da tecla no fundo é um evento mecânico diferente do choque feltro–corda; a aceleração deve ser integrada/derivada com cuidado de DC, fase e ruído para obter mobilidade; não presumir que todos os sinais medem a mesma força física.
- **Uso de pesquisa recomendado:** alinhar temporalmente movimento da ação, início de vibração na ponte e chegada ao ouvinte; diferenças antes/depois do ano; verificar ataque e correlação de pressão/percussão. NÃO identificar diretamente \`F_ponte\` apenas pela força na tecla.
- Lacunas ajudadas: K02 (parcial), K07, K08, K09, K11, K12, K17. Não fecha K03 nem K05 diretamente.

## B. BiVib — som binaural E vibração do teclado, 10 dinâmicas

**Papetti, Avanzini & Fontana: BiVib Audio-Tactile Piano Sample Library**, Zenodo v0.9.1 https://zenodo.org/records/2573232, DOI 10.5281/zenodo.2573232, 2019.

- Duas unidades **Yamaha Disklavier**, sendo um piano de **cauda** e um **vertical**, tocadas de forma controlada; dez níveis de MIDI velocity por tecla.
- Contém **som binaural** e **vibração medida no teclado**, com informações dos sensores/microfones e possibilidade de converter para grandezas físicas em documentação complementar.
- **Não confundir vibração do teclado com vibração medida diretamente na ponte ou no tampo**.
- Dataset volumoso (~33,1 GB), não baixado. A descrição disponibiliza também configuração de sampler/Kontakt, que **não será utilizada como gerador de áudio no V4**.
- Uso recomendado: variação de timbre com intensidade e diferenças entre vertical/cauda, percepção de ação/teclado, ataque e dinâmica de notas. Por ser uma biblioteca nomeada como 'sample library', manter separação de pesquisa **absoluta** da síntese: no motor V4 nunca serão lidos esses samples.
- Lacunas ajudadas: K01 (dados de instrumento conhecido), K02 (apenas MIDI controlado), K07, K09, K11, K13 (se houver sinal pedal documentado; **não pressupor**).
- Antes do uso: verificar a licença específica e documentação dos canais; repositório aberto não equivale a licença irrestrita para redistribuir.

## C. Iowa Electronic Music Studios — referência de áudio com proveniência

**University of Iowa Musical Instrument Samples — Piano**, https://theremin.music.uiowa.edu/MISpiano.html.

- Página atribui as gravações a **Steinway & Sons modelo B**, sessão em 2001, registra performer, técnico, microfones **Neumann KM 84**, formato **16-bit/44,1 kHz**, estéreo, e posição aproximada dos dois microfones a **8 polegadas acima das regiões de cordas graves/agudas**.
- Há notas em **pp, mf, ff**, incluindo C4, mas a gravação do piano foi realizada em **ambiente não anecoico**. Esses são metadados de captura conhecidos, mais úteis que um arquivo WAV de identidade desconhecida.
- NÃO há canais de força de martelo, aceleração de ponte ou velocidade de tampo publicados nessa página. Impossível separar fisicamente cada mecanismo pela gravação.
- O sítio permite disponibilidade de gravações, mas **não encontramos licença CC/open-source explicitamente atribuída às gravações**; confirmar permissões para análise, redistribuição e derivados. Não publicar no repo.
- Lacunas ajudadas: K01 (alvo nomeado e cadeia de captura), K09, por comparação EXTERNA; não fecha K03–K06.

## D. Dados de percepção de ruídos mecânicos (2024)

**Fontana, Järveläinen, Papetti & De Pra: Acoustic cues of keyboard mechanics enable auditory localization of upright piano tones**, DOI Zenodo https://zenodo.org/records/11654054 (2024).

- O depósito consultado contém **respostas experimentais CSV/RData** e documento metodológico, **não uma biblioteca bruta multicanal que possamos assumir pronta**.
- É útil para elaborar protocolo de teste de percepção/localização do som mecânico, em vez de adicionar ruído ad hoc para parecer piano.
- Lacunas ajudadas: K09 e K11; precisa avaliar desenho experimental antes de generalizar.

## E. Ordem de coleta e procedimentos de integridade

1. **Sem baixar coleções inteiras automaticamente.** Começar por metadados/licença, canais físicos e tamanho de arquivo; priorizar trecho C4 pp/mf/ff no dataset que disponibilizar extração parcial autorizada.
2. **Proveniência e separação de papéis**: gravação externa é medida/objetivo de validação, NÃO uma camada sonora da física. Código do sintetizador nunca importa AIFF, WAV, SoundFont, IR de terceiro nem faz convolution sample playback.
3. Na análise cruzada, distinguir **força N tecla–keybed**, **aceleração m/s² na ponte**, **vibração do teclado m/s²**, **pressão Pa microfones** e **velocidade m/s** da ponte; não tratar unidades distintas como um mesmo sinal.
4. Registrar \`instrumento, nota, dinâmica, amostragem, sensores, posicionamento, sala, licença, edição e proveniência\`; checksum dos arquivos permitidos, sem publicá-los.
5. Calibrar eventos e delays (impacto tecla vs martelo–corda vs ponte vs mic) por posição; filtro/integração de aceleração não são neutros e exigem faixa de frequência/controle de fase.
6. Separar por instrumento, dinâmica, data e ambiente: não usar dados de um Steinway B (microfones próximos) para exigir o mesmo espectro de Disklavier cauda ouvido de cabeça artificial.
7. Protocolo de validação física: note C4 temporizada, energia por região, parciais e seus decaimentos, alterações pp/mf/ff, chegada do transiente ao mic. **Não alegar correspondência em N, Pa ou m/s sem instrumentação/calibração**.
8. Somente depois realizar ajustes no V4; **gates de escuta continuam obrigatórios**.

## F. Novas prioridades decorrentes

- **P0-DATA:** estudar e, se autorizado, analisar sinais sincronizados do conjunto de Plath (tempo, keybed, ponte, Pa), com atenção ao fato de não haver sensor martelo–corda. Alto valor na identificação de perdas da cadeia.
- **P0-PERCEPTION:** preparar referência de C4 em vários níveis de dinâmica com metadados e direitos, de um instrumento só, sem misturar condições de microfonação.
- **P1-DYNAMICS:** comparar BiVib cauda vs vertical sob MIDI velocity controlado, sem alterar o motor V4.
- **Ainda precisa piano real ou ensaio especializado:** deformação/histerese do feltro do martelo C4 específico, força instantânea da ponte, mobilidade complexa medida por força/velocidade no ponto C4 e geometria material da estrutura.

**Conclusão:** agora temos opções de dados experimentais reais para investigar várias lacunas da V4 sem começar por construções arbitrárias. Nenhum desses arquivos é, por si, uma especificação completa de um instrumento nem autoriza amostragem no motor.
