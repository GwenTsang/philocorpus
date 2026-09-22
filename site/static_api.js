/* API de lecture de l’instantané publié, sans serveur ni PDF. */
window.staticApi=async function(path){
 const url=new URL(path,location.origin),id=url.searchParams.get('id');
 async function get(file){const r=await fetch('/data/'+file,{cache:'no-cache'});if(!r.ok)throw Error('La ressource n’a pas pu être chargée.');return r.json();}
 const routes={'/api/catalog':'catalog.json','/api/source-texts':'sources.json','/api/document':'documents/'+encodeURIComponent(id)+'.json','/api/resource':'resources/'+encodeURIComponent(id)+'.json','/api/source-text':'sources/'+encodeURIComponent(id)+'.json'};
 if(routes[url.pathname])return get(routes[url.pathname]);
 if(url.pathname==='/api/scan')return {pages:0};
 if(url.pathname==='/api/search'){
  const fold=s=>s.normalize('NFD').replace(/\p{M}/gu,'').toLowerCase();
  const q=fold(url.searchParams.get('q')||''),section=url.searchParams.get('section');if(!q)return [];
  const index=await (window.staticSearchIndex??=get('search.json').catch(e=>{window.staticSearchIndex=null;throw e;}));
  return index.flatMap(d=>{const text=section?(d.sections[section]||''):d.text,i=fold(text).indexOf(q);if(i<0&&(section||!fold(d.title).includes(q)))return [];const start=Math.max(0,i-90);return [{id:d.id,snippet:(start?'…':'')+text.slice(start,start+260).trim()+'…'}];});
 }
 throw Error('Ressource indisponible dans cette édition sans PDF.');
};
