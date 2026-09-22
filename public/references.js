/* Une observation par dissertation ; zéro mention reste une valeur observée. */
function referenceStatistics(copies, metric='mentions') {
  const excluded={grade:0,annotations:0,text:0,review:0},rows=[];
  for(const c of copies){
    if(!c.dissertation)continue;
    if(!Number.isFinite(c.grade)||c.grade<0||c.grade>20){excluded.grade++;continue;}
    if(c.authors_status!=='current'){excluded.annotations++;continue;}
    if(!c.has_text||!Number.isFinite(c.words)||c.words<=0){excluded.text++;continue;}
    if(c.warnings?.length){excluded.review++;continue;}
    const mentions=c.authors.reduce((sum,a)=>sum+a.count,0);
    const distinct=new Set(c.authors.map(a=>a.id)).size;
    const density=1000*mentions/c.words;
    rows.push({...c,mentions,distinct,density,x:metric==='distinct'?distinct:metric==='density'?density:mentions});
  }
  let correlation=null;
  if(rows.length>=3){
    const mx=rows.reduce((s,c)=>s+c.x,0)/rows.length,my=rows.reduce((s,c)=>s+c.grade,0)/rows.length;
    let xx=0,yy=0,xy=0;
    for(const c of rows){const dx=c.x-mx,dy=c.grade-my;xx+=dx*dx;yy+=dy*dy;xy+=dx*dy;}
    if(xx>0&&yy>0)correlation=Math.max(-1,Math.min(1,xy/Math.sqrt(xx*yy)));
  }
  return {rows,excluded,correlation};
}
if(typeof module!=='undefined')module.exports={referenceStatistics};
