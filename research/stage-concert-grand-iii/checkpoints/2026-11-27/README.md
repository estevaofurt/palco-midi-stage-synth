# G3 — checkpoint de consolidação 2026-11-27

Estado: pesquisa, não promovido. Base Git anterior: a9b2929b7ef197f8e6c97cf16955cb8dfcd5d09f. Base histórica dos renders: a9fd2ac6b7ccf18dafd03f77bc0d72de4f96d08e.

## Decisões
- Concert Grand III; normalização física corrigida; d3 a 48 kHz; 8 subpassos a 384 kHz.
- 80 portas superiores + 289 inferiores, geometria piloto 30×30, 127.825 estados da cavidade.
- Preservar pre-correction/ como auditoria; não usar para promoção.
- Sem alteração na main, merge, render sonoro ou aprovação de tempo real.

## Inventário verificado localmente
11 ZIPs, 257 entradas dos manifestos internos verificadas por SHA-256, nenhum erro CRC. Das 32 dependências anteriormente faltantes, 20 foram recuperadas com hash idêntico e 12 seguem ausentes (MISSING.sha256, caminhos relativos à raiz restaurada). Os quatro pacotes adicionais recuperam abertura, cavidade compacta, exterior acoplado e atrasos físicos.

Os hashes em ARCHIVES.sha256 identificam os ZIPs exatos. **Os ZIPs e seus conteúdos ainda não foram publicados por este commit.** O acesso ao GitHub por conector permite versionar texto, mas o ambiente local não consegue acessar github.com para enviar os binários; não existe release criada nesta etapa. Não confundir este inventário com backup remoto completo.

## Reprodução do inventário
Python 3.12 ou superior:
```sh
python restore.py /caminho/dos/zips /nova/pasta/g3
```
O teste local verificou 11 arquivos ZIP, 257 entradas internas e retornou código 2 (12 dependências ainda faltantes), sem divergências. Código 1 indica divergência. A execução não roda o motor nem implica validação física. Preserve os nomes das pastas irmãs. Use os comandos e versões de dependências dos CHECKPOINT.md individuais.

## Publicação e continuidade
Versionar código, testes, parâmetros e relatórios em diretório de pesquisa isolado; armazenar os ZIPs imutáveis como assets de release de pesquisa (preferencialmente rascunho até auditoria), com ARCHIVES.sha256; evitar blobs grandes no histórico. Completar as 12 dependências com os seis pacotes: G3_Reconstrucao_Estrutural, G3_Cavidade_Continua_Passiva, G3_Exterior_Esferico_Passivo, G3_Revisao_Geometrica_Fundo_Aberto, G3_Reacao_Acustica, G3_Terminacoes_das_Cordas. Verificar os hashes exatos e demais manifestos transitivos antes de executar a cavidade corrigida. Revalidar 6/12 portas, depois 369; manter d3, d6/d8 para diagnóstico; validar ataque, afinação, sustentação e desempenho antes de promover qualquer candidato. A escuta formal permanece no final.

Resultados físicos históricos: projeção exterior até 48 portas e memória causal particionada; acoplamento completo de 369 portas e balanço energético da cavidade ainda pendentes. Os experimentos sintéticos não são validação do piano.
