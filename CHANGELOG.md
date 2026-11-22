## v1.7.0 — seleção do órgão e síntese em tempo real

- Corrigido o seletor do órgão para distinguir B3 Jazz, B3 Gospel e Church.
- Migração de preferências e presets antigos de órgão (campo `type` para `registration`).
- Implementado Unison dinâmico para notas de Synth já iniciadas, com transição de ganhos.
- Matrix Velocity/Aftertouch agora redireciona a modulação à voz ativa.
- Portamento com rampas entre notas em Poly/Mono/Legato; ajuste de glide não cancela uma rampa em curso.
- Mudança para Mono/Legato limita as notas já ativas; `panic`/desconexão limpam o histórico de portamento.
- Ajuda contextual no editor explicando quando o glide é ouvido.
- Testes: 27 lógicos aprovados, validação de navegador e corte de vozes.

# v1.5.0 — Motor modal e roteamento FX

- Adicionado modo experimental de síntese modal para piano, rodando em AudioWorklet e com fallback à síntese clássica.
- Perfis iniciais Japanese, American, Felt e Upright com corpo, inarmonicidade e decaimento diferenciados.
- FX por instrumento com bypass independente; efeitos podem ser atribuídos a zero, um ou diversos instrumentos.
- Configurações antigas de um destino migram sem perder a seleção.
- Ocultada a importação manual de arquivos WAV no painel (SF2 permanece).
- Limitações: não equivale a modelagem física completa de martelo e tampo harmônico; requer ensaios em teclados MIDI e dispositivos móveis.

# Stage Synth · Histórico de versões

## v1.4.0 — Controles, presets, Auto-Pan e caminho para áudio real

- Grade de knobs responsiva: dimensionamento automático por espaço, quebra segura de rótulos, sem colisões em seis resoluções de teste.
- Separação explícita de seleção de **Instrumento** e **Preset**. Cada modelo de piano acústico, piano elétrico, órgão e SoundFont tem variantes Natural, Suave e Brilhante. IDs antigos de presets preservados.
- Selecionar outro instrumento aplica seu preset Natural e impede divergência de configuração visual. Estado salvo legado com modelo diferente do preset é reconciliado.
- Pianos elétricos: Pan estático removido; **Auto-Pan** com intensidade, velocidade e LFO independente conectado à panorâmica estéreo. Tremolo mantido.
- Piano acústico sintetizado: parciais inarmônicos e uníssono discretamente desafinado para reduzir sonoridade de osciladores puros. Não é substituto de um piano gravado.
- Importação opcional de arquivos de amostras locais WAV/OGG/MP3 (quando decodificáveis pelo navegador), identificando nota e velocidade pelo nome; carga separada por instrumento, sem upload externo.
- Ampliação da validação automatizada: 17 testes de lógica; navegador de seis larguras, trocas de presets, teste de Auto-Pan e amostras; estresse de 60 notas, polifonia e MIDI simulado.
- Persistência anterior preservada por compatibilidade e biblioteca de áudio de teste removida da distribuição.


## 1.3.0 — Seis módulos, instrumentos e performance

- Evolução da base original v1.2.0 para **5 motores independentes + rack de efeitos** com seis cartões e editores.
- Piano acústico: Japanese Grand, American Grand, Felt Piano e Upright; caracterização dos modelos, curvas de dinâmica, ruído de martelo/pedal, release e controle da ressonância de cordas.
- Pianos elétricos: nove timbres Rhodes/Wurly/CP80/Clav/FM; amplificadores, posições de microfone, preamp, panorama, tremolo e ruídos mecânicos.
- Órgãos B3 Jazz/Gospel e Church com Leslie, vibrato, percussão, key click e drawbars.
- Sintetizador ampliado: OSC A/B, pulse width, uníssono, afinação, mistura/ruído, hard sync aproximado por wavetable, filtros VCF, envelope ADSR, LFO, matriz de modulação limitada, modos de voz e glide.
- Leitor SF: cinco famílias de timbres internos e importação SF2 PCM na memória, com seletor de programas e suporte básico a zonas/amostras.
- Rack de **8 sessões**: dois reverbs, dois delays, dois efeitos de modulação, EQ e compressor; endereçamento e ativação por módulo e por sessão.
- Arpejador com BPM/subdivisão, Chord Mode e looper de 1–4 barras; execução integrada a teclado virtual, teclas do computador e entrada MIDI.
- Mantido limite de 32 notas, botão de pânico, persistência local de presets e temas escuros. Layout revisto para celular.
- Eliminação de requisição HTTP de piano sabidamente ausente; banco de gravações permanece pendente.
- Testes: 12 testes Node aprovados; navegador verificou os seis módulos, os oito slots, os cinco motores sonoros, um SF2 sintético, looper/acordes e responsividade; teste de estresse com 60 notas sem exceder 32 vozes e sem notas presas após corte.

### Limites ainda abertos

- Perfis de piano sintetizados não substituem amostras reais da Yamaha CFX ou Steinway.
- Suporte SF2 inicial: não há SFZ/SF3, nem modulação abrangente do padrão SF2; bancos reais precisam de testes adicionais.
- Hard sync usa aproximação por tabela de onda; a matriz de modulação é simplificada.
- Looper e SoundFont importado são dados temporários por sessão, não persistidos.
- Testes com controlador físico, latência e estabilidade prolongada de palco ainda pendentes.

---
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

## v1.5.0 — Interação e FX
- FX/FX OFF por módulo (atalho de bypass sem perder configurações).
- Cada efeito roteado simultaneamente para vários motores, migrando presets anteriores.
- Duplo clique para restaurar valor original de knobs, drawbars, volume e sliders de efeitos.
- Atualização de filtros, efeitos e parâmetros editáveis durante a execução; controles de ataque passam a afetar as próximas notas.
- Motor modal experimental com fallback clássico e correções de perfil e damping.

## v1.6.0 — Edição de vozes em execução
- Corrigida a propagação de mudanças de parâmetros para notas que já estão tocando; os motores antes não implementavam `part.update` de maneira uniforme.
- Piano Acústico: timbre do martelo (filtragem), abafamento, intensidade da ressonância e tempo de release em notas sustentadas. Modo modal recebe mensagens de atualização de decaimento sem novo ataque.
- Piano Elétrico: Pickup, dureza tonal e decay em execução, e release da voz. Auto-Pan, tremolo e gabinete continuam atualizando o áudio global.
- Órgão: drawbars, vibrato e Leslie permanecem globais e instantâneos; mudança de release reflete na voz ativa.
- Synth: agora afinação (oitava/semitons/fine), VCA (inclusive de 0% para valor audível), ADSR, ruído branco/rosa, níveis dos osciladores e filtros passam a atuar nas vozes existentes. O tipo de onda, pulse width e hard sync seguem ajustáveis ao vivo.
- Leitor SF: brilho, panorama e release atualizam vozes em andamento; ataque de uma nota ainda em fase de ataque também pode mudar.
- `AudioParam` é suavizado para reduzir cliques. `stage.update` notifica vozes existentes, incluindo caudas ainda ativas.
- Parâmetros estruturais e fenômenos de ataque (novos osciladores de uníssono, modo de voz, velocity já recebida, Key Click/Hammer Noise) se aplicam à próxima execução, pois não é tecnicamente correto recriar retroativamente o ataque de uma nota.
- Validação: 24 testes automatizados; Playwright simulou uma nota sustentada em cada motor e comprovou alteração de parâmetros ativos, além de bypass FX. Regressão de polifonia e interface aprovada.
- Pendente: teste com AudioWorklet em HTTPS e teclado MIDI físico em equipamento real.
