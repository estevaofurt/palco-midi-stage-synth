# Stage Concert Grand F10a results / F10b G4 spatial sensitivity — 24/11/2026

Base 25089223677780b8ddc12287d40e02ba544cb56e. Owner selected D in F9.20; model C remains reference and D C4 frozen. F10a [run 45486315236](https://github.com/estevaofurt/palco-midi-stage-synth/actions/runs/45486315236): 32/32 checks and all 9 render jobs succeeded; zero clipping, max energy balance error 6.869e-14 J, no positive energy increment reported. Data from CI logs (not local re-analysis of WAVs) persisted at audio/analysis_f10a_d_ci.json including all nine artifact/job IDs and spectral peaks.

| MIDI | touch | peak FS | RMS2 | wideOff .525–1.025 s |
|---|---|---:|---:|---:|
|55|24|.0295954|.00133418|.000627373|
|55|76|.344494|.01110775|.000418041|
|55|127|.910215|.03037450|.000369548|
|60|24|.0266500|.000574778|.000615519|
|60|76|.275111|.00879029|.000356730|
|60|127|.741493|.02493374|.000334309|
|67|24|.0195809|.000322044|.012339722|
|67|76|.270195|.00539306|.002612674|
|67|127|.764151|.01460672|.002666787|

RMS2 = 2–2.5 s; no long sustain inference. G4 off-band peak 367.67578125 Hz in all 3 dynamics, .025–.525 s at -2.27/-3.47/-3.62 dB relative to max bin. G4 nominal f1 391.9954 Hz; NOT proof of pitch failure, noise or modal cause. Strong G4 absolute wide-off power .525–1.025s is 3.05772e-6 FS² vs C4 D 1.83845e-6 (1.66×), despite lower RMS; inter-note comparison uses different harmonic masks. F10a reused same hypothetical bridge patch and plate for all notes. G3 ff peak .91 leaves little headroom for future chords; do not change gain in this diagnostic.

## F10b — restricted spatial sensitivity, not expansion to new registers
Decision: defer wider register expansion to diagnose G4 first. New module f10b-d-spatial.mjs wraps the original D register renderer for MIDI67 only. Fixed geometry, felt, velocity, damping, radiation, gain and spectral analysis. Three hypotheses: reference x=.83 m, minus8cm x=.75 m, plus8cm x=.91 m, y=.46 m, width .04 m, height .025 m; no measured bridge coordinates. Conjugate force/displacement weights recomputed through original BoardPort construction, not an EQ or notch. Record plate modal frequencies and coupling weights 340–440 Hz; no claim the peak is uniquely caused by one mode. Guard checkpoint variant. No changes to C4, G3, F10a, C/D original or main. F10b smoke requires exact G4 reference PCM/state, unchanged wire and damping, energy, same modal frequencies, valid positions and continuity. Six renders 3s at MIDI24/76/127, both shifted positions. Fixed gain clipping is a rejection gate, no normalization. Compare absolute off-band power, 367.7 Hz peak, RMS and attack against G4 F10a before choosing candidate; no adoption without evaluation. Workflow commit c03d6445da6cd309d9e8991afaec84d79d7932a8; execution not confirmed at this record. No 88-note expansion or 32–64 voice real-time claim.
