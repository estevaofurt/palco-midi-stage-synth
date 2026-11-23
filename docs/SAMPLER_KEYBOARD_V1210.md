# Stage Synth v1.12.10 — correção do teclado e aviso de banco no motor E

O motor E foi integrado na v1.12.9, mas como os WAVs do usuário permanecem privados fora do site, iniciava sem qualquer amostra. O código do Stage descartava a voz silenciosa imediatamente; o teclado pintava apenas vozes ativas e por isso parecia que não reconhecia cliques.

Na v1.12.10 o teclado mostra a tecla pressionada a partir da entrada do usuário, independentemente de existir uma voz audível. Uma faixa junto ao teclado informa qual banco WAV está carregado, a quantidade de notas e um botão **Carregar notas WAV** que abre o seletor de arquivos do instrumento atual. O sistema informa quando a nota solicitada está fora da cobertura das amostras importadas, em vez de simular falsamente um piano.

**Para ouvir:** ativar áudio → cena Piano acústico → E · Piano sampleado → escolher American/Japanese/Felt/Upright → clicar Carregar notas WAV → importar os arquivos MIDI60_v60.wav, MIDI60_v110.wav etc. O banco fica apenas na sessão do navegador e será necessário importar novamente após recarregar. Os WAVs privados anteriores não são distribuídos no GitHub Pages porque o direito comercial de redistribuição não foi demonstrado.

Regressão: motor C segue padrão; A/B/C/D e Histórico/Clássico, V4 físico, MIDI e efeitos permanecem. Verificar testes e escuta real com o banco privado.
