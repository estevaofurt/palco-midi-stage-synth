# Comparação de motores de piano — Stage Synth v1.12.4

O usuário pediu a comparação dos motores sem adicionar novos módulos, categorias ou links. O controle **Motor do piano** está no módulo **Piano Acústico → Identidade e dinâmica**.

| Opção | Algoritmo implementado | Fonte verificada | Observação |
|---|---|---|---|
| **A · Claude (modal)** | `piano-worklet.js`, síntese modal | motor modal da linha de comparação Claude já integrado ao Stage | é uma versão **derivada/adaptada**, não há evidência de que seja uma cópia bit a bit do motor externo original |
| **B · Stage físico anterior (v1.9.5)** | `physical-piano-legacy.js`, AudioWorklet independente | blob Git `0e7e64a3e0188dc3ae2f2e2b81a63a86b6a25a52` do arquivo `experimental/physical-v1.9.5/physical-piano.js` | código original preservado, apenas nome do processador alterado para evitar registro duplicado |
| **C · Novo Stage mecânico** | `physical-piano.js` + `piano-resonance.js` | v1.12.3 integrada | ponte, tampo e cordas simpáticas como experimento |
| **Clássico · compatibilidade** | síntese antiga WebAudio | `acoustic.js` | fallback para navegadores sem AudioWorklet |

**Importante:** o chamado **Novo Stage v1.11.0** publicado em outra conversa (tampo estéreo com duas zonas) NÃO foi recuperado como código-fonte no repositório central. A opção B é a versão estável v1.9.5, não deve ser apresentada como a v1.11.0. Para reproduzir a comparação original da outra conversa, será necessário importar a fonte exata da v1.11.0.

## Regras de funcionamento

- Mudanças de motor liberam as notas do piano e não encerram notas de outros instrumentos em camadas.
- Motores legados são instanciados sob demanda, evitando custo na inicialização.
- Presets anteriores com `soundEngine=physical` continuam selecionando o motor C.
- Qualidade `eco`/`balanced`/`studio` preserva 32/48/64 vozes **teóricas** nos waveguides B/C. O motor modal A está limitado a 32 vozes nesta versão.
- A ausência de estalos foi relatada pelo usuário ao testar a v1.9.5. Os novos motores precisam de medição em PC/Moto g04s real.
- Os 84 testes de Node e a regressão visual desktop/Android simulado passaram. O Chrome de testes bloqueou conexões localhost por políticas do ambiente (`ERR_BLOCKED_BY_ADMINISTRATOR`), então a execução real do AudioWorklet ainda não foi validada nesse ambiente.
- Não há alteração dos WAVs de referência; não publicar sons capturados sem direitos de distribuição.

## Próxima etapa

Obter o código original da v1.11.0 e inseri-lo como mais uma alternativa no **mesmo seletor**, ou substituir o rótulo B após validação e testes, sem criar novo módulo.
