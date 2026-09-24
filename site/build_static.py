#!/usr/bin/env python3
"""Exporte uniquement les données de lecture dans un dossier publiable sans PDF."""
import base64,gzip,json,shutil
from datetime import datetime,timezone
from pathlib import Path
from corpus import Corpus,plain,illustration_path
import source_texts
import philosophical_texts
HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'deployment'/'vercel'
PUBLIC=OUT/'public'
def dump(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if PUBLIC.exists():shutil.rmtree(PUBLIC)
 PUBLIC.mkdir()
 for name in ['index.html','app.js','style.css','balance.js','references.js','static_api.js']:
  shutil.copy2(HERE/name,PUBLIC/name)
 shutil.copytree(HERE/'fonts',PUBLIC/'fonts')
 index=(PUBLIC/'index.html').read_text().replace('<script src="/balance.js">','<script src="/static_api.js"></script><script src="/balance.js">')
 (PUBLIC/'index.html').write_text(index)
 app=(PUBLIC/'app.js').read_text().replace('async function api(path){','async function api(path){if(window.staticApi)return window.staticApi(path);')
 app=app.replace('Aucune transcription disponible. Consultez le manuscrit.','Cette copie ne dispose pas encore d’une transcription. Les scans ne sont pas inclus dans cette édition en ligne.')
 app=app.replace("c.has_scan?'Manuscrit disponible':'Texte seul'","c.has_scan?'Manuscrit disponible':c.has_text?'Texte disponible':'Transcription à venir'")
 app=app.replace('Le bouton « Actualiser les copies » recharge les annotations enregistrées dans l’atelier.','Cette édition en ligne est un instantané du corpus, sans PDF. Les corrections de l’atelier local sont intégrées lors de la prochaine publication. Le bouton « Actualiser les copies » recharge la version publiée.')
 (PUBLIC/'app.js').write_text(app)
 corpus=Corpus();corpus.refresh();catalog=corpus.listing();search=[]
 for c in catalog:
  c['has_scan']=False
  d=corpus.document(c['id']);d['has_scan']=False
  for key,relative in d.get('illustrations',{}).items():
   if key!='schema':continue
   asset=PUBLIC/'copy-assets'/c['id']/'schema.svg'
   asset.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(illustration_path(corpus.docs[c['id']]['directory'],relative),asset)
  if d.get('commented_text'):d['commented_text']['has_pdf']=False
  dump(PUBLIC/'data'/'documents'/(c['id']+'.json'),d)
  search.append({'id':d['id'],'title':d['title'],'text':plain(d['text']),'sections':{s['key']:plain(s['text']) for s in d['sections']}})
 stamp=datetime.now(timezone.utc).isoformat()
 dump(PUBLIC/'data'/'catalog.json',{'copies':catalog,'resources':corpus.resources(),'revision':stamp})
 dump(PUBLIC/'data'/'search.json',search)
 for r in corpus.resources():dump(PUBLIC/'data'/'resources'/(r['id']+'.json'),corpus.resource(r['id']))
 entries=source_texts.entries();dump(PUBLIC/'data'/'sources.json',[source_texts.summary(e) for e in entries])
 for entry in entries:
  d=source_texts.document(entry);d['has_pdf']=False
  dump(PUBLIC/'data'/'sources'/(entry['id']+'.json'),d)
 works=philosophical_texts.entries();dump(PUBLIC/'data'/'works.json',works)
 for entry in works:dump(PUBLIC/'data'/'works'/(entry['id']+'.json'),philosophical_texts.document(entry['id']))
 files={str(p.relative_to(PUBLIC)):({'base64':base64.b64encode(p.read_bytes()).decode()} if p.suffix=='.woff' else p.read_text()) for p in sorted(PUBLIC.rglob('*')) if p.is_file()}
 assert not any(Path(n).suffix in ['.pdf','.sqlite3','.py'] for n in files)
 bundle=gzip.compress(json.dumps(files,separators=(',',':')).encode(),mtime=0)
 
 for old in OUT.glob('snapshot.*'):old.unlink()
 for i,start in enumerate(range(0,len(bundle),200000)):(OUT/f'snapshot.{i:04d}').write_bytes(bundle[start:start+200000])
 shutil.copy2(HERE/'unpack_snapshot.cjs',OUT/'build.cjs')
 dump(OUT/'vercel.json',{'$schema':'https://openapi.vercel.sh/vercel.json','framework':None,'buildCommand':'node build.cjs','installCommand':'','outputDirectory':'public','headers':[{'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'}]}]})
 (OUT/'.vercelignore').write_text('public\n')
 report={'built_at':stamp,'copies':len(catalog),'source_texts':len(entries),'philosophical_texts':len(works),'files':len(files),'public_bytes':sum(p.stat().st_size for p in PUBLIC.rglob('*') if p.is_file()),'compressed_bytes':len(bundle),'pdfs':0}
 dump(OUT.parent/'build-report.json',report);print(json.dumps(report))
if __name__=='__main__':main()
