#!/usr/bin/env python3
"""Site local PhiloCorpus, en lecture seule. Port distinct de l’atelier."""
import argparse
import source_texts
import philosophical_texts
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import urlparse,parse_qs
import pymupdf
from corpus import Corpus, ROOT, resource_specs, fold, plain, illustration_path

HERE=Path(__file__).resolve().parent
corpus=Corpus();lock=RLock()
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,data,mime='application/json; charset=utf-8',status=200):
        body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        try:
            with lock:self.route()
        except (KeyError,StopIteration,IndexError,ValueError):self.send({'error':'Document ou page introuvable.'},status=404)
        except BrokenPipeError:pass
        except Exception as e:
            print(type(e).__name__,str(e),flush=True);self.send({'error':'Impossible de lire cette ressource.'},status=500)
    def route(self):
        u=urlparse(self.path);q=parse_qs(u.query)
        if u.path=='/fonts/EBGaramond-Regular.woff':
            return self.send((HERE/'fonts'/'EBGaramond-Regular.woff').read_bytes(),'font/woff')
        if u.path in ('/','/app.js','/style.css','/balance.js','/references.js'):
            name={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/balance.js':'balance.js','/references.js':'references.js'}[u.path]
            mime={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8','/balance.js':'text/javascript; charset=utf-8','/references.js':'text/javascript; charset=utf-8'}[u.path]
            return self.send((HERE/name).read_bytes(),mime)
        if u.path=='/api/philosophical-texts':return self.send(philosophical_texts.entries())
        if u.path=='/api/philosophical-text':return self.send(philosophical_texts.document(q['id'][0]))
        if u.path=='/api/source-texts':return self.send([source_texts.summary(e) for e in source_texts.entries()])
        if u.path=='/api/source-text':return self.send(source_texts.document(source_texts.get_source(q['id'][0])))
        if u.path=='/api/source-pdf':
            entry=source_texts.get_source(q['id'][0]);path=source_texts.local_path(entry['source']['file'])
            if path.suffix.lower()!='.pdf':raise KeyError('pdf')
            return self.send(path.read_bytes(),'application/pdf')
        if u.path=='/api/catalog':
            docs=corpus.listing();return self.send({'copies':docs,'resources':corpus.resources(),'revision':corpus.stamp[0]})
        if u.path=='/api/resource':return self.send(corpus.resource(q['id'][0]))
        corpus.refresh()
        if u.path.startswith('/copy-assets/'):
            _,_,ident,name=u.path.split('/')
            d=corpus.docs[ident]
            if name!='schema.svg':raise KeyError('illustration')
            path=illustration_path(d['directory'],d['illustrations']['schema'])
            return self.send(path.read_bytes(),'image/svg+xml')
        if u.path=='/api/search':
            query=fold(q.get('q',[''])[0]);section=q.get('section',[''])[0];hits=[]
            if not query:return self.send([])
            for d in corpus.docs.values():
                text='\n\n'.join(s['text'] for s in d['sections'] if s['key']==section) if section else d['text']
                t=plain(text);index=fold(t).find(query)
                if index>=0 or (not section and query in fold(d['title'])):
                    start=max(0,index-90);hits.append({'id':d['id'],'snippet':('…' if start else '')+t[start:start+260].strip()+'…'})
            return self.send(hits)
        if u.path=='/api/document':return self.send(corpus.document(q['id'][0]))
        if u.path=='/api/pdf':
            p=corpus.docs[q['id'][0]]['pdf']
            if not p:raise KeyError('pdf')
            return self.send(p.read_bytes(),'application/pdf')
        if u.path=='/api/scan':
            d=corpus.docs[q['id'][0]]
            if not d['pdf']:return self.send({'pages':0})
            with pymupdf.open(d['pdf']) as pdf:
                if 'page' not in q:return self.send({'pages':len(pdf)})
                n=int(q['page'][0]);assert n>=1
                return self.send(pdf[n-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).tobytes('png'),'image/png')
        self.send({'error':'Introuvable'},status=404)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8745);args=parser.parse_args()
    corpus.refresh();print(f'PhiloCorpus — http://127.0.0.1:{args.port} — {len(corpus.docs)} copies',flush=True)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
