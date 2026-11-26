# G3.13m — ressonância média relatada pelo usuário

Áudio 45-release_pedal_3_w0.0_loss1.0_40s.wav, PCM16 estéreo 48k 40.03s, baseline A2 forte. FFT Hann 1s: canal2 fundamental 110Hz 73.8/84.5/76.5/65.0/42.6/27.5/11.2% em 1/3/5/7/10/12/15s; 669Hz 3.3/5.8/8.0/10.6/13.3/13.1/10.3%; 783Hz 1.0/1.8/2.7/3.8/5.2/5.5/4.7%. Janelas +/-4Hz, fração de energia espectral, não volume absoluto. 220Hz segundo harmônico predominante no início, não declarar defeito só por presença. Não atribuir percepção exclusivamente a uma frequência.

Auditar os 24 WAVs físicos float32 existentes (4 notas, 2 velocidades, 1/4/12 perda) com hash, faixa média 250-1500Hz excluindo fundamental, alta >=1500Hz, picos médios, 10 frequências específicas, energia absoluta e relativa, referência fixa por ataque/canal, depois de 1/5s. Alerta exploratório >=30% energia média e nível médio >=-80dB do pico original. Não implica audibilidade; acima 500Hz diagnóstico. Nenhuma nova alteração física ou EQ.

G3.13l run 45823298620 falhou em unitário fixed_thresholds por fixture sem channel. Corrigir fixture; workflow reexecutado. Motor estável intacto.