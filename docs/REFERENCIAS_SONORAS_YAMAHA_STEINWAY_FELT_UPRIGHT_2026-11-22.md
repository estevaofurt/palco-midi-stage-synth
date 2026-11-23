# Stage Synth — catálogo verificado de referências acústicas Yamaha, Steinway, Felt e Upright

**Revisão:** 22/11/2026 (fusos podem registrar consultas em 23/11 UTC).  
**Base de código:** main 442b94bac4368c74b1237ca3555a7ea5a39aa000, v1.12.4.  
**Natureza:** pesquisa de gravações e licenças; nenhum WAV/FLAC/AIFF/SFZ/SF2, nem programa de síntese, é incorporado ao repositório.

## Critérios de seleção
Preferir **instrumento acústico real identificado**, cada nota isolada, fonte autorizada, faixas de dinâmica, efeitos de sala mínimos e metadados das gravações. Separar:
- **A — identificação física:** gravações individuais com ataque, sustento natural, parâmetros e pedal conhecidos; calcular frequências/parciais/decaimentos.
- **B — avaliação perceptual:** referências musicais e demonstrações de bibliotecas ou de piano real, que podem incluir ambiente, equalização ou processamento físico na reprodução.
- **C — características de piano:** não confundir Yamaha C5 com Yamaha CFX, Steinway B com D, vertical Felt com um piano de cauda preparado.

Não inferir que "sem reverberação adicionada" equivale a uma gravação em ambiente anecoico.

## 1. Yamaha — Salamander Grand Piano V3 (Yamaha C5)

**Origem:** Yamaha C5 acústico, gravado por **Alexander Holm**. Microfones **2 × AKG C414**, arranjo AB, ~12 cm sobre as cordas; 48 kHz, 24 bits. **16 camadas de velocity**; gravação de notas em intervalos de terça menor a partir de A0, samples de soltura do martelo e de ressonância de cordas. **Licença CC BY 3.0**.

**Fonte primária e download:** https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html#Salamander  
**Página auxiliar:** https://sfzinstruments.github.io/pianos/salamander/  
**Formatos:** SFZ/FLAC 707 MiB (48k/24b), SFZ/WAV ~1,18 GiB (48k/24b), SFZ/WAV ~394 MiB (44,1k/16b), SF2 ~296 MiB.
**Uso recomendado:** prioridade alta para dinâmica do martelo, espectro por velocity, batimentos e transientes; manter arquivo original e escolher explicitamente velocity. Os Cs de MIDI 36/60/84 se alinham à amostragem A0+(n×3) prevista, **mas verificar no mapa SFZ** se o sample associado é realmente capturado na nota e velocity solicitadas.
**Limitações:** C5 não é o CFX que inspirou o caráter Japanese Stage; captura muito próxima das cordas não é som ouvido a 2 m na plateia; ressonâncias/pedal podem depender de disparo de samples do sampler.

## 2. Yamaha CFX — GSi Venice Grand CFX, material complementar

**Origem real:** Yamaha CFX gravado com robô em fevereiro/2023. GSi descreve ~245 samples estéreo, entre 6 e 12 velocidades por região, sem loops e sem EQ ou pós-processamento; dois microfones próximos dos abafadores e dois em distância de escuta. O motor de reprodução **adiciona ressonância modelada**.

**Página com 7 demonstrações:** https://www.genuinesoundware.com/?a=page&p=VeniceGrandCFX  
**Uso recomendado:** somente **referência perceptiva específica do CFX** neste estágio. O pacote é uma expansão para GSi Gemini, **não demonstrado como banco WAV livre para redistribuição ou usar como amostras do nosso motor**. Não analisar demos como "isolados sem FX" nem assumir que conhecemos os parâmetros do piano CFX.
**Se for indispensável identificar CFX com física:** localizar gravação bruta com licença clara e notas isoladas; as capturas de performance do usuário com FX seguem privadas.

## 3. Steinway — University of Iowa Musical Instrument Samples, Steinway Model B (preferência para análise)

**Origem:** piano de cauda **Steinway & Sons Model B**, gravações de 2001; microfones **Neumann KM84** a cerca de 8 polegadas das seções grave/aguda; estéreo, 44,1 kHz/16 bits, **não anecoico**. Notas de teclado gravadas separadamente em **pp, mf, ff** (as letras são dinâmicas musicais, não mensagens velocity 32/80/120 calibradas). Inúmeros links diretos AIFF para cada nota, incluindo C2/C4/C6.

**Fonte original:** https://theremin.music.uiowa.edu/MISpiano.html  
**Informações de métodos/permissão do acervo:** https://theremin.music.uiowa.edu/MIS.html  
**Espelho por nota, metadados e checksums (de terceiro):** https://huggingface.co/datasets/sondalex/university-iowa-piano-samples  
**Uma nota individual verificada:** https://theremin.music.uiowa.edu/sound%20files/MIS/Piano_Other/piano/Piano.mf.C4.aiff  
**Permissões:** a universidade declara uso em projetos sem restrições na página geral; **não há licença SPDX/Creative Commons identificada para as gravações** e o espelho explicita isso. Registrar autoria/proveniência; não assumir que é CC0.
**Uso recomendado:** prioridade alta para observação de B, amplitude por parcial, envelopes, ataques e comparação pp/mf/ff nas regiões do teclado; compensar reverberação do ambiente antes de interpretar caudas como da corda.

## 4. Steinway — Ivy Audio Piano in 162 (complemento por pedal e posições)

**Origem:** Steinway Model B, **5 níveis de dinâmica**, **duas gravações round-robin por nota**, samples pedal down/up e **duas posições de microfone**; biblioteca ~4,9 GB.
**Fonte do autor:** https://ivyaudio.com/freebies  
**Detalhes técnicos:** https://sfzinstruments.github.io/pianos/in_162/
**Acesso (consulta 22/11/2026):** site do autor oferece BitTorrent para SFZ/Kontakt; informa que downloads diretos retornarão. NÃO prometer download HTTP direto.
**Uso:** comparar close vs ambient, pedal on/off e variação entre tomadas, como referência perceptiva/medição condicional em close/pedal off. "Grátis para usar musicalmente" não é concessão explícita para redistribuir os arquivos de áudio do banco; **não incluir as amostras no repositório nem no aplicativo**.
**Atenção:** Steinway Model B não é representativo universal de todos Steinway, nem especificamente de um Model D de concerto.

## 5. Felt — Fuchs & Möhr Felt Piano, autor Tom Guder

**Origem:** piano vertical real **Fuchs & Möhr** com feltro, gravado pelo autor Tom Guder. O próprio autor oferece a coleção original com **três camadas**, WAV estéreo 16 bits e declara **public domain**. Disponível em SF2 e WAV zip; pode exigir login/site externo.
**Fonte do autor e link WAV original:** https://www.polyphone.io/en/forum/your-creations/850-acoustic-felt-piano-upright-fuchs-mohr  
**Ficha da biblioteca:** https://www.polyphone.io/en/soundfonts/pianos/683-fuchs-mohr-felt-piano  
**Uso recomendado:** prioridade alta para distinguir ataque suavizado pela colisão feltro/corda de simplesmente aplicar LPF/EQ; escutar ruídos de mecanismo e duração da vibração. Gravação pode estar intencionalmente desafinada; não usá-la para calibrar afinação universal/B sem identificar cada sample e corrigir a nota de referência.
**Licença:** declaração de domínio público do próprio autor na postagem; guardar link e texto de atribuição voluntária no manifesto local.

## 6. Upright — FreePats Upright Piano KW (Kawai vertical)

**Origem:** piano vertical **Kawai** numa sala doméstica, gravado por Gonzalo e Roberto em 2017; microfone Zoom H1 próximo à posição da cabeça do pianista. **Duas camadas de velocity**, estéreo, disponível em SFZ+WAV (~69 MiB) e SFZ+FLAC (~32 MiB), ou SF2. Licença **CC0 1.0**.
**Fonte e download:** https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html#UprightKW  
**Projeto do autor:** https://github.com/freepats/upright-piano-KW  
**Uso recomendado:** prioridade alta para características típicas de vertical doméstico, variação de timbre entre registros e dinâmica. **Nota importante: graves têm loops e gravações foram editadas**, portanto não usar seus trechos de cauda/loop para estimar T60 natural de corda. A acústica da sala está impressa no microfone.
**Limite:** não interpretar um Kawai vertical específico como o comportamento de todos os pianos Upright.

## 7. Escolha de dados inicial por categoria

| Stage | Fonte inicial | Etapa mais viável | Intensidades verificadas | Principal restrição |
|---|---|---|---|---|
| Japanese / Yamaha | Salamander C5 | ataques e amplitude espectral, dinâmica | 16 layers | **não** CFX; captação próxima; SFZ para mapeamento |
| American / Steinway | University of Iowa Model B | B, parcial por parcial, decaimentos pp/mf/ff | pp/mf/ff | sala não anecoica; sem velocity MIDI físico |
| Felt | Fuchs & Möhr / Tom Guder | ataque abafado e envelhecimento dos parciais | 3 layers | afinação irregular; gravação de upright felt |
| Upright | FreePats Kawai KW | ataque, timbre regional, 2 intensidades | 2 layers | caudas graves em loop; ambiente doméstico |
| Japanese / CFX secundário | GSi Venice Grand CFX | audição de caráter CFX real | 6–12 por região em produto | dados brutos não abertos; demos com modelagem |

## 8. Ensaio controlado antes de novos DSPs

1. Para cada fonte, baixar **localmente** um subconjunto, inspecionar o instrumento e a **nota realmente amostrada** no mapa SFZ/SF2, tipo de microfone, pedal, possíveis loops e metadados de captura. Não subir WAVs/FLACs/AIFFs/SFZs para o repositório sem revisão explícita de licença.
2. Começar por C2 (MIDI 36), C4 (60) e C6 (84); escolher os extremos baixo/médio/alto disponíveis no próprio banco. Yamaha possui 16 velocities, Iowa pp/mf/ff, Fuchs três, KW duas. **Não atribuir velocity MIDI exata a pp/mf/ff, nem inventar amostras ausentes**. Localizar próximas velocities apenas quando mapeamento explícito estiver disponível.
3. Armazenar no **manifesto local**: fonte/URL, hash SHA-256, instrumento exato, altura tocada vs nome sample, velocity/label, taxa/bits, canais, pedal, microfone, sala, eventuais loops/normalização/ruído, permissões, tempo de corte e versão de processamento.
4. Manter original intacto; decodificar AIFF/FLAC para análise, comparar inicialmente nas taxas nativas e só reamostrar em cópia para 48 kHz. Não normalizar individualmente amostras usadas para estudar a curva dinâmica.
5. Pré-checagem por janela temporal: detecção de ataque, ruído inicial, reverberação, autocorrelação de pitch e segmentos com loop. Usar espectro temporal multi-janelas para parciais e B; não tentar estimar T60 da corda com cauda de reverb ou loop. Na análise, separar first 100 ms, 100–500 ms e cauda e conferir efeitos de sala.
6. Rodar a mesma rotina para A modal, B v1.9.5, C mecânico e P1 isolado (se pertinente); reportar erro em cents e dB **com limites de incerteza**, e ouvir samples/reproduções com ajuste de loudness para comparar timbres.
7. Não calibrar corpo de um Yamaha C5 diretamente para um Yamaha CFX; gravação CFX de GSi serve apenas para benchmark auditivo até uma referência física seca CFX estar disponível.
8. Para ressônancia simpática/pedal, priorizar Steinway Ivy (pedal on/off) e eventualmente gravações controladas originais com estado conhecido; sample isolado não prova interação real entre notas.

## 9. Estado, direitos e entregáveis

- **Somente pesquisa de catálogo**. Não baixamos/importamos esses bancos para a app, não produzimos amostras derivadas e não alteramos o DSP.
- Links, licença e metadados são documentados para **consulta e análise futura**, não autorização para embutir bibliotecas na distribuição do Stage.
- Arquivos de gravação privados fornecidos pelo usuário permanecem fora de GitHub.
- Próxima etapa independente: adquirir **um conjunto pequeno de notas individuais localmente**, inspecionar áudio de fato, preparar manifesto local sem dados brutos no GitHub e medir em comparação com o Stage. Quando houver direitos, obter permissão explícita antes de redistribuir.
