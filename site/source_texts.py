"""Textes commentés et liens explicites vers les copies, sans modifier les transcriptions."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
MANIFEST=ROOT/'Textes_commentaires_de_textes'/'catalogue.json'

def entries():
    result=json.loads(MANIFEST.read_text())['texts'] if MANIFEST.exists() else []
    anthology=MANIFEST.with_name('anthologie.json')
    if anthology.exists():result+=json.loads(anthology.read_text())['texts']
    return result

def source_for(document_id):
    return next((e for e in entries() if document_id in e.get('document_ids',[])),None)

def get_source(ident):
    return next(e for e in entries() if e['id']==ident)

def local_path(relative):
    path=(ROOT/relative).resolve()
    if not path.is_relative_to(ROOT):raise ValueError('Chemin de source invalide')
    return path

def summary(entry):
    return {k:entry.get(k) for k in ('id','title','reference','document_ids','note','collection')}

def document(entry):
    from corpus import render
    import re
    text=local_path(entry['markdown']).read_text()
    # Un titre est déjà affiché par l’interface.
    body=re.sub(r'^# [^\n]+\n+','',text,count=1)
    line_data=None
    if entry.get('lines_file'):
        from html import escape
        import hashlib
        line_data=json.loads(local_path(entry['lines_file']).read_text())
        expected=entry['source']['sha256']
        if hashlib.sha256(local_path(entry['source']['file']).read_bytes()).hexdigest()!=expected:
            raise ValueError('Le PDF source a changé : extraction à refaire')
        def row(line,numbered):
            number=f'<span class="pdf-line-number" aria-hidden="true">{line["number"]}</span>' if numbered else ''
            return f'<div class="pdf-line">{number}<span class="pdf-line-text">{escape(line["text"])}</span></div>'
        html='<div class="pdf-lines" tabindex="0" role="region" aria-label="Texte numéroté, lignes du PDF conservées">'+''.join(row(l,True) for l in line_data['lines'])+'</div>'
        if line_data['supplement']:
            html+='<div class="pdf-supplement"><div class="pdf-lines" tabindex="0" role="region" aria-label="Référence et notes du PDF">'+''.join(row(l,False) for l in line_data['supplement'])+'</div></div>'
    else:html=render(body)
    html=re.sub(r'(id|href)="(#?)(fn[^"]*)"',lambda m:f'{m[1]}="{m[2]}source-{entry["id"]}-{m[3]}"',html)
    return dict(summary(entry),line_count=len(line_data['lines']) if line_data else None,lines=line_data['lines'] if line_data else None,text=text,html=html,source=entry['source'],has_pdf=entry['source']['file'].lower().endswith('.pdf'))
