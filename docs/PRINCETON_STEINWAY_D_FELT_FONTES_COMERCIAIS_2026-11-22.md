# Preparação comercial — Steinway Model D Princeton e Felt Fuchs & Möhr

**Data de pesquisa:** 22/11/2026 (execuções automáticas em UTC 23/11).
**Base de código:** main 4bc10c298043065a9649e4d4a9792d0fcfe5d684.
**Limite expresso:** NÃO programar o motor, integrar P1/P2, ajustar DSP, MIDI, interface, FX ou presets. Apenas obter e verificar referências permitidas para uso comercial.

## Steinway Model D original — Princeton / bitKlavier Grand

**Publicação dos autores:** https://bitklavier.com/the-bitklavier-grand/

- Instrumento: Steinway Model D acústico real, gravado em janeiro de 2021 no Taplin Auditorium da Universidade de Princeton.
- Autor/produtor: Dan Trueman e equipe. **Licença CC BY 4.0**, declarada tanto pelo criador quanto no registro do Internet Archive. Atribuição e aviso de alterações são exigências comerciais relevantes.
- Nove pares estéreo de microfones com **16 layers por nota realmente amostrada a intervalos de terça menor**, começando A0. Não confundir com 88 notas originais separadamente gravadas.
- Sons de tecla/martelo soltando, pedal e ressonância de liberação.
- Processamento **por parte dos autores**: redução de ruído RX8, fades de ataque/release, ajustes/seleção de níveis por RMS, ajustes de ganho geralmente menores que 2 dB. Portanto, não inferir força física do martelo dos amplitudes relativas.

### Três coleções de microfone com identidade e hashes do ZIP comprovadas

O workflow https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45102640600 consultou a API de metadados do Internet Archive e confirmou nome, licença CC BY 4.0, tamanho e hash MD5 registrado para cada ZIP. **Não implica que o ZIP foi integralmente baixado ou que MD5 do arquivo foi recalculado.**

| Coleção 44.1kHz/16-bit | Bytes do ZIP oficial | MD5 informado pelo Archive |
|---|---:|---|
| Piano Bar (Earthworks, captação próxima) | 976630577 | d1ff666c99bb1a7298bde9f2c81f8293 |
| Binaural (Neumann KU100, posição do pianista) | 1012656771 | a636786c04a480127ef6e879cc311b34 |
| Harp Omni (DPA 4060, cordas/harpa) | 988859574 | cff1154ba1a8b805b878b137cad22bf2 |

Tamanho combinado **2.978.146.922 bytes**. 
IDs: bitKlavierGrand_PianoBar_44k16b, bitKlavierGrand_Binaural_44k16b, bitKlavierGrand_HarpOmni_44k16b.
Índice persistente: research/commercial_audio/steinway_d_verified_archive_index.json .

**Índice interno do ZIP acessível:** foram localizados os **11/11 nomes escolhidos** de Piano Bar, **3/3** Binaural e **3/3** Harp Omni; nomes incluem C2v1/v8/v16, C4v1/v8/v16, C6v1/v8/v16, rel40 e pedalU1. Execução https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45102770585 . 
Também foi testada a URL do membro virtual C4v8.wav do ZIP original: retornou **cabeçalho RIFF/WAVE válido em 256 bytes**, mas isso isoladamente não verifica o arquivo todo. Não anunciar esse teste parcial como WAV totalmente íntegro.

**Método de extração seletiva CRIADO E EXECUTADO com sucesso:** manifesto research/commercial_audio/steinway_d_selective_pilot.json, script verify_bitklavier_wavs.py e testes offline. Baixou diretamente **sete WAVs originais de dentro dos ZIPs oficiais**, com limite de 30 MB por WAV e 100 MB no conjunto; verificou WAV PCM e SHA-256 integral e eliminou os bytes de áudio após cada teste. **7/7 aprovados**, total 39.356.676 bytes, sem publicar WAVs. Execução https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45103239343 (**22/22 testes unitários**). Os sete SHA-256 permanentes estão em research/commercial_audio/steinway_d_verified_wav_sha256.json; áudio não está no repositório. Dados disponíveis: Piano Bar C2v8, C4v1/v8/v16, C6v8, Binaural C4v8 e Harp Omni C4v8.

**Usos da referência Steinway D:** comparação de timbre American Grand, variação por posição microfonada, eventos de pedal e ressonância; **não** fornece medição direta de impedância da ponte, velocidade do martelo nem contato do feltro.

**Resumo acumulado:** com a rodada anterior de 28 WAV/FLAC originais de Yamaha C5, Steinway B, Knight e Kawai e os sete WAVs Steinway D atuais, são agora **35 arquivos originais de cinco pianos reais**, **103.753.348 bytes** verificados. Isso não equivale a cinco pianos com física medida nem libera qualquer um dos sete gates.

## Felt original — Tom Guder / Fuchs & Möhr upright

**Publicação do próprio criador:** https://www.polyphone.io/en/forum/your-creations/850-acoustic-felt-piano-upright-fuchs-mohr

O autor declarou que o piano é um Fuchs & Möhr vertical real e publicou o arquivo **FuchsUndMoehrSamplesWAV16bit.zip** com três camadas estéreo WAV 16 bits, declaradas **Public Domain**. Seu link autoral de origem é:

https://drive.google.com/file/d/1XbIZgTdKoR2KxIyKM-CkEweS3HI4ieHu/view?usp=drive_link

**Estado:** a proveniência/autoria e declaração explícita de domínio público estão confirmadas no fórum; **o ZIP WAV original do Drive NÃO foi baixado nem teve SHA256 confirmado nesta etapa**. As nove amostras Felt do experimento E0 vieram de um reempacotamento CueHarbor com edições e cortes; não as apresentar como bytes originais sem cotejar hashes. A afinação peculiar do instrumento e o processamento são limitações acústicas.

**Limitação prioritária:** falta um conjunto controlado do mesmo piano com e sem inserção de feltro para quantificar o efeito da preparação sem misturar outros fatores.

## Auditoria preliminar dos componentes do produto comercial

- A árvore de arquivos de main não inclui bancos de áudio comercial de terceiros, arquivos WAV/FLAC, MP3 ou imagens: foi localizado somente o pequeno arquivo binário de teste **tests/fixture_minimal.sf2** (4492 bytes). **A procedência desse fixture também deve ser documentada** antes do lançamento.
- A página creditos.html afirma que o Stage utiliza síntese original e que bancos de usuários são carregados localmente, não incorporados. Os perfis Japanese/American não são instrumentos Yamaha/Steinway licenciados nem significam endosso.
- O projeto não tem arquivo de licença LICENSE no diretório raiz; **package.json private=true NÃO é licença de redistribuição**. Antes da venda, decidir a licença do Stage e revisar direitos de código adaptado e recursos de terceiros.
- A auditoria dos direitos do código e de marcas/terceiros não está homologada; não concluir automaticamente que todos os arquivos são de propriedade exclusiva do titular.

## Pendências e liberação

- **CONCLUÍDO PARCIALMENTE:** sete WAVs do Model D foram integralmente verificados em três mics e diferentes layers, com SHA256 persistente. Para ampliar a escala, decidir se é útil obter a coleção 48k/24b em calibração acústica futura; lembrar que a pós-produção dos autores permanece. Ainda NÃO há medidas de martelo e ponte.
- Baixar/validar o ZIP Felt original do criador e registrar autor, licença e integridade; não publicar bytes no GitHub ou aplicativo.
- Obter dados de martelo–corda, duas polarizações e mobilidade da ponte de laboratório próprio ou autorizado comercialmente; **microfone sozinho não identifica física interna**.
- Preparar lista de atribuições, decisão sobre licença do aplicativo, termo de distribuição e prova de direitos de código/fixtures.
- **Os sete R-GATEs globais continuam pendentes; não liberar P1/P2 nem mexer no DSP até validação integral e autorização expressa do usuário.**

Fontes oficiais adicionais:
- Archive Piano Bar https://archive.org/details/bitKlavierGrand_PianoBar_44k16b
- Archive Binaural https://archive.org/details/bitKlavierGrand_Binaural_44k16b
- Archive Harp Omni https://archive.org/details/bitKlavierGrand_HarpOmni_44k16b
- Creative Commons BY 4.0 https://creativecommons.org/licenses/by/4.0/
