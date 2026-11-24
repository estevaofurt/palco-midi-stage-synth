# Stage Concert Grand — F4.3 sensibilidade do martelo e solver de contato otimizado

Data 24/11/2026. Base 86ed225507125ab7ea66b3169611db6d8830bcbc. Pesquisa autoral offline; nenhum arquivo de main, V10, DSP público, áudio ou UI alterado. Sem WAV. F4 aceita internamente no escopo de contato isolado, não homologação acústica ou ação completa.

## Método
Dependências lidas no GitHub: felt-memory.mjs 13fb31fbf82f9a9895c1d6091edb67604934e594; hammer-contact.mjs f833868efe3ea1a7a85ebef25601d5b9721d326f; trichord.mjs aa29d9616119ab24cec6779ee3fd60bd490902e4. Não mudar a lei constitutiva ou parâmetros padrão da F4.2. Em efficient-felt.mjs, para estado interno congelado e força não negativa, delta1_i=free_i-g_i*F_i-hm*sum(F), hm=h²/(2m). A iteração F_next_i=G_i(delta0_i,delta1_i,z_i), onde G é o gradiente discreto do potencial unilateral, é Lipschitz na caixa positiva: majorar derivada pela maior derivada da força pontual entre as compressões relevantes, vezes g_i+3hm. Usar contração quando limite <=0,5; residual infinito <=1e-11 N; máximo 64 iterações, caso contrário retornar à bisseção aninhada original. A iteração preserva não negatividade; como G é monótona em delta1, forças estão limitadas pelo valor sem reação. Para contatos abertos usar zero. Relaxação interna por bisseção permanece inalterada. Este ganho é apenas na equação de força, não tempo total, nem benchmark de 64 vozes. Sem alteração da referência F4.2.

## Paridade e custo
48 kHz, 8 ms, 1 m/s, baseline F4.2. 384 passos; 249 abertos, 135 por contração, zero fallback. Contagem de avaliações da lei de força (incluindo verificações iniciais internas ao solver): referência instrumentada 510642; novo 3915, ~130,43 vezes menos, redução 99,233%. Não inclui custos de relaxação, integração modal, diagnósticos ou chamadas externas. Trajetória referência instrumentada igual à original; diferença máxima nova/original 4,998e-11 N, pico 11,54166617879 N, energia nas cordas 2,197659813 mJ. Forte assimétrico 2,5 m/s com folgas 0/50/100 micrometros: diferença máxima 1,740e-10 N. Caso sintético de acoplamento forte (limite 2,236) acionou bisseção e deu 4,778687525 N por contato. Conferência adicional de residual após leitura do arquivo salvo: 4.020508e-10 N. Não extrapolar domínio de teste para impactos arbitrários.

## Sensibilidade
Uma variável por vez, ±20%, demais mantidas: 48 kHz, 1 m/s, 16 kHz, 8 ms. A rigidez escala ke e km juntas, sem alterar expoente p. Fração de energia mecânica vertical acima de 3 kHz (não pressão acústica), energia total das cordas, força pico.
| parâmetro | valor baixo/alto | pico N baixo/alto | energia mJ baixo/alto | fração alta % baixo/alto |
|---|---|---|---|---|
| massa | 8/12 g | 10,200785/12,589467 | 1,840505/2,537463 | 0,007629591/0,006492522 |
| rigidez | 0,8/1,2 vezes | 11,322206/11,721441 | 2,115131/2,262442 | 0,003177596/0,012004099 |
| posição | 0,104/0,156 L | 12,313797/10,859748 | 1,901785/2,444171 | 0,004453915/0,001688383 |
| largura | 9,6/14,4 mm | 11,526920/11,558792 | 2,193211/2,202838 | 0,006949010/0,006834182 |
| viscosidade | 0,8/1,2 Ns/m | 11,538805/11,545881 | 2,201783/2,195419 | 0,006556075/0,007115338 |
Baseline fração alta 0,006899496%. A posição tem efeito não monotônico em torno de 0,13L; não generalizar. Massa variada com velocidade fixa muda também a energia inicial. Não são intervalos de incerteza medidos. Não escolher parâmetros por maximizar brilho: manter baseline e priorizar posição e rigidez na calibração posterior com saída acústica física, avaliar massa e dissipação conjuntamente. Não é estudo de interações entre parâmetros nem cobertura de registros.

## Convergência
Frequência de cálculo 48/96/192 kHz, banda fixa 16 kHz: pico 11,541666/11,544506/11,545192 N; energia 2,197660/2,197985/2,198066 mJ; fração acima de 3 kHz 0,006899496/0,007147812/0,007211171%. Espectro do impulso de força total (soma discreta a centros de passo, normalizado por impulso DC), não pressão, nem espectro contínuo exato:
| Hz | 48k dB | 96k dB | 192k dB |
|---|---:|---:|---:|
|500|-16,103544|-16,104543|-16,104794|
|1000|-29,847953|-29,848993|-29,849268|
|3000|-52,410218|-52,360791|-52,348599|
|6000|-77,078906|-76,818540|-76,752413|
|10000|-94,525601|-94,095864|-93,987080|
Diferença a 10 kHz de ~0,539 dB a 48 vs 192 kHz; 96 vs 192 ~0,109 dB. O erro de pico não representa toda a banda; 48 kHz candidato, repetir com ponte e radiação. Corte 8/16/32 kHz à taxa fixa 192 kHz: pico 11,577052/11,545192/11,538784 N, energia 2,207202/2,198066/2,196175 mJ; fração alta 0,007489698/0,007211171/0,007157426%. Corte 16 vs 32 kHz difere ~0,056% no pico e ~0,086% na energia. Referência finita, não solução contínua. Manter 16 kHz provisoriamente, reavaliar quando a ponte e radiação estiverem presentes.

## Testes, decisão e F5
12/12 verificações em V8 antes da gravação: paridade, contagem, fallback, passividade, soltura, energias modais, espectro finito, refinamento, truncamento e sensibilidade. Em todos os cenários da bateria, aumento energético observado zero e resíduo de balanço <1e-10 J; força final zero, rebote negativo. Reprodução: `node research/stage-concert-grand/efficient-felt.test.mjs`. Commits 0cc1c0e85582c2a72cb492d124b3e18174f7b0be e 714f416222e6c8c4f24d999d661f5448f6b56815. Sem nova execução de CI Node ou hardware. F4.1–F4.3: 44 verificações aprovadas, aceite interno limitado ao contato de martelo e cordas com apoios fixos. Parâmetros não medidos nem calibrados. Repetição e ação completa F11; desempenho F12.
Próxima F5: introduzir apoio móvel por transformação de coordenadas ou condição de contorno energética, com força e velocidade conjugadas e reação recíproca. Não ligar força do apoio fixo diretamente a um filtro de saída; validar mobilidade/impedância, balanço e transferência entre cordas, comparar referência de apoio rígido, preservar o martelo. F6 tampo e F7 radiação depois. Sem WAV de piano até F8; F9 validação auditiva, F12 e F13 continuam bloqueadas. Meta 32–64 vozes não homologada.