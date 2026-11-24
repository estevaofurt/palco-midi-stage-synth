/** Exportador OFFLINE da prova modal V11B. Não é a renderização sonora C3X V10. */
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { RtMidiRing, EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PEDAL } from './rt-midi-ring.mjs';
import { ModalContinuityProbe } from './modal-continuity-probe.mjs';

export function renderDiagnosticWav({ destination, seconds = 5, sampleRate = 48000, block = 128 } = {}) {
  if (!destination) throw new TypeError('destino necessário');
  const frameCount = Math.round(seconds * sampleRate);
  if (frameCount % block !== 0) throw new RangeError('duração deve ser múltiplo do bloco');
  const q = new RtMidiRing({sampleRate, maxBlock:block});
  const synth = new ModalContinuityProbe({sampleRate});
  const events = [
    [0.00, EVENT_NOTE_ON, 60, 70], [0.38, EVENT_NOTE_OFF, 60, 0],
    [0.45, EVENT_NOTE_ON, 64, 95], [0.88, EVENT_NOTE_OFF, 64, 0],
    [0.95, EVENT_NOTE_ON, 67, 100], [1.25, EVENT_NOTE_OFF, 67, 0],
    [1.35, EVENT_PEDAL, 0, 127],
    [1.42, EVENT_NOTE_ON, 60, 80], [1.42, EVENT_NOTE_ON, 64, 90],
    [1.42, EVENT_NOTE_ON, 67, 92], [1.42, EVENT_NOTE_ON, 72, 110],
    [1.90, EVENT_NOTE_OFF, 60, 0], [1.90, EVENT_NOTE_OFF, 64, 0],
    [1.90, EVENT_NOTE_OFF, 67, 0], [1.90, EVENT_NOTE_OFF, 72, 0],
    [2.55, EVENT_NOTE_ON, 69, 65], [2.68, EVENT_NOTE_OFF, 69, 0],
    [2.75, EVENT_NOTE_ON, 69, 95], [2.88, EVENT_NOTE_OFF, 69, 0],
    [2.95, EVENT_NOTE_ON, 69, 115], [3.10, EVENT_NOTE_OFF, 69, 0],
    [3.40, EVENT_PEDAL, 0, 60], [3.90, EVENT_PEDAL, 0, 0],
  ];
  // Emissão offline, ordenação permitida antes de enfileirar.
  for (const [seconds, type, note, value] of events) q.enqueue({frame: Math.round(seconds*sampleRate), type, note, value});
  const stereo = new Float32Array(frameCount * 2);
  const l = new Float32Array(block), r = new Float32Array(block);
  let peak = 0;
  for(let b=0; b<frameCount; b+=block){
    q.processBlock(l,r,synth);
    for(let j=0;j<block;j++){
      const k=(b+j)*2;
      stereo[k]=l[j];stereo[k+1]=r[j];
      peak=Math.max(peak, Math.abs(l[j]), Math.abs(r[j]));
    }
  }
  // Normalização apenas para ouvir o demonstrador diagnóstico.
  const factor=peak>0?0.75/peak:1;
  const buffer = Buffer.alloc(44 + frameCount * 4);
  buffer.write('RIFF',0); buffer.writeUInt32LE(buffer.length-8,4);
  buffer.write('WAVEfmt ',8);buffer.writeUInt32LE(16,16);buffer.writeUInt16LE(1,20);
  buffer.writeUInt16LE(2,22);buffer.writeUInt32LE(sampleRate,24);
  buffer.writeUInt32LE(sampleRate*4,28);buffer.writeUInt16LE(4,32);
  buffer.writeUInt16LE(16,34);buffer.write('data',36);buffer.writeUInt32LE(frameCount*4,40);
  for(let i=0;i<stereo.length;i++){
    const v=Math.max(-1,Math.min(1,stereo[i]*factor));
    buffer.writeInt16LE(Math.round(v*32767),44+2*i);
  }
  writeFileSync(destination,buffer);
  return {destination,frames:frameCount,peakRaw:peak,strikes:synth.strikes};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log(renderDiagnosticWav({destination:process.argv[2]||'V11B_modal_probe_DIAGNOSTICO.wav'}));
}