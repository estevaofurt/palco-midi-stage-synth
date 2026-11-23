# Stage Synth — E2.6 | Banco local privado e comparação real com D v1.12.8
**Data:** 23/11/2026. **Escopo:** experiência independente da PR física #37; **NÃO é versão D v1.12.9/v1.13** e nenhum audio foi incorporado.

## Descoberta no código público
`sample-library.js` já disponibiliza `SampleLibrary.load/choose/play`, decodifica amostras somente no navegador, seleciona nota e camada de intensidade e impede transposição além de 12 semitons. `acoustic.js` só chega a `this.samples.play` na rota Clássica (as rotas A/B/C/D retornam anteriormente). `panel.js` já implementava um editor `samplepack`, porém **`patches.js` não declarava o controle na lista de grupos do Piano Acústico**. Portanto, importar WAV no painel não estava acessível, embora o backend existisse.

**Correção E2.6 em branch DRAFT:** acrescentar ao painel de Piano um grupo `Amostras locais · apenas Clássico` que reutiliza o mesmo `samplepack`. `panel.js` informa claramente que os WAV locais **não afetam A/B/C/D**, permanecem só na sessão e não são enviados ao servidor. Sem novo seletor/categoria e **sem alteração em `acoustic.js`, `sample-library.js`, `app.js`, Worklets, MIDI, FX, presets ou versão**. Banco opcional; padrão C continua igual e os presets existentes são preservados.

## Extração e comparação a partir das gravações do usuário
O usuário disponibilizou previamente `American(1).wav`, `Japanese(1).wav`, `Felt(1).wav`, `Upright(1).wav`, e seus WAV derivados. A análise local da gravação `American(1).wav` (44 kHz, PCM24 estéreo, cerca de 386,91 s) permitiu localizar **trechos candidatos de Dó1–Dó6**, identificados por picos espectrais de famílias harmônicas nas regiões correspondentes. Para escuta pessoal foram preparados 12 recortes privados C1–C6 (duas dinâmicas NOMINAIS por nota) e três A/B de C2/C3/C4 com o áudio verdadeiro previamente renderizado do Stage D v1.12.8. Esses arquivos **não estão neste repositório** e NÃO são distribuídos no site. O arquivo de teste é entregue somente ao próprio usuário no diálogo.

A comparação nivela RMS em trecho sustentado, mas os contextos de captação, origem do instrumento, velocity MIDI e expressão exatos são **desconhecidos**. **Não se pode afirmar que sejam gravações de piano acústico em condições controladas, nem avaliar blindamente melhorias de DSP por esse A/B.** A/B ilustra uma direção audível baseada em material gravado; não existe candidato D+samples integrado ou aprovado.

Os rótulos `MIDI36_v60.wav` etc. são compatíveis com `sampleDescriptor()`. Os números v60/v110 são camadas **nominais**, NÃO velocity identificada das performances. Com somente seis raízes, transpor muitos semitons pode soar artificial. O bloco `SampleLibrary` já recusa a nota se estiver mais de 12 semitons distante da raiz.

## Ferramenta reproduzível sem bytes pessoais
- `research/private-wav-note-bank.mjs`: analisa RIFF PCM16/24, mono/estéreo, 22.05–96k; admite chunks BEXT/JUNK antes dos dados, valida limites dos recortes e extrai a janela sem reprocessar os samples interiores. Aplica fades apenas nas pontas para evitar click.
- `scripts/build_private_piano_bank.mjs`: leitura **local** do arquivo e de manifesto explícito com SHA256, root MIDI, velocity nominal, duração e `verifiedPitch:true`. Só permite `use:private-listening-only` e `redistributionAuthorized:false`; evita sobrescrever amostras existentes, mantém arquivos localmente, emite `PRIVATE_MANIFEST.json`.
- `tests/private_wav_note_bank.test.mjs`: arquivos inteiramente **sintéticos gerados em memória**, parser, preservação PCM24 no interior, fades, hashes, rejeição de root falso, manifesto privado, mapeamento de nota/layer e proteção do seletor clássico/A/B/C/D. **Nenhum WAV real é versionado**.
- `.github/workflows/stage-e26-private-samples.yml`: `npm run check`, validação de CLI, `git diff` de motores públicos/roteamento e rejeição explícita de WAV/ZIP/SF2 no PR.

## Uso (branch experimental, sem merge)
1. Obter a branch `experiment/e26-local-piano-samples-20261123` e abrir Stage Synth em ambiente local/HTTPS adequado.
2. Selecionar **Piano Acústico → Motor Clássico** e o instrumento **American Grand**.
3. No painel **Amostras locais · apenas Clássico**, selecionar os WAVs nomeados `MIDI*_v*.wav` do pacote de teste privado; nada é enviado ao servidor nem persistido em presets.
4. Comparar por ouvido as mesmas notas C2/C3/C4 com o motor D original, volume semelhante e efeitos desligados.
5. Retirar amostras para regressar à síntese original. **Não mesclar ao D** nem liberar comercialmente o banco antes de validação perceptiva e licenciamento.

## Direitos e gates
O fato de o usuário ter carregado uma gravação permite análise privada solicitada, **não comprova que detém os direitos comerciais da biblioteca original** nem permite redistribuição do áudio num site público. Há bloqueio até prova explícita de licença e origem. As referências C2/C3/C4 também não foram gravadas com mesmas condições/velocities do Stage D. Não afirmar que uma nova síntese de piano foi concluída.

**Decisão:** disponibilizar apenas acesso local opcional no motor Clássico, em PR independente DRAFT; manter D v1.12.8, default C, A/B/C, FX/MIDI, bibliotecas atuais e pesquisa física PR #37 intactas. R-GATEs comerciais continuam 0/7; 32–64 vozes no dispositivo real pendentes.
