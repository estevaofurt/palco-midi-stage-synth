# Concert Grand III — checkpoint de continuidade

Atualizado em 28/11/2026. Este índice acompanha a evolução da branch de pesquisa desde o [executor de retomada](https://github.com/estevaofurt/palco-midi-stage-synth/commit/19fb3673bfd1c2578931ec01a47cb528e81d6dff). O [contrato de engenharia](contrato.json) e a [especificação](ESPECIFICACAO_G3.md) definem a sequência de aprovação. Resultados, scripts e instruções detalhadas estão nos pacotes abaixo.

- [Sustentação com pedal aberto, 500 ms](https://chatgpt.com/library?file_id=libfile_28f7ae536de08191ace83b6f54413fe2&account_id=personal)
- [Soltura do pedal, 850 ms](https://chatgpt.com/library?file_id=libfile_8037b0a706408191b540073aa1aa74d9&account_id=personal)
- [Soltura gradual, 850 ms](https://chatgpt.com/library?file_id=libfile_a26e9d918e488191a1fc3d728accb35c&account_id=personal)
- [Motor físico regional](https://chatgpt.com/library?file_id=libfile_c345c938ad9c8191ba13718cdcaad3a4&account_id=personal)
- [Renderização MIDI offline](https://chatgpt.com/library?file_id=libfile_1b5c633aa3408191a15c2e8cdedeefa3&account_id=personal)
- [Auditoria do martelo](https://chatgpt.com/library?file_id=libfile_b476eedcbf7c8191bbbc291416d9b3ca&account_id=personal)
- [Curvas força–tempo com estrutura compartilhada](https://chatgpt.com/library?file_id=libfile_2754aa8703c0819198070a5e01c4370f&account_id=personal)
- [Curvas com carga vibroacústica](https://chatgpt.com/library?file_id=libfile_51913da56e40819195e3380a6bfc0bf8&account_id=personal)
- [Confronto experimental em C4](https://chatgpt.com/library?file_id=libfile_eba499acacc48191b78a314c579725cc&account_id=personal)
- [Referência de contato nos agudos](https://chatgpt.com/library?file_id=libfile_a6669561e41c8191a7bf782c071d34b0&account_id=personal)
- [Comparador de curvas força–tempo](https://chatgpt.com/library?file_id=libfile_46ba6fb43de88191b5891e22df631a52&account_id=personal)
- [Espectro da força do martelo](https://chatgpt.com/library?file_id=libfile_5717bb5e912881919221fa8f3ea0a61c&account_id=personal)

- [Pressão simulada no ataque forte de C8, 30 ms](https://chatgpt.com/library?file_id=libfile_9d45e51808ac8191b6cd4938ab8f08a6&account_id=personal)

- [Pressão simulada de C8 leve e médio, 60 ms](https://chatgpt.com/library?file_id=libfile_dd4145c8d7108191b10caffffb058f4a&account_id=personal)

- [Pressão de Si7 e Dó8 leve e médio, 100 ms](https://chatgpt.com/library?file_id=libfile_acd0031b0ef8819197d219dcfbc83ec2&account_id=personal)

- [Decomposição por bandas do decaimento de Si7 e Dó8](https://chatgpt.com/library?file_id=libfile_1ab16a9cb82c8191969441e07e229599&account_id=personal)

- [Decomposição por portas no decaimento de Dó8 leve](https://chatgpt.com/library?file_id=libfile_3500e41571588191954ebbda22593e44&account_id=personal)

- [Estados internos no decaimento de Dó8 leve](https://chatgpt.com/library?file_id=libfile_59dfdc2650a4819198f903f3a09a43b9&account_id=personal)

- [Transferência isolada dos estados do tampo e da cavidade](https://chatgpt.com/library?file_id=libfile_ae24d5360a508191b12aa9a1ceb06370&account_id=personal)

- [Contribuição dos estados em Dó8 leve com fase real](https://chatgpt.com/library?file_id=libfile_e487fb096a6081919e3ec6a931da06ce&account_id=personal)

- [Auditoria modal de Dó8 leve em seis janelas](https://chatgpt.com/library?file_id=libfile_16eedaf4ca4481918f8501894320e288&account_id=personal)

## Estado técnico

O motor offline recebe MIDI e gera áudio em sete notas da escala regional. A G3.02 segue aberta. O feltro graduado em C8 é um candidato experimental. A simulação demonstrou mudança no espectro da força durante o contato. O ensaio de pressão simulada de C8 forte em 30 ms encontrou +0,74 e +0,39 dB de energia de pressão no total, com +3,51 e +14,05 dB nos primeiros 5 ms (graduado sobre original). Em 60 ms, o ataque leve marcou +3,18/+2,98 dB e o médio +1,08/+0,77 dB. Na janela 30–60 ms, o efeito permaneceu nos dois observadores. Repetir o ataque médio com 128 modos mudou o contraste em menos de 0,00018 dB. Em 100 ms, o aumento da energia de pressão se repetiu em Si7 e persistiu de 60 a 100 ms para Si7 e Dó8. Entre 60 e 100 ms, 92,22–99,21% da diferença líquida ficou em 300–650 Hz na análise retangular. Em Dó8 leve, os grupos 0–79 e 80–368 contribuíram para o aumento da pressão em 300–650 Hz, com compensação no termo cruzado. A projeção estrutural de 443,42 Hz e o estado acústico nominal de 528,53 Hz coincidiram com bins relevantes da pressão. Com energia inicial igual, o teste isolado gerou picos de 450 Hz para a projeção estrutural e 525 Hz para a cavidade. Com os estados efetivos aos 60 ms de Dó8 leve, a remoção da projeção do tampo reduziu o bin de 450 Hz em 5,84–8,72 dB. A remoção do estado da cavidade reduziu o bin de 525 Hz em 0,02–0,15 dB. O aumento do feltro graduado em 300–650 Hz persistiu em +2,70/+2,18 dB após a remoção de ambos os estados. A ampliação para 41 modos do tampo e 25 estados da cavidade atribuiu à parcela modal isolada 79,7–104,6% da diferença líquida de energia entre feltros nas seis análises. A retirada de toda a faixa nominal deixou um contraste de −0,58 a +2,58 dB conforme a janela. A validação física continua pendente. Integração de 88 teclas e desempenho em tempo real seguem no planejamento.

## Retomada

1. Abra primeiro os checkpoints de espectro e de curvas acopladas. Confira os hashes e preserve os dados de referência.
2. Isole as contribuições dos modos do tampo com maior diferença de energia, começando por 527–532 Hz e 446,40 Hz. Repita as análises com Hann e janela retangular para verificar interferências.
3. Confronte os candidatos com curvas experimentais comparáveis quando disponíveis. Mantenha a G3.02 aberta até reunir evidência suficiente para o critério do contrato.
4. Ao concluir cada etapa, registre nesta branch a evidência, os limites, a próxima etapa e instruções de retomada. Vincule artefatos grandes aos pacotes versionados. Preserve a branch `main`.

Para iniciar em um novo chat, indique a branch `research/stage-concert-grand-iii` e este arquivo. Os links de arquivo exigem acesso à conta do projeto.
