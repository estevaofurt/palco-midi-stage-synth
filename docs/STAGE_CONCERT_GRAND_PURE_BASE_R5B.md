# Diretriz de timbre base puro — R5b (2026-11-25)

Feedback explícito do usuário: R4-presence-z0.3 (run 45538861022, artifact 14987907757) trouxe mais presença, mas ainda há muita ressonância. Não eliminar a ressonância natural do piano: obter timbre base mais puro, com ressonância adicional ajustável nos editores do app.

Decisões de pesquisa: z=.3 m passa a referência provisória de captação; R2-25 mantido. Não reduzir indiscriminadamente sustain ou harmônicos, nem usar corte de volume como correção. Preservar tampo e acoplamento natural; ressonância simpática e de pedal adicionais serão parâmetros físicos/editáveis, ambiente/reverb separado e opcional. Não implementar UI ou declarar modelo homologado nesta etapa. A arquitetura do editor ainda necessita integração e calibração.

R5 run 45539739679: 3/3 success, 16 ataques, zero clipping. L1/L1.5/L2 em z=.6: RMS ataque -41.13/-41.19/-41.25; acorde -27.77/-27.89/-28.01; held -33.37/-33.92/-34.46; cauda pedal -40.96/-42.31/-43.56 dBFS. 58 modos alterados nos fatores superiores. Mudança moderada, não prova de pureza nem sustentação longa. Nenhum fator selecionado.

R5b reutiliza o renderer R5 sem modificá-lo, z=.3, K750, R25, ganho fixo .20 S50. Matriz 3 fatores x 3 programas: frase original com pedal, mesma frase sem CC64, C4 isolado 10s pressionado + 2s de soltura. Medir janelas equivalentes, ouvir com nível percebido comparável, verificar redução de excesso sem deteriorar sustentação/ataque. A nota de 12s não certifica meta de 30–35s ff. Se insuficiente, estudar posições de ponte distintas e modos do tampo por contribuição, antes de aumentar perdas gerais. F12.5 segue obrigatório. Main/S50 preservados.
