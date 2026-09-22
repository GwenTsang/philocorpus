"""Lecture seule du corpus, des références JSON et des annotations humaines."""
from pathlib import Path
import hashlib
import html
import json
import re
import sqlite3
import sys
import unicodedata
from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
import bleach
import source_texts

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'viewer'/'atelier'))
from export_structured import clean, clean_section, utf16_positions
DB=ROOT/'viewer'/'atelier'/'data'/'reviews.sqlite3'
FIELDS={'introduction':'Introduction','annonce_du_plan':'Annonce du plan','partie_1':'Partie 1','transition_1':'Transition 1','partie_2':'Partie 2','transition_2':'Transition 2','partie_3':'Partie 3','conclusion':'Conclusion'}
PRIMARY=set(FIELDS.values())
RESOURCES=[
 ('methode','Méthodologie de la dissertation','Du sujet à la conclusion : construire une argumentation.','Methodologie de la dissertation (Licence, Capes, Agreg).md'),
 ('plans','Penser le plan','Dialectique, approfondissement et articulation des thèses.','Methodologie - remarques théoriques sur les PLANS.md'),
 ('anthologie','Anthologie d’introductions','Observer différentes façons de faire émerger un problème.','Anthologie de dissertations de philosophie.md'),
 ('tableaux','Arguments & contre-arguments','Mettre les références à l’épreuve des difficultés.','Dissertations_en_tableaux.md'),
]
def resource_specs():
    manifest=Path(__file__).with_name('resources.json')
    entries=json.loads(manifest.read_text())
    result=[];seen=set()
    for entry in entries:
        path=(ROOT/entry['file']).resolve()
        if not path.is_relative_to(ROOT.resolve()) or entry['id'] in seen:
            raise ValueError('Ressource invalide ou identifiant dupliqué')
        seen.add(entry['id'])
        result.append((entry['id'],entry['title'],entry.get('description',''),entry['file']))
    return result

MD=MarkdownIt('commonmark',{'html':True}).enable('table').use(footnote_plugin)
TAGS=set(bleach.sanitizer.ALLOWED_TAGS)|{'p','h1','h2','h3','h4','h5','h6','hr','br','table','thead','tbody','tr','td','th','sup','sub','span','div','u','s','del','section'}

def plain(text):
    return html.unescape(bleach.clean(MD.render(text),tags=[],strip=True))

def words(text):
    return len(re.findall(r"[^\W_]+(?:[’'\-][^\W_]+)*",plain(text),re.UNICODE))

def render(text):
    return bleach.clean(MD.render(text),tags=TAGS,attributes={'a':['href','title'],'*':['id'],'th':['align'],'td':['align']},protocols=['http','https','mailto'],strip=True)

def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if not unicodedata.combining(c))

def sections_from_state(state):
    text=state['text'];positions=utf16_positions(text)
    boundaries=sorted(state.get('boundaries',[]),key=lambda b:b['offset'])
    valid=[b for b in boundaries if b.get('offset') in positions]
    if len(valid)!=len(boundaries):raise ValueError('Repère invalide')
    # Les repères personnalisés ne tronquent pas les grandes parties.
    main=[b for b in valid if b['label'] in PRIMARY]
    result=[]
    for i,b in enumerate(main):
        end=next((x['offset'] for x in main[i+1:] if x['offset']>b['offset']),max(positions))
        raw=text[positions[b['offset']]:positions[end]]
        result.append({'label':b['label'],'key':next(k for k,v in FIELDS.items() if v==b['label']), 'text':clean_section(raw),'offset':b['offset'],'end_offset':end,'scan_page':b.get('scan_page'),
                       'markers':[x for x in valid if x['label'] not in PRIMARY and b['offset']<=x['offset']<end]})
    # Préserver l’intégralité du texte de la copie même lorsque seul un plan atypique existe.
    start=min((b['offset'] for b in main),default=0)
    return result,'\n\n'.join(s['text'] for s in result) if result else clean(text[positions[start]:]),valid

def load_authors(item):
    item.update(authors=[], author_mentions=[], authors_status='unavailable')
    if not item['dissertation']:return
    path=item['directory']/'annotations_references'/'automatic_authors.json'
    if not path.exists():return
    try:
        data=json.loads(path.read_text())
        if data['document_id']!=item['id'] or data['source']['text_sha256']!=hashlib.sha256(item['text'].encode()).hexdigest():
            item['authors_status']='stale';return
        units={u['id']:u for u in data['units']};authors={};mentions=[]
        for ref in data['references']:
            unit=units[ref['unit_id']]
            if unit['text'][ref['start']:ref['end']]!=ref['quote']:raise ValueError('Invalid reference')
            key=ref['entity_id']
            author=authors.setdefault(key,{'id':key,'name':ref['canonical_label'],'category':ref.get('category','philosophique'),'count':0})
            author['count']+=1
            mentions.append({'author_id':key,'quote':ref['quote'],'left':ref['left'],'right':ref['right'],'section':unit['section'],'label':unit['label']})
        item.update(authors=sorted(authors.values(),key=lambda a:(-a['count'],a['name'])),author_mentions=mentions,authors_status='current')
    except (ValueError,KeyError,TypeError):item['authors_status']='invalid'

class Corpus:
    def __init__(self): self.stamp=None;self.docs={};self.resource_cache={}
    def refresh(self):
        metas=sorted(p for base in ('COPIES_with_notes','COPIES_without_notes') for p in (ROOT/base).glob('*/metadata.json') if not p.parent.name.startswith(('_','.')))
        reference_files=[p.parent/'annotations_references'/'automatic_authors.json' for p in metas]
        source_files=sorted({f for p in metas for pattern in ('*.md','*.json','transcriptions_md/*.md','transcriptions_json/*.json') for f in p.parent.glob(pattern)})
        source_stamp=tuple((str(p),p.stat().st_mtime_ns) for p in source_files)
        reference_stamp=tuple((str(p),p.stat().st_mtime_ns) for p in reference_files if p.exists())
        stamp=(DB.stat().st_mtime_ns if DB.exists() else 0,tuple((str(p),p.stat().st_mtime_ns) for p in metas),reference_stamp,source_stamp)
        if self.stamp==stamp:return
        annotations={}
        if DB.exists():
            with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as c:
                for rid,doc,variant,saved,payload in c.execute('SELECT id,document,variant,saved_at,payload FROM revisions WHERE id IN (SELECT MAX(id) FROM revisions GROUP BY document,variant) ORDER BY id DESC'):
                    state=json.loads(payload)
                    if state.get('boundaries'):annotations.setdefault(doc,[]).append((rid,variant,saved,state))
        docs={}
        for mp in metas:
            meta=json.loads(mp.read_text());d=mp.parent;ident=meta['document_id']
            item={'id':ident,'title':meta['title'],'exam':meta.get('exam'),'year':meta.get('year'),'grade':meta.get('grade'),'kind':meta.get('type_epreuve'),'context':meta.get('context'),'collection':d.parent.name,'gold':False,'source_kind':'scan','source_label':'Scan seul','sections':[],'text':'','revision':None,'saved_at':None,'warnings':[],'directory':d,'statistics':meta.get('exam_statistics'), 'boundaries':[]}
            is_commentary=any(w in d.name.casefold() for w in ('commentaire','explication'))
            item['genre']=meta.get('genre') or ('commentaire' if is_commentary else 'dissertation')
            is_dissertation=item['genre']=='dissertation'
            item['dissertation']=is_dissertation
            authoritative=[p for p in (d/'transcriptions_json').glob('*.json') if not p.name.startswith('atelier__')]
            authoritative += [p for p in d.glob('*.json') if p!=mp and isinstance((obj:=json.loads(p.read_text())),dict) and 'introduction' in obj]
            if authoritative:
                f=sorted(authoritative)[0];data=json.loads(f.read_text())
                sections=[{'key':k,'label':label,'text':clean_section(data[k]),'markers':[],'scan_page':None} for k,label in FIELDS.items() if isinstance(data.get(k),str) and data[k].strip()]
                item.update(gold=True,source_kind='authoritative_json',source_label='JSON de référence',source_file=str(f.relative_to(d)),sections=sections,text='\n\n'.join(s['text'] for s in sections))
            elif annotations.get(ident):
                rid,variant,saved,state=annotations[ident][0]
                try:
                    sections,text,boundaries=sections_from_state(state)
                    item.update(gold=True,source_kind='human_annotation',source_label='Annotation humaine',source_file=variant,sections=sections,text=text,revision=rid,saved_at=saved,boundaries=boundaries,source_text_sha256=hashlib.sha256(state['text'].encode()).hexdigest(),annotation_offset_unit='utf16',annotation_offsets_reference='Texte original de la révision atelier, avant nettoyage')
                    if any(b.get('needs_review') for b in boundaries):item['warnings'].append('Certaines limites sont à revérifier après une correction du texte.')
                    if not all(x in [s['key'] for s in sections] for x in ('introduction','partie_1','partie_2')):item['warnings'].append('La structure principale est partiellement délimitée.')
                except ValueError:item['warnings'].append('Positions d’annotation invalides : transcription source affichée.')
            if not item['text']:
                variants=sorted(set(d.glob('*.md'))|set((d/'transcriptions_md').glob('*.md')))
                variants=[p for p in variants if p.name.lower()!='readme.md']
                reference=d/(meta.get('reference_transcription') or '_')
                variants.sort(key=lambda p:(p!=reference,'<span' in p.read_text(encoding='utf-8-sig'),str(p)))
                if variants:
                    f=variants[0];item.update(text=clean(f.read_text(encoding='utf-8-sig')),source_kind='transcription',source_label='Transcription à vérifier',source_file=str(f.relative_to(d)))
            pdf=d/(meta.get('source_pdf') or '_');pdfs=sorted(d.glob('*.pdf'))
            item['pdf']=pdf if pdf.is_file() else (pdfs[0] if pdfs else None)
            item['has_scan']=bool(item['pdf']);item['has_text']=bool(item['text'])
            item['words']=words(item['text']) if item['text'] else None
            for section in item['sections']:section['words']=words(section['text'])
            part_sections=[s for s in item['sections'] if re.fullmatch('partie_[123]',s['key'])]
            item['parts']={s['key']:s['words'] for s in part_sections}
            # Une conclusion non délimitée peut être absente ou intégrée : ne pas assimiler les deux.
            item['conclusion_delimited']=any(s['key']=='conclusion' for s in item['sections'])
            item['balance']=min(item['parts'].values())/max(item['parts'].values()) if len(item['parts'])>=2 and max(item['parts'].values()) and item['conclusion_delimited'] and not item['warnings'] else None
            item['search']=fold(item['title']+' '+item['text'])
            load_authors(item)
            docs[ident]=item
        self.docs=docs;self.stamp=stamp
    def listing(self):
        self.refresh()
        excluded={'text','sections','directory','pdf','search','boundaries','author_mentions'}
        return [{k:v for k,v in d.items() if k not in excluded} for d in self.docs.values()]
    def document(self,ident):
        self.refresh();d=self.docs[ident]
        result={k:v for k,v in d.items() if k not in ('directory','pdf','search')}
        entry=source_texts.source_for(ident) if d['genre']=='commentaire' else None
        result['commented_text']=source_texts.document(entry) if entry else None
        result['html']=render(d['text'])
        result['sections']=[dict(s,html=render(s['text'])) for s in d['sections']]
        return result
    def resources(self):return [{'id':i,'title':t,'description':desc} for i,t,desc,_ in resource_specs()]
    def resource(self,ident):
        i,title,desc,name=next(r for r in resource_specs() if r[0]==ident)
        p=ROOT/name;stamp=p.stat().st_mtime_ns
        if (ident,stamp) in self.resource_cache:return self.resource_cache[ident,stamp]
        raw=p.read_text();text=re.sub(r'(?m)^\s*(?:&nbsp;\s*)+$','',raw)
        text=re.sub(r'\n{3,}','\n\n',text)
        if ident=='methode':
            first=text.find('## **1.1.');text=text[first:] if first>=0 else text
        if ident in ('plans','tableaux'):
            text=re.sub(r'(?m)^\*\*([^\n]+)\*\*\s*$',r'## \1',text)
        text=re.sub(r'(?m)^#{1,6}\s*(?:&nbsp;)?\s*$','',text)
        tokens=MD.parse(text);toc=[];n=0
        for index,token in enumerate(tokens):
            if token.type=='heading_open':
                inline=tokens[index+1];match=re.search(r'\s*\{#([^}]+)\}\s*$',inline.content)
                anchor=match.group(1) if match else f'section-{n}'
                inline.content=re.sub(r'\s*\{#[^}]+\}\s*$','',inline.content)
                inline.children=MD.parseInline(inline.content)[0].children
                token.attrSet('id',anchor);toc.append({'id':anchor,'title':plain(inline.content).strip(),'level':int(token.tag[1])});n+=1
        rendered=bleach.clean(MD.renderer.render(tokens,MD.options,{}),tags=TAGS,attributes={'a':['href','title'],'*':['id'],'th':['align'],'td':['align']},protocols=['http','https','mailto'],strip=True)
        result={'id':ident,'title':title,'description':desc,'html':rendered,'toc':toc,'filename':name}
        self.resource_cache[ident,stamp]=result;return result
