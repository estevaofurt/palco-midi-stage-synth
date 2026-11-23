# Stage Synth — auditoria de referências científicas de pianos acústicos

**Consulta:** 22/11/2026 (Brasil; disponibilizações e logs UTC de 23/11).
**Base auditada:** main 6eb2001989dec3580d3ff3475e848274984f7514 (Stage Synth v1.12.4).
**Escopo:** curadoria de fontes **primárias acadêmicas e oficiais**, condições de captura, licenças e estratégia E1. **Nenhum áudio foi baixado nesta auditoria, nem DSP/UI/MIDI/FX/preset foi alterado.**

## Por que elevar a exigência

O estudo anterior E0 realmente processou 33 notas de Iowa Steinway B (9 AIFF), Salamander Yamaha C5 (9 **AAC reempacotados**), VCSL Knight Upright (6 AAC) e Fuchs & Möhr Felt (9 WAV reempacotados), com um único valor speed=80/127 para os motores A/B/C, ao passo que pp/mf/ff e as camadas de fontes não têm equivalência de velocidade do martelo demonstrada.

Os erros médios de forma espectral E0 (ex.: C2 Steinway B/C ~38 dB contra A ~17 dB) são **apenas diferenças de amplitudes relativas dos parciais numa janela escolhida**; não são evidência de qual motor "soa mais piano". Podem refletir diferenças de microfone, resposta de ambiente, processamento dos arquivos, velocity, detecção de fundamental/harmônicos ou fase. Sem *matched excitation* e *matched mic/radiation*, **não otimizar DSP para diminuir esse único número**.

A avaliação física rigorosa requer ao menos: piano físico realmente identificado; notas de uma mesma tecla em dinâmica reproduzível; áudio PCM sem perdas, sem normalização e cortes que comprometam cauda; registro de posições de microfone/ambiente; estado do pedal, tempo de press/release, afinação real, licença clara; idealmente vibração/pressão calibrada e publicação acadêmica.

## 1. BiVib — PRIORIDADE MÁXIMA para força/velocidade e resposta acústica

**Fonte dos dados:** https://zenodo.org/records/2573232
**Artigo técnico revisado:** Papetti, Avanzini e Fontana (2019), *Design and Application of the BiVib Audio-Tactile Piano Sample Library*: https://www.mdpi.com/2076-3417/9/5/914
**DOI:** 10.5281/zenodo.2573232.

Dois Yamaha Disklavier **acústicos reais**:
- Cauda **DC3 M4** (Padova, Itália), sala laboratorial ~6 × 4 m.
- Vertical **DU1A** (Zurique, Suíça), sala com tratamento acústico ~4 × 2 m.
- **88 teclas × 10 velocidades MIDI** controladas por piano eletromecânico. As velocities foram escolhidas no intervalo **12 a 111**, devido à resposta inconsistente fora desse intervalo.
- **WAV PCM 24 bits / 96 kHz**, captação binaural com cabeças artificiais KEMAR 45BM (cauda) e Neumann KU100 (vertical) próximas da posição dos ouvidos do pianista. **Três configurações de tampa por piano**.
- Registro adicional de **aceleração/vibrações no teclado**; equipamento, calibração nominal, níveis elétricos e cadeia de aquisição documentados. **Sem normalização de amplitude nem processamento dinâmico**.
- Procedimento removeu silêncio do começo; pre-roll e envelope inicial devem ser avaliados antes de tomar um tempo de ataque como verdade física. O vertical tem limite eletromecânico ~17 s no tempo de tecla pressionada; não inferir T60 de notas graves a partir da cauda truncada.
- **Não anecoico**; as salas e a geometria de microfone afetam espectro e decaimento.
- Dados **~33,1 GB**, múltiplos arquivos 7z multipartes, relativamente dispendioso adquirir um banco completo. Não baixar sem justificar armazenamento/banda. Artigo e metadados podem ser consultados sem áudio.
- **Licença CC BY-NC-SA 4.0** informada no artigo. Usar para pesquisa compatível com termos; **não incorporar WAV ao Stage nem redistribuir em produto comercial**.

**Aplicação Stage:**
1. Projeto-padrão para derivar mapeamento *velocity MIDI → brilho, amplitudes relativas de parciais e ataque* por região, porque existem dez níveis controlados.
2. Comprovar como a radiação binaural e a tampa alteram som ouvido; não usar os filtros do mic como constantes intrínsecas de corda.
3. Comparar **Yamaha cauda versus Yamaha vertical** de maneira mais controlada que as amostras Knight/Kawai AAC.
4. O sinal de vibração de **teclado** não equivale à vibração da ponte ou à força exata martelo–corda; registrar isso nas conclusões.

## 2. RWC Musical Instrument Sound Database — PRIORIDADE MÁXIMA para Steinway, Yamaha e Bösendorfer reais

**Reedição acadêmica com licença:** https://zenodo.org/records/17170844
**Artigo original:** Masataka Goto et al., ISMIR 2003. Pôster: https://ismir2003.ismir.net/posters/Goto1.pdf
**Estudo de metodologia:** https://staff.aist.go.jp/m.goto/PAPER/ICA2004RWCMDBgoto.pdf

- Captura **três instrumentos de fabricantes distintos: Yamaha, Bösendorfer e Steinway**. Não assumir modelos específicos de piano sem consultar a documentação individual dos arquivos.
- **3 pianos × 88 teclas × 4 estilos (normal, staccato, pedal, repetição) × 3 intensidades (p, mf, f) = 3.168 sons individuais**. O pacote foi gravado em WAV mono a 16 bits/44,1 kHz; alguns arquivos concatenam notas com intervalos de silêncio e precisam de segmentação validada.
- Articulação, release e pedal tornam esse conjunto especialmente importante para testar os fenômenos ausentes no nosso motor (abafador, *repeated notes*, sustain), e o **Steinway real** é uma comparação independente da gravação de Iowa.
- "p, mf, f" são rótulos de intensidade, **não velocidades MIDI/velocidades físicas do martelo registradas com fidelidade instrumental**.
- **Licença da reedição de 2026: CC BY-NC 4.0**, registrada pelos mantenedores no Zenodo. Versões históricas exigiam termo de compromisso: para qualquer uso aplicar **as condições da versão efetivamente acessada** e manter atribuição; não redistribuir amostras em produto comercial.
- Excelente para caracterização do **piano por modelo de fabricação e articulação**, mas não fornece medições binaurais calibradas equivalentes às do BiVib.

## 2A. bitKlavier Grand — STEINWAY MODEL D REAL, PRIORIDADE ALTA para timbre American e microfones

**Fonte autoral e downloads (Princeton, Dan Trueman e equipe):** https://bitklavier.com/the-bitklavier-grand/
**Depoimento institucional:** https://cdh.princeton.edu/blog/bitklavier-30-an-interview-with-professor-dan-trueman/

- **Steinway Model D** real novo, gravado em janeiro de 2021 no Taplin Auditorium, Princeton, com **18 canais / 9 pares estéreo** incluindo Piano Bar (Earthworks, próximo ao martelo e cordas), Harp Omni (DPA 4060 junto à harpa), Lip Cardioid, palco, plateia e binaural (Neumann KU100 na posição do pianista).
- **16 camadas de velocity** nas **notas amostradas a cada terça menor** começando no A0. Assim, **não são 88 notas gravadas individualmente**: outras são transpostas no sampler. Há sons separados de soltar martelo, ressonâncias de release e pedais.
- Amostras em 96k/24b, 88.2k/24b, 48k/24b, 44.1k/16b; download de coleções por imagem estéreo no Archive.org; **CC BY 4.0**, inclusive para criar instrumentos derivados com atribuição.
- **Limitação física fundamental:** as sessões foram **denoised (iZotope RX8)**, recortadas com fades, seleção por RMS e **reequilibradas em ganho (normalmente variações <2 dB)** para homogeneidade de velocity e teclado; **não usar amplitude de arquivos como medição direta da força/massa do martelo**. Os registros podem conter reverb do auditório. Ainda sim são excelente referência para corpo, timbre, expansão espacial e detalhes de pedais/release.
- Para **American Stage**: usar Piano Bar / Harp Omni como referência de radiador próximo, e binaural/House ORTF como condições de escuta alternativas; **a diferença entre posições é dado sobre microfonação, não um erro intrínseco de corda**.
- Mais útil que Steinway B Iowa para caracterizar **especificamente Model D** e testar múltiplos radiadores. Complementar RWC para verificar um Steinway real não editado/não nivelado no mesmo padrão artístico.

## 3. MAPS (ENSTDkCl / ENSTDkAm) — PRIORIDADE ALTA para MIDI controlado e captação

**Grupo de pesquisa original (Telecom Paris):** https://adasp.telecom-paris.fr/resources/2010-07-08-maps-database/
**Reedição identificada no Zenodo:** https://zenodo.org/records/18160555
**Metodologia de experimentos:** https://www.mdpi.com/2076-3417/7/9/901

- Base do grupo de V. Emiya/B. David com notas isoladas, acordes e peças completas, ground-truth MIDI e WAV.
- **Somente duas condições acústicas reais**: **ENSTDkCl (close)** e **ENSTDkAm (ambient)**, de piano Yamaha Disklavier; **os outros sete subconjuntos são pianos sintetizados**, inclusive Steinways e Bösendorfers virtuais — **não tratá-los como pianos reais**.
- Estudo publicado identifica o instrumento real como **Disklavier vertical**, gravado em estúdio ~4 × 5 m, microfones a ~50 cm. Os subconjuntos isolados foram usados para moldes por nota e intensidades. O conteúdo inclui WAV e etiquetas MIDI (nota e velocidade).
- Os registros de captação close e ambient são **do mesmo instrumento**, não dois pianos independentes. Comparar os dois demonstra o impacto do ambiente e da distância na caracterização espectral.
- Conjuntos ENSTDkCl e ENSTDkAm da reedição pesam cerca de 2,6–2,7 GB cada; licença **CC BY-NC-SA 2.0 França**, **não incorporar áudio ao produto**.
- É fonte especialmente adequada para **teste A/B do mesmo MIDI sob diferentes microfones**, além de *pedal/chords* quando metadata permitir, mas **não** substitui identificação de martelo/ponte.

## 4. MAESTRO v3 — PRIORIDADE ALTA para audição musical, pedal e desempenho, NÃO para corda isolada

**Fonte autoral Google Magenta:** https://magenta.tensorflow.org/datasets/maestro
**Versão recomendada:** v3.0.0.
- ~198,7 h de performances em pianos **Yamaha Disklavier acústicos de concerto**, com pares MIDI/WAV sincronizados em torno de **3 ms**.
- Os MIDI incluem nota, velocity, **CC64 sustain, CC66 sostenuto, CC67 una corda**. Áudio estéreo PCM de 44,1–48 kHz, 16 bits.
- **101 GB compactados**; não baixar o corpus todo para caracterizar três notas. Muitos sons são **polifônicos**, com notas e pedais simultâneos, portanto impossíveis de atribuir com rigor a uma única corda apenas pela FFT.
- Licença **CC BY-NC-SA 4.0**, uso somente sob as condições legais.
- Usar após modelos de notas isoladas como **benchmark musical de percepção, articulação, dinâmica, acordes, sustain/CC, polifonia e repetição**.

## 5. KRAISLER (2026) — CANDIDATO para dry/studio/hall e pedal, permissões requerem validação

**Dataset:** https://zenodo.org/records/21082251
**Artigo:** https://reference-global.com/article/10.5334/tismir.338
- 20 trechos de duetos piano/violino executados por profissionais, com **stems de piano isolados** e versões **dry/studio/hall**, WAV PCM 16 bits/44,1 kHz, MIDI gravado no próprio Disklavier incluindo velocidades e pedal. As salas de captação foram isoladas entre os instrumentos; as versões studio/hall simulam reverberações.
- **Não oferece necessariamente notas isoladas**, mas tem vantagem para aferir a contribuição de reverb sem interferência do violino.
- Cerca de **1,6 GB** no pacote disponibilizado.
- **Alerta de licença:** a página Zenodo marca **CC BY 4.0**, mas o texto na própria descrição menciona **restrição a usos comerciais**; são declarações potencialmente conflitantes. **Não assumir liberdade comercial; confirmar diretamente com os responsáveis antes de incorporar ou redistribuir.** A pesquisa metodológica pode usar apenas metadados e artigos enquanto não houver resolução.

## 6. Materiais secundários que continuam úteis, mas NÃO são padrões de calibração de velocidade

**Yamaha C5 Salamander original, Alexander Holm**: https://github.com/sfzinstruments/SalamanderGrandPiano ; 48 kHz /24 bit, 16 camadas e microfones AKG C414 a ~12 cm, licença CC BY 3.0. Preferir **original FLAC/WAV**; versões mono AAC recortadas usadas em E0 só servem para triagem. Yamaha C5 **não é Yamaha CFX**.

**Steinway B University of Iowa**: https://theremin.music.uiowa.edu/MISpiano.html ; AIFF 44,1k/16 bit, pp/mf/ff, notas por tecla, microfones Neumann KM84 a ~8 polegadas e **gravação não anecoica**. A Iowa permite uso amplo em projetos mas **não declara licença CC/SPDX** e as notas pp/mf/ff não registram velocidades precisas de martelo. Continuar como controle independente, não fonte única de física. https://theremin.music.uiowa.edu/MIS.html

**Versilian Community Sample Library (VCSL)**: https://versilian-studios.com/vcsl/ ; **CC0** e arquivos originais WAV, pianos Steinway B NoSus close e Knight Upright. Preferir originais sem reamostrar/comprimir e inspecionar se as camadas foram normalizadas; pacote completo é grande, mas a licença é apropriada para testes e usos comerciais com os devidos controles de identidade de fonte.

**Fuchs & Möhr Felt Upright, Tom Guder**: https://www.polyphone.io/en/soundfonts/pianos/683-fuchs-mohr-felt-piano ; domínio público declarado pelo autor, três layers e WAVs. Seu felt é uma preparação de **piano vertical**; não substituir por piano de cauda. O controle de força física, o estado do instrumento e o processamento dos reempacotadores não são metrologicamente documentados como BiVib. Para construir uma física de felt confiável, é preciso **medir a diferença** do mesmo instrumento/posicionamento de feltro com e sem preparação ou uma captura calibrada; não temos esse par controlado.

**Yamaha CFX:** continua sem dataset científico aberto, original e controlado verificado nesta auditoria. **Steinway Model D:** está identificado no **bitKlavier Grand (Princeton)**, CC BY 4.0, 16 camadas e 9 pares de microfones, mas o áudio foi editado/denoised e nivelado. RWC identifica o fabricante Steinway, não um modelo específico; Iowa/VCSL são Model B. **Não confundir modelos nem tratar remasterização como medida física bruta.**

## 7. Outras referências que não entram no benchmark imediato

**PianoUPM**: artigo da Audio Engineering Society confirma 13 pianos acústicos diferentes, verticais e de cauda, 88 notas por instrumento, acordes e quatro intensidades para notas A. https://aes.org/publications/elibrary-page/?id=14690 ; página de download original atualmente retornou **HTTP 404 na verificação de 22/11/2026**: https://www.etsist.upm.es/estaticos/pianoupm/ . Não chamar acessível antes de localizar um espelho autorizado.

**Ressonância física de tampo**: estudos de impacto/posição na ponte podem fornecer funções resposta frequência e modos, mas sem liberação clara dos WAVs de medição não são bases prontas para colocar samples no Stage. https://www.mdpi.com/2624-599X/4/4/62

**Accurate-Salamander Grand Piano (2026)**: https://www.ir.isas.jaxa.jp/~cyamauch/AccurateSalamander/index.html ; remasterização de 641 samples, 16 layers 48k/24bit do Yamaha C5 original para consistência sonora. Serve como **referência de voicing e homogeneidade de um piano digital amostrado**, **não** observação física independente do C5. Não confundir sua correção de gain/retune com comportamento da corda original.

## 8. Matriz de confiança (para escolher conforme a pergunta)

| Fonte | Nota isolada | Velocity controlada | Gravação sem perdas | Documentação captação | Uso preferencial |
|---|---|---|---|---|---|
| BiVib Yamaha DC3 M4/DU1A | **Sim, 88** | **10 valores MIDI explicitados** | **WAV 96k/24b** | **Alta: binaural, sala, equipamentos, calibração** | **Martelo/dinâmica e radiador cauda/vertical** |
| bitKlavier Grand Steinway D | **Somente notas amostradas a cada terça menor** | **16 layers equalizadas/selecionadas, sem controle físico de hammer velocity** | **WAV até 96k/24b** | **Alta: 9 pares de microfones, pós-produção explicitada** | **Timbre Model D, imagem espacial, release/ruído** |
| RWC Yamaha/Steinway/Bösendorfer | **Sim, 88 cada** | **p/mf/f subjetivos** | **WAV 44.1k/16b** | Alta: fabricante/articulação, pacote/paper | **Identidade Steinway e variações de pedal/repetição** |
| MAPS real ENSTDkCl/Am | **Sim** | MIDI anotado/gerado | **WAV CD** | Boa: close/ambient, estúdio | **Correlações de MIDI, mic e transcrição** |
| Iowa Steinway B | **Sim, nota a nota** | pp/mf/ff não calibrados | AIFF 44.1k/16b | Boa, não anecoico | **Controle independente Steinway B** |
| VCSL Steinway/Knight original | Sim, amostras mapeadas | Camadas processadas possíveis | WAV original | Variável conforme instrumento | **Modelo sonoro e teste de licença CC0** |
| Salamander Yamaha C5 original | Amostragem de terceiras menores | 16 layers mapeadas | WAV/FLAC 48k/24b | Boa: microfones perto das cordas | **Yamaha C5, transientes e dinâmica relativa** |
| Felt Fuchs & Möhr | Sim | 3 layers, não calibrados | WAV disponível | Limitada | **Qualidade percebida da preparação em feltro** |
| MAESTRO / KRAISLER | **Notas geralmente polifônicas** | MIDI de performance com velocity e pedal | WAV de alta qualidade | Boa | **Aceite musical, pedal, dinâmica e reverb** |

**Importante:** O termo "sem perdas" não significa "sem ambiente", "não editado", nem "medição física absoluta" quando o microfone/gravação não foram calibrados. Nenhuma fonte, sozinha, torna as equações do nosso motor identificáveis sem estudo de limitações.

## 9. Protocolo E1 revisado: três bases de referência independentes antes de alterar motores

**Experimento 1 — rigidez e perdas de cordas:**
- BiVib Yamaha **cauda** (dados de 88 notas e 10 velocities) e **vertical**, no mesmo equipamento/condição de tampa para cada comparação;
- RWC Steinway e Bösendorfer como **verificação cruzada**; impedir que o Stage copie um único instrumento específico.
- Para primeira rodada, notas MIDI 36/48/60/72/84 e velocidades reais baixas/médias/altas conforme mapeamento disponível, sem inventar valores.
- Trilha de parciais com STFT multirresolução e estimador paramétrico em janelas variáveis, medindo f_n, diferença em cents, B com incerteza, envelope individual, *double decay* e batimentos; deixar nulos resultados sem SNR e parciais confiáveis.

**Experimento 2 — excitação e contato martelo:**
- Nas mesmas notas BiVib, confrontar ataque por 10 velocities. Usar RMS de trechos e relações harmônicas **sem normalizar arquivos independentemente**, checar a consistência do mapeamento velocity→velocidade física (controlador MIDI não mede o martelo diretamente);
- Estudar ruído, largura do ataque e amplitude/decay inicial para martelo não linear *fisicamente derivado*. Não escolher expoente de feltro por ajuste arbitrário de C4.

**Experimento 3 — corpo, espaço e acústica:**
- Comparar BiVib de tampa fechada, aberta e removida, canal esquerdo e direito, e piano cauda/vertical;
- MAPS close versus ambient e KRAISLER dry versus studio/hall, com **o mesmo piano**; estimar sensibilidade ao microfone/reverb; não equiparar "dry" a anecoico;
- RWC staccato/release/pedal/repetição para identificar amortecedores e interações, cuidando das legendas e das respostas da sala.

**Experimento 4 — integração ao Stage:**
- Só após modelos identificáveis, criar P2 isolado e comparar A (modal adaptado), B (v1.9.5 preservado), C (mecânico atual), P1 isolado e protótipo novo na mesma velocity/pitch/posição de saída quando plausível.
- Manter referências livres de áudio nos artifacts/repositório: apenas metadados, hashes, plots/valores espectrais que **não reconstruam** samples de terceiros. Controlar licença CC BY-NC/SA e proibição de redistribuição comercial.
- Não publicar nova categoria, link ou módulo no aplicativo. Se houver uma futura alternativa de motor aprovada, ela pertence ao seletor existente do piano acústico.
- Polifonia **32 notas mínimas, meta 64**, AudioWorklet 48k/128 e validação de CPU/estalos em PC/Chrome e Moto g04s. Não declarar hardware homologado por benchmark offline.

## 10. Estado da pesquisa e reavaliação de evidência

- A pesquisa acima **localizou fontes com documentação e autorização de download identificadas**; não realizou download dos arquivos BiVib/RWC/MAPS/MAESTRO. O total de 33 gravações **da E0 anterior** continua real e preservado em histórico, mas não são o nível máximo de confiabilidade necessário para inferir constantes físicas.
- **BiVib é a prioridade nº 1 para calibrar dinâmica e radiação**; **RWC é a prioridade nº 1 para comparar um Steinway real com Yamaha e Bösendorfer**; **MAPS** cobre os dois ambientes de captação e midi real; **MAESTRO/KRAISLER** validam musicalidade.
- A **única referência Felt disponível neste momento continua artisticamente preparada, sem capturas físicas controladas**, não generalizar coeficientes de B desse conjunto.
- A referência real **Yamaha CFX** ainda não foi encontrada em dados abertos com o mesmo controle; não apresentar um C5/DC3 como CFX.
- Nenhuma alteração de motores ou versão pública foi executada nesta pesquisa.


## 11. Fontes adicionais verificadas depois da hierarquia inicial

### Yamaha CFX verdadeiro (comparação auditiva, NÃO calibração física aberta)

Vienna Symphonic Library **Synchron Yamaha CFX / CFX Essentials**: https://www.vsl.co.at/instruments/synchron-pianos/yamaha-cfx-essentials .
É um **Yamaha CFX real** gravado com sistema robótico do instrumento, sensores ópticos do movimento das 88 teclas e pedais e sensores de martelo; microfones de palco e proximidade, processos de gravação documentados em marketing técnico. É produto **comercial com motor de sampler/processamento**, com demos e presets (inclusive reverb, EQ, body resonance, release samples). **Não demonstrado como WAV aberto, não baixar/extrair samples do produto**. Serve para avaliar o caráter final de um verdadeiro CFX ao ouvido, **não para extrair constantes de corda ou reempacotar áudio**.

### Piano Sound Quality Dataset — China Conservatory of Music / CCMusic

Site institucional: https://ccmusic-database.github.io/en/database/ccm.html .
- **1.320 gravações individuais** e 12 arquivos de extensão do teclado, pianos Steinway em sala e teatro, Kawai cauda/vertical, Young Chang vertical, Hsinghai vertical e Pearl River vertical. **Painel de avaliação subjetiva com 29 pessoas**.
- Existem arquivos WAV e conversões MP3/M4A; para qualquer estudo físico, **usar original WAV do acervo e verificar metadados de áudio**, nunca MP3. O registro de velocidade física e os microfones calibrados não foram demonstrados como no BiVib; utilizar como **validação externa de diferenças percebidas entre marcas, modelos e verticais**.
- Espelho HF: https://huggingface.co/datasets/ccmusic-database/pianos , cujo cartão marca **CC BY-NC-ND 4.0** para o espelho. Respeitar as restrições e a proveniência autoral; não distribuir arquivos nem derivados incorporáveis ao software sem revisar as condições.

### Felt e Upright

Até aqui não há dataset **comprovadamente controlado** com o **mesmo piano tocado com e sem feltro**, as mesmas posições de microfone e 10 velocidades controladas de marte­lo. O Fuchs & Möhr de Tom Guder continua sendo boa gravação acústica de **piano vertical com feltro**, mas uma amostra preparada não serve para identificar separadamente o efeito do martelo, feltro e instrumento.
