"""Bibliothèque indépendante des copies : fichiers Markdown fournis, sans réécriture."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent.parent
DIRECTORY=ROOT/'Textes_philosophiques'
METADATA={
 'Comte - Cours de philosophie positive.md':('comte-cours-philosophie-positive','Auguste Comte','Cours de philosophie positive — 1re et 2e leçons','fr'),
 'Descartes - Discours de la méthode.md':('descartes-discours-methode','René Descartes','Discours de la méthode','fr'),
 'Descartes - Méditations métaphysiques.md':('descartes-meditations','René Descartes','Méditations métaphysiques','fr'),
 'Husserl Edmund - Die Krise (conference).md':('husserl-krisis','Edmund Husserl','Die Krisis des europäischen Menschentums und die Philosophie','de'),
 'Kritik der reinen Vernunft von Immanuel Kant.md':('kant-kritik-reinen-vernunft','Immanuel Kant','Kritik der reinen Vernunft — édition de 1787','de'),
 'Nietzsche - die-froehliche-wissenschaft.md':('nietzsche-frohliche-wissenschaft','Friedrich Nietzsche','Die fröhliche Wissenschaft','de'),
 'Pascal, De l_esprit géométrique.md':('pascal-esprit-geometrique','Blaise Pascal',"De l’esprit géométrique",'fr'),
}
def entries():
 result=[]
 for p in sorted(DIRECTORY.glob('*.md')):
  ident,author,title,language=METADATA.get(p.name,('texte-'+hashlib.sha256(p.name.encode()).hexdigest()[:16],'',p.stem,'und'))
  result.append(dict(id=ident,author=author,title=title,language=language,filename=p.name))
 return result

def document(ident):
 from corpus import MD,TAGS,plain
 import bleach
 entry=next(e for e in entries() if e['id']==ident)
 raw=(DIRECTORY/entry['filename']).read_text(encoding='utf-8-sig')
 # Le front matter décrit l’édition ; ce n’est pas un paragraphe de l’œuvre.
 body=re.sub(r'\A---\s*\n.*?\n---\s*\n','',raw,count=1,flags=re.S)
 tokens=MD.parse(body);toc=[]
 for i,t in enumerate(tokens):
  if t.type=='heading_open':
   anchor=f'work-section-{len(toc)}';t.attrSet('id',anchor)
   toc.append({'id':anchor,'title':plain(tokens[i+1].content).strip(),'level':int(t.tag[1:])})
 rendered=MD.renderer.render(tokens,MD.options,{})
 rendered=bleach.clean(rendered,tags=TAGS,attributes={'a':['href','title'],'*':['id'],'th':['align'],'td':['align']},protocols=['http','https','mailto'],strip=True)
 return dict(entry,text=raw,html=rendered,toc=toc,sha256=hashlib.sha256((DIRECTORY/entry['filename']).read_bytes()).hexdigest())
