# STAGE SYNTH — F1: critérios verificáveis de evidência e bloqueio de aprovação

**24/11/2026 — Objetivo: converter a pesquisa F1 acumulada em um controle reproduzível de aceite.**

**Situação atual:** F0 concluída conforme roteiro, **F1 Yamaha C3X PENDENTE**, fases F2–F13 não promovidas, V10 preservada, `main` e os áudios publicados sem alteração. O usuário não dispõe de gravação de um C3X e autorizou **Yamaha C5** exclusivamente como referência comparativa. Não pedir que forneça gravações.

## Problema identificado na rota

As verificações F1.1–F1.12 acumulam dados suficientes para apontar um problema matemático da V10 (IR modal que reforça H4 e cancela H5, robustez estéreo variável na referência C5) e melhorar a metodologia. **Não acumulam uma única medição física comprovada do Dó4 no Yamaha C3X escolhido.** Continuar subdividindo F1 com as mesmas amostras poderia criar a impressão incorreta de aprovação progressiva.

## Implementação: `f1_evidence_gate.py`

O controle **não é medidor** e **não tem poder de aprovação**. Ele analisa apenas um manifesto local de medições realmente obtidas:

- Identifica modelo e exemplar individual C3X convencional, sessão, afinação e contexto de sala/captação.
- Exige três arquivos originais da mesma nota **MIDI 60 / Dó4**, dinâmicas `pp`, `mf`, `ff`, tecla sustentada, pedal desligado e sem pós-processamento.
- Confere WAV PCM, frequência de amostragem e **SHA-256 real** de cada arquivo, sem ler/licenciar amostras do projeto como fonte sonora.
- Verifica oito **campos físicos mínimos** com unidades e incertezas: número de cordas, comprimento vibrante, diâmetro, densidade linear, tensão, inarmonicidade, decaimento parcial e posição de impacto. A lista mais completa de **16 lacunas** permanece obrigatória para revisão humana (e para as fases seguintes); oito campos mínimos não substituem ponte, martelo e tampo.
- Rejeita deduzir **simultaneamente** tensão e densidade linear da frequência alvo e chamá-las de medições independentes.
- Exige autorização específica de uso **na análise comercial**, documento de permissão e conferência humana, com direitos de terceiros sujeitos a revisão real.
- Rejeita arquivos fora da pasta de dados, conteúdo alterado após gerar hash, instrumentos C5 no lugar do C3X e pacotes declarados sintéticos.

**Saídas:** `BLOCKED` ou `READY_FOR_MANUAL_REVIEW`. Não existe `F1_APPROVED` automático. A verificação computacional **não autentica o piano real**, não prova a veracidade do consentimento nem a qualidade científica da incerteza fornecida. O estado `READY_FOR_MANUAL_REVIEW` não é conclusão F1: a equipe ainda precisará auditar originais, documentação física, licenças e receber **aceite explícito do titular**.

### Execução a partir da raiz do repositório

```bash
python research/c3x-physical/f1_evidence_gate.py \
  --project-state research/c3x-physical/F1_ESTADO_E_GATES_V2.json \
  --expect-blocked

python -m unittest discover -s research/c3x-physical -p 'test_f1_evidence_gate.py' -v
```

A primeira operação **deve retornar sucesso operacional enquanto o status impresso continua `BLOCKED`**; `--expect-blocked` serve para evitar que o CI trate a ausência de dados como falha de execução ou como avanço científico. Sem esta flag, bloqueio faz o processo retornar código 1.

Quando um conjunto C3X medido e licenciado existir, executar `--bundle /path/evidence.json --root /path/data` para verificar arquivos e manifesto, **sem colocar WAV de terceiros no GitHub**. O usuário não precisa preparar esse conjunto agora. Originais externos ficam em armazenamento autorizado, fora do repositório.

## Linha de trabalho permitida sem C3X

1. **Continuar a usar as gravações C5 CC BY 3.0 apenas para referência/escuta diagnóstica** com atribuição, sem incorporar samples no motor ou rotulá-las como C3X.
2. Preservar o diagnóstico **F1.4–F1.5** que identificou o cancelamento do quinto harmônico pela IR sintética do corpo na V10; não corrigir unilateralmente por EQ.
3. Manter o estudo F1.12 de sensibilidade por canal/janela como restrição metodológica. A diferença de harmônicos entre os canais não prova a radiatividade específica do C3X.
4. Não promover os parâmetros da V10 ou do C5 como físicos do C3X, mesmo com testes numéricos positivos.
5. Só iniciar F2 quando a F1 tiver conjunto físico C3X independente auditável, direitos verificados e aprovação explícita.

## Decisão de qualidade

**A F1 C3X está BLOQUEADA por ausência de material físico específico.** O avanço concreto desta entrega é a prevenção automática de evidências inválidas e uma regra de parada verificável. Não houve inclusão de áudio, versão V11, mudança de timbre, parâmetros do motor, presets ou implantação do aplicativo.
