# Histórico de correções — Palco MIDI

## v1.2.0 — Confiabilidade e dinâmica

- A curva de toque e a dureza do martelo passaram a afetar também o **piano de síntese alternativo** usado quando as gravações originais não estão disponíveis. Acrescentado quarto harmônico em notas graves/médias para ampliar a resposta tímbrica; não é substituto de biblioteca profissional de samples.
- Corrigido acionamento duplicado via **Enter/Espaço** quando o navegador emite `click` sintético após o teclado virtual já ter recebido `keydown`/`keyup`.
- Acrescentadas teclas do computador (A/W/S/E/D/F/T/G/Y/H/U/J/K etc.) para tocar sem controlador MIDI. Atalhos são ignorados em campos e seletores; soltar tecla ou perder foco encerra notas do teclado do computador.
- Indicador de polifonia e teclas pressionadas adicionado ao rodapé, sem substituir o medidor de nível de áudio.
- O callback de encerramento de vozes atualiza os contadores inclusive quando fontes são finalizadas após o `note-off`.
- Reforçada a rejeição de mensagens MIDI malformadas fora da faixa de notas/controladores.
- Adicionados testes automatizados para curva de toque e polifonia; testes Chromium cobrindo rajadas MIDI, sustain, modo duo, desligamento do dispositivo, clique de teclado e comando de pânico.

**Limites conhecidos:** o banco de amostras do piano continua ausente; nenhum teste físico com controlador MIDI foi realizado; efeitos avançados, leitor SF2, looper e arpejador não foram implementados. A qualidade sonora depende do navegador e do dispositivo de áudio.

# Histórico de correções — Palco MIDI

## v1.1.0 — Estabilização após recuperação de arquivos

- Corrigido `index.html`: a cópia salva do navegador trazia controles criados em tempo de execução (motores, editores, cenas, medidor e teclas). Agora o HTML mantém somente os recipientes e `app.js` constrói cada componente uma única vez.
- Corrigido o estado visual inicial: o áudio não aparece como ativo antes de o navegador autorizar o `AudioContext`.
- Corrigido o acesso ao botão da cena personalizada durante a inicialização.
- Corrigido o carregamento da biblioteca opcional de piano: se faltarem os arquivos da pasta `piano/`, o programa informa que está usando síntese de piano e não repete requisições a cada tentativa de ouvir.
- Endurecida a proteção contra falha de instrumento: falhas em uma voz não impedem a execução de outras notas ou deixam entradas órfãs no registro de vozes.
- Reforçada a limpeza de fontes de áudio durante soltura e corte de som.
- Ajustado o controle do teclado virtual para ignorar referências obsoletas ao mudar oitava e proteger a captura do ponteiro em navegadores diferentes.
- Removidas declarações de fontes que apontavam para arquivos não recuperados. Mantidos os estilos e fontes de fallback existentes.
- Incluídos testes automatizados de estado, presets, cenas e persistência; testado fluxo dos quatro motores no Web Audio API em Chromium.

### Limitações que permanecem

- As gravações originais da pasta `piano/` não vieram no backup; o piano acústico ainda utiliza síntese alternativa, que **não** equivale a bibliotecas profissionais de piano.
- O som não foi homologado com um teclado controlador MIDI USB real, nem em todos os navegadores/dispositivos.
- Os módulos novos de SoundFont, arpejador, looper, split avançado e efeitos ainda não estão implementados nesta base recuperada. Não devem ser apresentados como concluídos.
