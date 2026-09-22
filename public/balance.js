/* Mesures descriptives : P1, P2, P3 uniquement ; une observation par copie. */
function balanceStatistics(copies, isolatedConclusion=false) {
  const excluded={parts:0,review:0,conclusion:0};
  const rows=[];
  for(const c of copies){
    const p=['partie_1','partie_2','partie_3'].map(k=>c.parts?.[k]);
    if(p.some(n=>!Number.isFinite(n)||n<=0)){excluded.parts++;continue;}
    if(c.warnings?.length){excluded.review++;continue;}
    if(isolatedConclusion&&!c.conclusion_delimited){excluded.conclusion++;continue;}
    const total=p.reduce((a,b)=>a+b,0),shares=p.map(n=>n/total);
    rows.push({...c,part_words:p,part_shares:shares,part_total:total,part_ratio:Math.min(...p)/Math.max(...p),part_gap:100*(Math.max(...shares)-Math.min(...shares))});
  }
  const n=rows.length,ratios=rows.map(c=>c.part_ratio).sort((a,b)=>a-b);
  const meanShares=n?[0,1,2].map(i=>rows.reduce((sum,c)=>sum+c.part_shares[i],0)/n):null;
  const median=n?(ratios[Math.floor((n-1)/2)]+ratios[Math.floor(n/2)])/2:null;
  const rated=rows.filter(c=>Number.isFinite(c.grade));
  let correlation=null;
  if(rated.length>=3){
    const mx=rated.reduce((s,c)=>s+c.part_ratio,0)/rated.length,my=rated.reduce((s,c)=>s+c.grade,0)/rated.length;
    const xx=rated.reduce((s,c)=>s+(c.part_ratio-mx)**2,0),yy=rated.reduce((s,c)=>s+(c.grade-my)**2,0);
    if(xx&&yy)correlation=rated.reduce((s,c)=>s+(c.part_ratio-mx)*(c.grade-my),0)/Math.sqrt(xx*yy);
  }
  return {rows,rated,excluded,n,meanShares,median,correlation,withoutConclusion:rows.filter(c=>!c.conclusion_delimited).length};
}
if(typeof module!=='undefined')module.exports={balanceStatistics};
