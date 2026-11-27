# G3 — convergência regional acoplada de 250 ms

Continuação de 75b2fa9bb5635ad6decbbb5d6f58a5c32e03a2cd. ZIP anterior SHA-256 327d2e11aefc40658fbb3908a7f168ecdba03f9015c7942a0ec8989eb35bfab7 e 151 entradas verificados. Modelo físico de sete notas, 18 cordas, 369 portas, 127825 estados acústicos, coeficientes refinados, 384 kHz, ranks mistos 64/64/128/64/64/64/64 (1360 coordenadas) vs 128 uniformes (2384). Nenhuma recalibração ou redução de modos acústicos. Executor incremental NPY substitui armazenamento em listas; regressão 18 ms, 6912 passos: cinco arrays e 18 indicadores exatamente iguais. Mantém algoritmo de contato e integrações, não reinicializa estados entre golpes.

Cronograma experimental: MIDI48/60/64/48/60/64 aos 0/15/30/55/120/160 ms, velocidades 0,3/1/3/1/0,7/0,5 m/s. Pedal abre 5, fecha 75, abre 105, fecha 200 ms. Teclas liberadas MIDI48 aos 40 e 85, MIDI60 aos 65 e 145, MIDI64 aos 70 e 185 ms. Seis lançamentos/capturas por caso; 96000 passos cada, 192000 novos passos acoplados. Capturas misto 1686/6663/12232/22544/47028/62413, uniforme 1686/6664/12232/22545/47028/62413. Injeção 0,05075078112 J. Todos abafadores fechados após 200 ms. Balanço máximo 6,826673e-13, continuidade 2,073585e-15, reconstrução energia 2,666135e-15 e dissipação 7,178056e-15. Trabalho exterior acumulado não negativo. Convolução direta máxima 1,787156e-17, pré-chegada 2,583187e-15. Energia mecânica final 0,197141532/0,197138542 mJ; cavidade 6,463195e-8/6,463501e-8 J. Tempos dos laços 600,764/606,914 s (processos concorrentes, não benchmark).

| Janela ms | Pressão fina causal mic1/mic2 % | Gate |
|---:|---|---|
|50|0,119832/0,107356|passa|
|100|0,117812/0,110824|passa|
|150|0,119796/0,108464|passa|
|200|0,125903/0,113242|passa|
|250|0,127594/0,113970|passa|
Pressão fina completa 0,127616/0,113887%; todas comparações globais/bandas passam 1 dB/3 dB; gate 1% fino causal e completo passa. Referência uniforme finita, não convergência espacial absoluta. Pressão pós-janela assume fluxo zero, não cauda física. Quatro notas não golpeadas: RMS das portas 200–250 ms (m/s) MIDI33/45/55/72 = 0,0234134/0,0414502/0,0203758/0,00911566. Participação interna não é energia isolada ou audibilidade. Cronograma e velocidades são hipóteses experimentais, não calibração do mecanismo. Não é validação de 88 teclas, tempo real ou de som final.

Retomada opt-in: teste de 18 ms com três processos independentes, snapshots nos passos 1200 (três martelos ativos) e 3200 (buffer exterior já envolvido, capturas concluídas). Cinco arrays e 18 indicadores idênticos à execução contínua. Variante versionada conserva ambos os estados completos, SHA-256 6bc52176a94730133d224315a1875ed7827156b1642b4a1b2e433b4dede6b3f0 e c2caf01ab537c5511379d1f4abb990f426a9b314c5c4c735be2c8734a37209f3. 265675080 bytes cada. Prefixo e estado verificados antes de restaurar; assinatura liga fontes e insumos. Retomada prolongada ainda não testada. Ensaios de 250 ms não interrompidos. Próximo: validar retomada longa e 500 ms, investigar redução acústica preservando passividade/impedância e precisão. Sem render, EQ, normalização ou promoção.

Pacote mínimo SHA-256 1d279241b7effc9704539c98987efd775eb937c369efcc2d3438354525570192, 18065854 bytes, 182 entradas verificadas. Sinais completos locais, 10 NPY, 3483649280 bytes, manifestados em SINAIS_250ms.sha256; não publicados como binários. Relatórios, fontes novos e hashes publicados na branch de pesquisa.
