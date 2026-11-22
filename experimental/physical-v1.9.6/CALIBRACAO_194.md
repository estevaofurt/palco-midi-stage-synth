# Calibração de 4 pianos — experimento v1.9.4

**Referências fornecidas pelo usuário:** `Japanese.wav`, `American.wav`, `Felt.wav` e `Upright.wav`, com os **efeitos originais dos instrumentos** mantidos. Os arquivos permanecem fora do repositório e **não integram** o motor sonoro.

## O que foi efetivamente medido

As quatro gravações estão alinhadas. Identificou-se uma passagem próxima do **Dó4 (~261,63 Hz), iniciada em aproximadamente 82,52 s**, que aparece nos quatro arquivos. As medidas abaixo vêm de janelas de 180 ms iniciadas 280 ms após esse ataque. A queda de nível usa janelas 90 ms e 700 ms após o ataque.

| Modelo | H2/H1 na referência | Motor v1.9.3 | Motor v1.9.4 | Queda 0,09–0,70 s na referência | v1.9.3 | v1.9.4 |
|---|---:|---:|---:|---:|---:|---:|
| Japanese | +7,81 dB | −7,16 dB | **+6,55 dB** | −18,47 dB | −2,15 dB | **−18,01 dB** |
| American | −11,61 dB | −8,88 dB | **−12,89 dB** | −9,11 dB | −2,58 dB | **−8,38 dB** |
| Felt | −10,77 dB | −7,11 dB | **−11,94 dB** | −11,30 dB | −3,96 dB | **−11,19 dB** |
| Upright | −2,43 dB | −9,20 dB | **−2,42 dB** | −11,75 dB | −2,70 dB | **−12,75 dB** |

Valores calculados com `tests/reference_analysis_v194.py` em ambiente local e salvos em `CALIBRACAO_194.json`. Os novos valores sintetizados usam MIDI 60, velocidade 0,75, brilho 0,5 e dureza 0,6, com renderização a 48 kHz. A velocidade exata da captura não foi informada. Não se deve interpretar coincidência de alguns valores como equivalência subjetiva ao piano original.

## Alterações no DSP

- `physical-piano.js`: quatro perfis separados com **pesos de harmônicos por instrumento** e atenuação progressiva em registros afastados do Dó4 (evita extrapolar uma única nota para o teclado inteiro).
- Decaimento rápido inicial por voz, seguido do corpo sustentado; processado com uma multiplicação por amostra, coeficientes calculados na criação da nota.
- Contorno de emissão por nota **mais quente em American e Felt**, com um filtro de primeira ordem dependente do registro, anterior à ponte/tampo.
- Panorâmica levemente diferenciada por instrumento.
- Mesma arquitetura sem samples, mesmo banco de cordas pré-alocadas e 32/48/64 vozes dependendo da qualidade.

## Limitações honestas

- Os WAVs incluem efeitos originais, ressonâncias e possivelmente notas sobrepostas; não são capturas secas com eventos MIDI documentados. Assim, a comparação refere-se ao **som final ouvido** e não revela constantes físicas exatas do martelo ou das cordas.
- Esta etapa calibra o comportamento em **um registro**. Ainda faltam notas isoladas em graves/agudos, diferentes intensidades MIDI e parâmetros de pedal para calibração multi-registro.
- Um timbre fisicamente convincente exige avanço no contato martelo–corda não linear, no acoplamento de 2/3 cordas, no tampo harmônico e na espacialização; uma igualdade de H2/H1 e decaimento não é prova de realismo.
- O navegador de testes carregou a interface em resoluções desktop/Android sem erros; **a ferramenta local bloqueou o acesso direto do Chrome ao servidor localhost**, impossibilitando confirmar a execução do AudioWorklet real no browser. Homologação física no Moto g04s continua pendente.

## Testes e desempenho

- `npm run check`: **62 testes aprovados**, incluindo novos testes de diferença espectral e envelope.
- Renderização CPU Node.js, 48 kHz, 1 s de áudio em acordes simultâneos com quatro timbres: **~81 ms por segundo de áudio com 32 notas** (eco), **~201 ms com 64 notas** (studio), na máquina de testes. São tempos *offline*, não medidas de latência, gargalos em buffers de 128 amostras nem garantia no Moto g04s.
- Na simulação de 32 e 64 notas, amostras não finitas: zero; pico medido inferior a 0,26 no ensaio.
- `tests/browser_physical_ui_v19.py`: interface passou em perfil Android e desktop.

## Próxima etapa

Usar calibração por registro e velocidade; comparar diretamente o A/B ouvido pelo usuário; depois melhorar o martelo e a resposta acústica sem ultrapassar o custo de CPU de um celular básico.
