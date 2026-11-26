# G3.11u — observador mecânico offline

G3.11t unitários aprovados; prova extensa ainda em execução no início da etapa. Densificação G3.11g pendente. Não usar impedância rejeitada nem confundir quatro campos sintéticos com microfones.

Observar velocidade de ponto médio dos quatro campos de tábua com duas direções lineares fixas. Sem feedback, sem pressão acústica e sem posição física de microfone. Comparar referência densa, silêncio exato, partição bitwise, energia. Decimar offline 96 para 48 kHz com FIR polifásico Kaiser 8.6; verificar 1 kHz e rejeição 35 kHz. Seis sinais sintéticos de 0.22 s, 2 vozes, 4 parciais, velocidades 32/80/127, com/sem pedal. Guardar dados brutos NPY e WAV PCM16 com ganho comum aos seis sinais; nenhuma normalização por nota. WAV é sonificação de velocidade mecânica, não amostra de piano calibrado. Não validar sustain, timbre ou polifonia. Main preservada.
