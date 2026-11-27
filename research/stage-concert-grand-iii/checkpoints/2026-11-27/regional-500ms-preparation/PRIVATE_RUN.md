# Execução física privada e retomável (500 ms)

O pacote histórico continua privado. Não é copiado para GitHub Actions, não é publicado no repositório e não se usa um modelo substituto. O ambiente local do assistente segue indisponível; nenhuma nova simulação física foi executada nesta etapa. A alternativa local requer que Python 3.11+ e versões compatíveis de NumPy/SciPy/Numba já estejam instalados no computador de execução. Recomenda-se reproduzir o ambiente histórico, pois igualdade exata pode depender da plataforma e versões.

Com esta pasta de código e o ZIP original de 250 ms:

```
python private_run_500ms.py --package "C:/dados/G3_Continuidade_Regional_250ms.zip" --workdir "C:/dados/G3_500ms"
```

O diretório precisa ser novo e o disco ter pelo menos 12 GiB livres. Para só validar e preparar os arquivos, acrescente --prepare-only. Para continuar um workspace preparado ou interrompido entre etapas completas:

```
python private_run_500ms.py --workdir "C:/dados/G3_500ms" --resume-work
```

O lançador verifica o SHA-256 do ZIP, as 182 entradas do manifesto, as fontes copiadas e os resultados já concluídos. Mantém nove etapas com recibos e logs locais. Se houver interrupção dentro de uma etapa, ele para e preserva os arquivos parciais: não afirma retomada automática de uma execução contínua incompleta. Inspecionar logs e snapshots antes de qualquer recuperação manual. Os checkpoints planejados do terceiro caso são 22000, 96000, 153600. A retomada física prolongada só será aprovada após comparação com a execução contínua. Todos os critérios de aceitação anteriores permanecem. O relatório acceptance-500ms.json só é emitido após a última auditoria. Não é necessário executar um servidor ou tornar os arquivos públicos.

Os testes unitários são fixtures de I/O e verificam recibos, integridade, preservação de dados parciais e critérios de aceitação. Não são experimentos mecânicos/acústicos. Nenhuma mudança na main.
