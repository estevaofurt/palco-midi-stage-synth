# Stage Concert Grand — F5.3 ponte em duas polarizações

Data 24/11/2026. Base 354a89a0e64511c2cde3111e2bc7cd6d8159de99. Pesquisa autoral offline. Nenhuma alteração em main, V10, DSP, UI ou áudio. Sem WAV. F5 aceita internamente no escopo de ponte concentrada, não ponte/tampo real homologados.

## Formulação
Fontes lidas: moving-bridge.mjs 998aa8a6a5a0265f555d04827783f4d6a2e40241; mobile-hammer.mjs 4d4dd498846f83db8d9458d1a235aefd7b316806; felt-memory.mjs 13fb31fbf82f9a9895c1d6091edb67604934e594. Reaproveitados dois sistemas de levantamento de contorno F5.1, um por polarização. Três cordas, 47 modos por corda por polarização, total 282; dois graus da ponte, martelo compartilhado com três estados de memória. Massa efetiva de translação da ponte 25 g em cada direção (mesma massa isotrópica, não somar como duas massas físicas). Rigidez principal [1e6,2e6] N/m, amortecimento [20,5] Ns/m, ângulo 0,25 rad (~14,3 graus), tensores K=R diag(k) R^T e C=R diag(c) R^T. Hipóteses ilustrativas, não medidas Yamaha. K_vv=1061208,7191, K_hh=1938791,2809, K_vh=-239712,7693 N/m; C_vv=19,081869, C_hh=5,918131, C_vh=3,595692 Ns/m. Perdas distribuídas verticais [0,4;0,0002], horizontais [0,2;0,00012] conforme F3.2; não atribuir anisotropia ao aço circular sozinho.
Complementos de Schur escalares da F5.1 formam diagonal do sistema 2x2; termo cruzado h*C_vh/2+h²*K_vh/4. Resolver velocidades médias simultaneamente, aplicar forças cruzadas -K_vh*b_other_mid-C_vh*v_other_mid em cada eixo, mantendo balanço. Energia inclui K_vh*b_v*b_h, dissipação inclui 2*C_vh*v_v*v_h. Trabalho externo exclui trabalho cruzado interno. Matriz SPD por construção e determinante do Schur conferido. Custo estrutural O(N) por passo, mas implementação repete cálculos de redução e aloca arrays: laboratório, não AudioWorklet. Hammer F5.2 preserva contato somente vertical, resposta afim de contato usa elemento vv da inversa do Schur 2x2; compliance ainda não negativa no domínio testado. Nenhum ganho arbitrário de excitação horizontal. Não alterar lei do feltro.
Mobilidade contínua 2x2 obtida por eliminação harmônica dos modos de cada eixo e inversão da matriz dinâmica complexa. Reciprocidade por simetria; parte hermitiana real PSD conferida. Não é FRF medida ou resposta discreta.

## Resultados
Impactos de 8 ms, 96 kHz, corte 16 kHz:
| velocidade m/s | força pico N | b_v máximo µm | b_h máximo µm | E corda v mJ | E corda h mJ |
|---:|---:|---:|---:|---:|---:|
|0,5|5,302700|4,943303|0,959912|0,438269|0,000247434|
|1|11,546167|12,187723|2,271236|2,127882|0,001980008|
|2,5|32,469421|35,886689|6,873951|15,865129|0,019162737|
Ângulo zero: energia horizontal e deslocamento horizontal exatamente zero; pico vertical igual F5.2 11,54616657328226 N. Com acoplamento, diferenças de pico são muito pequenas no cenário padrão; não alegar mudança sonora percebida. Resposta afim conferida com erro 1,694e-21 m. Máximo resíduo de balanço dos impactos 1,058e-14 J, aumento máximo 8,674e-19 J (arredondamento), força final zero, rebote negativo. Pico a 48/96/192/384 kHz: 11,548488/11,546167/11,545639/11,545529 N.
Decaimento livre: corte 4 kHz (42 modos por polarização), taxa 96 kHz, 200 ms, deslocamento inicial primeiro modo primeira corda 1e-4 m. Energia inicial 24,935875 µJ. Excitação vertical: energia total final 82,921554%, horizontal 0,486675% da inicial (~0,121405 µJ). Excitação horizontal: total 91,824038%, vertical 0,486805% (~0,121466 µJ máximo). Ângulo zero: nenhuma energia cruzada. Resíduo máximo 1,091e-17 J, sem crescimento observado. Ensaio sem perdas aprovou conservação relativa <1e-9. Não prova envelope acústico bifásico, apenas mecanismo e hipótese de perdas diferentes.
Mobilidade calculada em nove frequências selecionadas; após leitura de código salvo, varredura adicional 20–16000 Hz a cada 5 Hz (3197 pontos, 192 kHz na construção da base): menor parte real diagonal 3.77225154e-8 m/(s N), menor determinante real 6.18899830e-15, maior módulo cruzado 4.71495287e-2 m/(s N). Não substitui medição nem garante cobertura de picos estreitos entre pontos.

## Precisão de fase e custo
Midpoint permanece referência, não adequado cegamente a 48 kHz para a banda superior. Orçamento teórico de oscilador isolado sem perdas, em cents (não erro medido dos modos acoplados):
| Hz | 48k | 192k | 384k |
|---:|---:|---:|---:|
|1000|-2.467442|-0.154483|-0.038624|
|5000|-59.107598|-3.851372|-0.964933|
|10000|-210.604506|-15.273759|-3.851372|
|16000|-447.966393|-38.424669|-9.815418|
F6/F7/F8 utilizar referência offline refinável; comparar saídas a múltiplas taxas e ampliar se necessário antes de escuta. Não afirmar que 192 ou 384 kHz garante precisão universal. F12 deve resolver fase/custo (por exemplo, diagonalização de sistema linear com integração modal exata e portas conjugadas, verificando dissipação e contato), medir hardware e polifonia. Não trocar integrador sem regressão.

## Testes e decisão
13/13 verificações V8 antes dos commits: PSD, resposta afim, paridade vertical, transferência cruzada, decaimento, energia e trabalho, soltura, dinâmica, mobilidade, refinamento, conservação e limite alinhado. Primeiro script falhou por sintaxe antes de execução, corrigido. Código lido após gravação e varredura adicional executada. Reprodução: `node research/stage-concert-grand/polarized-bridge.test.mjs`. Commits 622be15c2f9f4043faa9fd3e0177809abc1fb5a1 e e90a883bdc6777c09d84e193c7c360e71f75c34f. Sem CI Node novo ou hardware.
F5.1–F5.3: 40 verificações aprovadas, aceite interno limitado ao sistema concentrado e apoios móveis. F6 próxima: tampo ortotrópico com geometria explícita, energia de flexão, nervuras, massa e condições de contorno, convergência espacial, mobilidade recíproca, acoplamento energético à ponte; separar perdas estruturais de radiação F7. Parâmetros F1/F3/F4/F5 ainda hipóteses. Sem WAV até F8; F9 validação auditiva; meta 32–64 notas e F12/F13 não homologadas.
