# Stage Synth — E2.8 | Direção exclusiva de modelagem física (23/11/2026)

## Decisão do titular
Após aprovar auditivamente o demo E2.7 e ser informado que ele usava gravações, o titular determinou: **"quero que seja baseado somente em modelagem física"**. Portanto, não promover o sampler da PR #38 nem o caminho híbrido amostral ao novo piano. Os WAV anteriores E2.7 serão, quando permitidos, **apenas referências externas de escuta**, nunca voz PCM do motor. O mesmo se aplica a respostas ao impulso gravadas: elas não entram na geração sonora do candidato puramente físico.

## Implementação E2.8 — experimento auditável, sample-free
- `research/pure-physical-audition-e28.mjs`: roteiro determinístico de arpejos C maior/A menor e acordes F maior, G7 e C, com pedal CC64 e eventos de noteOn/noteOff, alimentando **exclusivamente** `SharedPassiveModalPiano` da E2.3.
- A E2.3 gera força de martelo por pulso sen² normalizado, múltiplas vibrações de corda com inarmonicidade, dois eixos/polarizações, abafamento com pedal e **molas recíprocas** conectadas a uma ponte/tampo compartilhados. Solver implicit-midpoint passivo, balanço de energia medido.
- `scripts/render_pure_physical_e28.mjs`: exporta **WAV PCM16 mono, 48 kHz, 13 segundos**, sem import de `sample-library.js`, `PianoBank`, `SF2Reader`, arquivos de referência, PCM gravado ou qualquer convolver. Contém uma única projeção das velocidades mecânicas da placa e **ganho global** para audibilidade, com fade de início/fim anti-click. Não soma osciladores nem reverb ao sinal.
- **Não é pressão acústica real:** a velocidade generalizada `boardVelocity` não está em m/s calibrados, e a escuta do WAV não constitui demonstração de realismo de piano. É uma amostra do **solver físico**, não uma amostra gravada de instrumento.
- `tests/pure_physical_audition_e28.test.mjs`: seis verificações de eventos/CC64, ausência de imports de amostras, saída finita e trabalho-energia passivo, render determinístico bit a bit, cabeçalho WAV/limite de nível e rejeição de eventos errados.

## Resultado CI
[GitHub Actions E2.8 — run 45220052292](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45220052292): **208/208 testes Node aprovados**; WAV gerado e armazenado no artefato `stage-e2-88-key-node-benchmark`, juntamente com `e28-physical-audition.json`. SHA256 de referência do PCM mono 16: `fafc514d7d858d77725bc65cf08852096c9534538af484918912ee658f056e1a`; 1.248.044 bytes. **Energias equilibradas** com erro relativo ~3,75e−14. 592 coordenadas de vibração de corda + dois modos de placa, 88 teclas permanentemente conectadas.
[Regressão Stage 45220051691](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45220051691): verde.

## Limites e próximos passos
1. O atual tampo de dois graus de liberdade e pesos de força/mobilidade **não são calibração física**. A E2.3 pode ainda soar arredondada e diferente de um piano acústico.
2. Para ser 100% físico **e soar convincente**, melhorar geometria de martelo/cordas e modelo estrutural de tampo/ponte com mobilidade complexa, amortecimento e dispersão derivados de medições/física; calcular propagação no ar por modelo acústico parametrizado, não por convolução de gravações.
3. Evidência de dados externos poderá **calibrar parâmetros**, mas nenhum WAV de referência deve entrar na voz, no arco de ataque ou na saída de radiação. Se direitos de medição não forem claros, não copiar dados ao projeto.
4. Antes de integrar ao motor D público, executar comparação auditiva sem efeitos, teste browser AudioWorklet e hardware 32 mínimo/64 meta, ressonância, CC64, dano/aliasing e regressão A/B/C/Clássico. Continuar sem afirmar fidelidade/performance até provar.
5. PR #37 continua draft; Stage D público v1.12.8, versão, FX/UI, histórico e padrões permanecem intocados; R-GATEs 0/7.

**Conclusão de produto:** o futuro piano do Stage Synth terá **som gerado somente por modelagem física**. E2.7 é apenas prova de que referências grabadas podem ter qualidade auditiva agradável, não uma arquitetura aprovada.
