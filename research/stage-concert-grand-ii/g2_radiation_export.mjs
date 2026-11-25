// Export original mass-normalized transverse mode shapes for independent radiation tests.
import {buildBoard} from './g2_board_pilot.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const b=buildBoard('control',6000),modes=b.modes.filter(m=>m.frequencyHz<6000);
const selected=[modes[0],...[100,260,500,1046,2000,4000,5800].map(f=>modes.reduce((a,m)=>Math.abs(m.frequencyHz-f)<Math.abs(a.frequencyHz-f)?m:a))];
const exportMode=m=>({id:'mode-'+modes.indexOf(m),frequencyHz:m.frequencyHz,components:m.components.map(c=>({m:c.m,n:c.n,kx:c.kx,ky:c.ky,coefficient:c.coefficient}))});
mkdirSync('/tmp/g2-radiation',{recursive:true});writeFileSync('/tmp/g2-radiation/shapes.json',JSON.stringify({L:b.p.lengthM,W:b.p.widthM,selected:selected.map(exportMode)}));
