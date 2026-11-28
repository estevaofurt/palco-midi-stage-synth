# G3.02 — auditoria da definição de contato e preparação da convergência

Origem imutável: 733391f4067845f9e679b5f6e10b75ed0acfcf94. Leitura e recálculo do JSON de resultados arquivado, não nova integração física. As 48 comparações de energia em 300–650 Hz confirmam o candidato intermediário entre original e graduado. Os quatro impulsos excedem o graduado em 0,047–0,190%.

## Distinção física

O Impact em physical_hammer_contact.py inicia o martelo 0,0001 m antes da corda. pressao_c8.py registra capture_step a partir do lançamento, e comparar.py denomina esse intervalo contact_ms. O intervalo inclui a aproximação e não mede diretamente a duração de força positiva. O JSON de auditoria mantém os números originais e separa o tempo nominal de aproximação (distância/velocidade). Subtrair esse tempo não substitui a inspeção da força por passo; eventuais intervalos internos sem contato e o critério de captura precisam ser distinguidos.

## Literatura reaberta

- Askenfelt e Jansson, Five lectures on the Acoustics of the Piano (1990), String contact duration and dynamic level: https://www.speech.kth.se/music/5_lectures/askenflt/stricont.html . A duração decresce com a dinâmica e do grave ao agudo, chegando abaixo de 1 ms no agudo mais alto; depende de massa relativa e posição de ataque. A figura 7 apresenta faixa pp–ff. Não usar a faixa como medida do Yamaha C5 nem impor limiar único sem velocidades e geometria comparáveis.
- Experimental investigation of the piano hammer-string interaction (2013), https://pubmed.ncbi.nlm.nih.gov/23556611/ . O resumo informa observação óptica de deslocamentos e velocidades de impacto de 1,06 a 2,98 m/s, e discute identificação do contato. Não foi recuperada curva de Si7/Dó8 em condições equivalentes; não há calibração experimental neste checkpoint.
- Giordano e Winans (2000), https://pubmed.ncbi.nlm.nih.gov/10790050/ . O resumo identifica efeitos da flexão da haste e propagação da força no feltro em impactos sobre objeto rígido. Não igualar impacto rígido a cordas reais.

## Execução seguinte

Usar os mesmos insumos físicos do pacote G3_02_Feltro_Intermediario.zip e a cadeia de dependências do CHECKPOINT_ATUAL.md. O executor pressao_c8.py já aceita --partials 128. Repetir os quatro casos 107-24, 107-76, 108-24, 108-76 em diretório separado, sem modificar velocidade, prior, geometria ou método. Após execução, usar:

```
python feltro_intermediario/convergencia.py /caminho/run64 /caminho/run128 --output /caminho/convergencia.json
```

O comparador mede duração de força positiva por fio e agregada, intervalos internos sem força, sensibilidade a limiar relativo de 1e-6, erro L2 da força sem alinhamento artificial, impulso, pico, pressão causal e bandas. O limite histórico de 1% da pressão é somente uma triagem numérica neste teste; não equivale à aprovação de contato ou do contrato G3.02. Os dados de 128 parciais ainda não existem neste checkpoint. O código não foi executado em Python nesta sessão: terminal e Python indisponíveis. Os pacotes foram recuperados para o ambiente de trabalho, mas seus hashes não puderam ser recalculados. Sem recalibração, sem render, sem promoção. G3.02 aberta.
