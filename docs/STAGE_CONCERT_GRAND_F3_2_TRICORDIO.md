# Stage Concert Grand — F3.2 tricórdio, polarizações e limites de truncamento

Data 24/11/2026. Base 51133f0925fbce797e86cafcb3b73f55dd1dec5d. Pesquisa autoral offline; nenhum DSP público, V10, main, áudio ou UI alterado. Nenhuma aquisição nova de PCM. F3 aceita internamente para cordas lineares isoladas, não para timbre ou terminação móvel.

## Modelo e dependências
stiff-string.mjs blob c5b2f2f47cb237e2967530e062a6d039443a2787; exact-modal.mjs blob 5421be767601a96fab1e430453dc5e9b9ea1e2f1; c4-design.mjs blob f17a9e7e5f5aa0c9f9394105164aefad3603b4b5; c4-wire-consistency.mjs blob 8ae5b2bb81a2374ad0cc9bc88030b1c2d20b935a. Três fios maciços de mesma geometria/material, duas polarizações transversais ortogonais, 47 modos por polarização a 48 kHz, total 282. Mesma rigidez conservativa para ambas as polarizações de um fio circular. Perdas verticais sigma0=0,4 s^-1, sigma2=0,0002 m²/s; horizontais 0,2 s^-1 e 0,00012 m²/s, hipóteses explícitas, não identificadas em Yamaha. Não atribuir essas diferenças ao material isotrópico sozinho. Sem transferência entre polarizações/cordas até ligação física; nenhuma energia horizontal aparece por força exclusivamente vertical. Forças vetoriais independentes em cada corda, projeção conjugada no contato (posição hipotética 0,13L, largura 12 mm). Ainda não há um martelo compartilhado, nem ponte móvel; apoio ideal fixo.

| Corda | cents | f1 natural Hz | T N | B |
|---|---:|---:|---:|---:|
|1|-0,5|261,550015785|656,703623|0,000296611815|
|2|0|261,625565301|657,083172|0,000296440484|
|3|+0,5|261,701136639|657,462940|0,000296269252|

A tensão é recalculada pela equação física da F1, não por deslocamento artificial da frequência; mesma massa e EI. Desvios escolhidos para ensaio, não medição nem recomendação para afinação real.

Batimentos teóricos entre as duas cordas externas, frequências naturais n=1/4/8/16: separação 0,151121/0,603144/1,197837/2,331444 Hz, período 6,617220/1,657978/0,834838/0,428919 s. A frequência de batimento não é a frequência da envoltória completa de três cordas. Simulação sem perdas verificou a identidade de interferência de duas oscilações durante 0,1 s; não observou um ciclo completo do batimento fundamental. Detune zero retorna separação zero, período nulo.

## Truncamento dinâmico
Força prescrita 0,1*sin²(pi*t/0,0005) N durante 0,5 ms; total 5 ms simulados a 192 kHz em todas as bases, posição 0,13L. Referência finita de 118 modos abaixo de 70 kHz, não solução contínua exata. Erro RMS relativo do deslocamento conjugado e da força de apoio ideal, sem reamostragem. Comparação de cortes de modos, não de taxa temporal:

| Largura mm | Corte kHz | Modos | Deslocamento erro % | Força apoio erro % |
|---:|---:|---:|---:|---:|
|0|8|27|1,043299|1,075855|
|0|16|47|0,359377|0,100313|
|0|32|74|0,087647|0,073658|
|12|8|27|0,582166|0,788183|
|12|16|47|0,102945|0,204911|
|12|32|74|0,004445|0,115717|

A hipótese inicial de que a força de apoio sempre tem erro maior que o deslocamento não se confirmou. Não transformar hipótese em critério de aceite: preservar os números, testar finitude e comparação com base maior. O corte de 16 kHz é defensável neste ensaio linear suave, não homologado para impacto não linear, apoio móvel ou pressão acústica. Repetir convergência no contato real da F4 e ponte F5.

## Referência acústica
Alexander Holm, Salamander Grand Piano V3, Yamaha C5, CC BY 3.0, commit 3382bf9496bba2486f5ab0de55a264d1dfc38404, relatório arquivado C5_C4_verified_numeric_report.json blob 63e893d8cfff79c247c0ea76b944885669a8249f; aquisição original CI 45313270498. Usadas amplitudes de pico em janelas corpo 260–700 ms e cauda 900–1400 ms, com contraste >=20 dB e nível relativo >=-60 dB em ambas. 21 pares aceitos (n=2–8, três camadas), fundamentais excluídas. Comparar 20log10(A_cauda/A_corpo) à hipótese de envelope vertical isolado em 0,67 s (distância entre centros). Janelas de durações diferentes e picos sujeitos a interferência/resolução; não estimar coeficientes de perda mecânica a partir disso. C5 v8 n=2..8: -19,661/+2,147/-4,791/-5,938/-19,535/-9,512/-9,467 dB. Envelope vertical isolado: -2,437/-2,573/-2,763/-3,008/-3,307/-3,660/-4,068 dB. Não são saídas equivalentes; não atribuir divergências a uma causa específica nem corrigir com EQ por parcial. Crescimento de magnitude de pico em algumas janelas não prova energia mecânica crescente. Sem calibração acústica independente.

## Testes e decisão
14/14 verificações executadas no ambiente JavaScript V8: bancos, retensionamento, afinação, perdas, isolamento, balanço de trabalho e energia, monotonicidade, identidade de batimento, uníssono, qualidade da fonte, truncamento e entradas inválidas. F3.1 + F3.2 = 33 verificações. Reprodução: `node research/stage-concert-grand/trichord.test.mjs`. Commits 8df9867eabee4978f1ba946ae176d5004774c821 e 789c7bfee997c5ba0418873a366748f986105d7b. Sem execução nova de Node/CI/hardware.
F3 aceita internamente somente como infraestrutura de cordas lineares com apoios fixos; perdas e uníssonos são hipóteses, devem ser revisitados em F5/F8/F9. Próxima F4.1: martelo com massa explícita, contato unilateral não linear com energia elástica do feltro, força distribuída entre três cordas, reação igual/oposta, dissipação não negativa, ensaios de convergência e soltura. Nenhum WAV de piano até F8. Preservar meta 32–64 vozes, sem alegar homologação de hardware.
