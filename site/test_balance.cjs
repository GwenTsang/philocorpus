const assert=require('node:assert/strict');
const {balanceStatistics}=require('./balance.js');
const copy=(parts,grade,conclusion=true)=>({parts,grade,conclusion_delimited:conclusion,warnings:[]});
const rows=[copy({partie_1:100,partie_2:100,partie_3:100},20),copy({partie_1:100,partie_2:200,partie_3:300},10,false),copy({partie_1:10,partie_2:10},15)];
let s=balanceStatistics(rows);assert.equal(s.n,2);assert.equal(s.excluded.parts,1);assert.equal(s.median,2/3);assert.equal(s.rows[1].part_ratio,1/3);assert.ok(Math.abs(s.rows[1].part_gap-100/3)<1e-10);assert.ok(Math.abs(s.meanShares[0]-0.25)<1e-10);assert.equal(s.correlation,null);
s=balanceStatistics(rows,true);assert.equal(s.n,1);assert.equal(s.excluded.conclusion,1);assert.equal(s.median,1);
s=balanceStatistics([copy({partie_1:100,partie_2:100,partie_3:100},20),copy({partie_1:50,partie_2:100,partie_3:100},10),copy({partie_1:25,partie_2:100,partie_3:100},5),copy({partie_1:50,partie_2:50,partie_3:50},null)]);assert.ok(Math.abs(s.correlation-1)<1e-10);assert.equal(s.n,4);assert.equal(s.rated.length,3);assert.equal(balanceStatistics([]).median,null);
console.log('OK proportions, médiane, corrélation, absence de note, deux parties et filtre conclusion.');
