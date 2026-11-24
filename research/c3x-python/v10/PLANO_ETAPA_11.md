# Etapa 11 proposta — preparação para execução em tempo real

**Condição inicial:** V10 funciona e é testada offline. Não presumir VST pronto nem performance real-time a partir de benchmark offline.

1. Separar agendamento de ações e integrador físico para processar blocos consecutivos de 64/128/256 amostras sem zerar os estados das cordas, martelos, tampo ou pedal.
2. Criar interface de eventos MIDI com timestamp por amostra: note on/off, sustain CC64 e, quando disponível, aftertouch/profundidade de tecla. Manter suporte a keyframes V10 para ensaios físicos.
3. Alocar estados na inicialização, evitar processamento em Python no caminho de áudio e validar Numba/C++ ou DSP em processo sem bloqueios e sem alocação no callback.
4. Medir CPU, latência, dropout e consumo de memória sob 1, 8, 16 e 32 notas simultâneas em pelo menos 44,1 e 48 kHz, sem sacrificar a física nem os parciais.
5. Criar testes bit a bit e testes perceptuais de parciais V9/V10 contra o processamento em blocos; verificar pedal e repetição nos limites de blocos.
6. Isolar definitivamente a ambiência em um módulo de efeitos externo desligado por padrão. Preservar o motor dry e a ressonância natural do instrumento.
7. Coletar dados reais de um Yamaha C3X, preferencialmente instrumentos e microfones documentados, usando gravações apenas para análise/comparação, nunca como amostra fonte do modelo.

**Critérios de saída:** dados não perdidos entre blocos, mesmo som offline/blocos dentro de tolerância testada, desempenho sustentado em tempo real em Windows/ASIO medido, e comparação auditiva aprovada antes de alterar o preset principal.
