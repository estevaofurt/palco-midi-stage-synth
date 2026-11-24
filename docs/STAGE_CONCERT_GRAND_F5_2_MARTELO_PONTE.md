# Stage Concert Grand — F5.2 martelo viscoelástico, tricórdio e ponte móvel

Data 24/11/2026. Base 62d345f4dd3fc39b15bc4853ba782822eb2cbab6. Pesquisa autoral offline, uma polarização vertical. F5 continua em andamento. Nenhuma alteração de main, V10, DSP público, interface ou áudio; sem WAV.

## Formulação
Dependências lidas no GitHub: moving-bridge.mjs 998aa8a6a5a0265f555d04827783f4d6a2e40241; felt-memory.mjs 13fb31fbf82f9a9895c1d6091edb67604934e594; hammer-contact.mjs f833868efe3ea1a7a85ebef25601d5b9721d326f; stiff-string.mjs c5b2f2f47cb237e2967530e062a6d039443a2787. Parâmetros padrão F4.2/F5.1 preservados. O passo mecânico da ponte e cordas usa ponto médio implícito, não evolução modal exata. Não reutilizar diretamente a flexibilidade diagonal F4.3.
Se A=M+hC/2+h²K/4, P projeta forças dos três contatos em coordenadas mecânicas, y1=y_free+G*F, G=h²/2*P^T*A^-1*P. Matriz simétrica positiva por construção. Aproveitar estrutura ponta de flecha: G_ij=h²/2*(delta_ij*sum_n w_in²/A_in+t_i*t_j/Schur), t_i=0,13-sum_n B_in*w_in/A_in. Para martelo livre m, compressão d1=d_free-(G+h²/(2m)*11^T)*F. Usar gradiente discreto do feltro F4.2 com memória congelada entre duas meias relaxações. Solução por contração com majorante <=0,5, resíduo <1e-10 N; fallback por bisseções coordenadas (até 256 sweeps, resíduo global <1e-9 N ou erro explícito). Solver atual exige matriz de flexibilidade simétrica com elementos não negativos e diagonal positiva; positividade definida vem da construção física, não é validada para matrizes arbitrárias. Não extrapolar para portas com sinais cruzados. Teste sintético SPD forte convergiu em 8 sweeps, residual 1,45848e-10 N. A resposta afim prevista foi conferida contra step real com erro máximo 3,388e-21 m. G a 48 kHz, 47 modos/corda: diagonais ~1,888e-6 m/N, termos cruzados ~1,28e-14 m/N. A interação instantânea por passo não é uma FRF; a transferência se acumula ao longo do tempo.
Trabalho do contato sum(F_i*delta y_i) conferido com trabalho externo do subsistema ponte/cordas. Reação oposta total atua no martelo. Energia total = cinética martelo + potenciais feltro/memória + energia integral de cordas incluindo levantamento do contorno + energia massa/mola própria da ponte. Perdas feltro e Rayleigh distribuídas, amortecimento da ponte separado. Nenhuma saída de pressão, tampo ou radiação modelada.

## Resultados
Impactos 8 ms, taxa 96 kHz, corte 16 kHz, massa martelo 10 g, folga 0,2 mm; posição 0,13L e largura 12 mm. Valores hipotéticos, não medições Yamaha.
| velocidade m/s | pico N | compressão mm | contato ms | energia cordas mJ | energia ponte mJ | perda ponte mJ | perda feltro mJ | deslocamento máx ponte µm |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|0,5|5,302700|0,265202|3,166667|0,438042|0,002286|0,006778|0,056788|5,181860|
|1|11,546167|0,365483|2,791667|2,126580|0,024137|0,047481|0,167327|12,663697|
|2,5|32,469421|0,557856|2,468750|15,857940|0,066058|0,455068|0,691509|37,230643|
A 1 m/s, trabalho dos contatos 2,210269 mJ, perdas cordas 0,012071 mJ; energia inicial martelo 5 mJ. Rebote -0,724210 m/s, força final zero. Máximo resíduo energético global nos cenários 1,066e-14 J, aumento máximo de energia 8,674e-19 J (arredondamento); resíduo lei de força <1e-8 N. A comparação inicial do relatório de energia da ponte produziu NaN por erro aritmético em diagnóstico (multiplicação por objeto). Corrigido e adicionada verificação de energia armazenada finita, não negativa e balanço independente do subsistema. Bateria reexecutada a partir dos arquivos recuperados do GitHub; sem mudança na dinâmica. Impulso e trabalho conjugado aprovados.
Limite rígido K=1e14 N/m, 192 kHz: deslocamento máximo 8,238e-14 m; pico 11,54563935 N vs F4.2 apoio fixo exato 11,54519202 N (~0,00387%); energia cordas 2,19807390 vs 2,19806642 mJ (~0,00034%). O limite é ensaio numérico e não parâmetro de construção.
Convergência a 1 m/s, 48/96/192/384 kHz: pico 11,548488/11,546167/11,545639/11,545529 N. Comparação espectro de força, normalizado pelo impulso DC, amostragem no centro dos passos:
| Hz | 48 kHz dB | 96 kHz dB | 192 kHz dB | 384 kHz dB |
|---:|---:|---:|---:|---:|
|500|-16,109179|-16,105955|-16,105146|-16,104943|
|1000|-29,839360|-29,846779|-29,848718|-29,849208|
|3000|-52,193785|-52,308839|-52,335719|-52,342339|
|6000|-77,627401|-76,901832|-76,768634|-76,739481|
|10000|-94,185291|-94,053613|-94,153705|-93,985621|
Erro a 6 kHz ~0,888 dB para 48 vs 384 kHz; 10 kHz não monotônico com refinamento. Não confundir convergência de pico com precisão da trajetória dos modos ou pressão acústica. Corte 8/16/32 kHz à taxa 192 kHz: pico 11,577518/11,545639/11,539224 N, energia cordas 2,135233/2,126684/2,124911 mJ. Corte 16 kHz ainda hipótese provisória; benchmark de tempo real não executado. A fase da integração midpoint nos modos altos continua lacuna, reavaliar antes de produto.

## Testes e decisão
13/13 verificações executadas em JavaScript V8, incluindo previsão afim, reciprocidade, fallback, passividade, balanço independente do subsistema, impulso, rebote, dinâmica, limite rígido, refinamento, espectro e assimetria. Reprodução: `node research/stage-concert-grand/mobile-hammer.test.mjs`. Commits 48882d19fa9a9fdb1dcce488b2ae03c47ad7c8ab, 56d76194a396684eb4ea222c022f9565483c3a6d e 7fda895a3fe9528363e2446d781e7806ff0c98d0 (diagnóstico corrigido e nova execução V8 a partir dos fontes recuperados). Sem novo CI Node/hardware.
F5.2 entregue no escopo vertical de pesquisa. F5.3: introduzir duas polarizações com transformação geométrica conjugada e matriz de ponte passiva, demonstrar transferência bidirecional e perdas, estudar decaimento e mobilidade; resolver ou delimitar precisão de fase e custo. Não forçar excitação horizontal por ganho artificial. Se necessário, manter solver de referência offline e levar otimização ao F12. F6 tampo, F7 radiação, F8 demonstração completa, F9 validação auditiva; F12/F13 e meta 32–64 vozes não homologados. Sem WAV até F8.
