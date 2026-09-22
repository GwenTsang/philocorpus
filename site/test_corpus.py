import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import corpus

class CorpusTests(unittest.TestCase):
    def test_segmentation_preserves_nested_coincident_markers_and_unicode(self):
        chunks=['😀 Introduction\n','Annonce générale\n','Premier argument <u>livre</u>\n','Deuxième argument\n']
        offsets=[];n=0
        for t in chunks:offsets.append(n);n+=len(t.encode('utf-16-le'))//2
        bs=[{'label':label,'offset':offset} for label,offset in zip(['Introduction','Annonce du plan','Partie 1','Partie 2'],offsets)]
        bs.append({'label':'Annonce thèse P1','offset':offsets[2]})
        sections,text,markers=corpus.sections_from_state({'text':''.join(chunks),'boundaries':bs})
        self.assertEqual(len(sections),4)
        self.assertEqual(sections[2]['text'],'Premier argument *livre*')
        self.assertEqual(sections[2]['markers'][0]['label'],'Annonce thèse P1')
        self.assertEqual(sections[-1]['key'],'partie_2')
        self.assertNotIn('conclusion',[s['key'] for s in sections])
        self.assertEqual(corpus.words(text),sum(corpus.words(s['text']) for s in sections))
    def test_scan_placeholder_does_not_hide_real_transcription(self):
        placeholder='# Copie\n*(Le PDF source est un scan sans texte extrait)*\n```json\n'+json.dumps({'ocr_status':'not_started','pages':[],'runs':[]})+'\n```'
        self.assertTrue(corpus.is_scan_placeholder(placeholder))
        self.assertFalse(corpus.is_scan_placeholder('Une dissertation sur le JSON.'))
        oldroot,olddb=corpus.ROOT,corpus.DB
        with tempfile.TemporaryDirectory() as tmp:
            corpus.ROOT=Path(tmp);corpus.DB=Path(tmp)/'missing.sqlite3'
            try:
                d=Path(tmp)/'COPIES_without_notes'/'Copie';d.mkdir(parents=True)
                (d/'metadata.json').write_text(json.dumps({'document_id':'scan','title':'Copie'}))
                (d/'scan-source.md').write_text(placeholder)
                c=corpus.Corpus();c.refresh()
                self.assertFalse(c.docs['scan']['has_text']);self.assertIsNone(c.docs['scan']['words'])
                self.assertEqual(c.docs['scan']['authors_status'],'unavailable')
                (d/'transcription.md').write_text('Texte véritable de la dissertation.')
                c.refresh();self.assertTrue(c.docs['scan']['has_text'])
                self.assertEqual(c.docs['scan']['text'],'Texte véritable de la dissertation.')
                self.assertEqual((d/'scan-source.md').read_text(),placeholder)
            finally:corpus.ROOT,corpus.DB=oldroot,olddb

    def test_safe_html_and_word_definition(self):
        self.assertEqual(corpus.words("L'État *juste* et soi-même."),4)
        out=corpus.render('<img src=x onerror=alert(1)><script>alert(1)</script>[x](javascript:alert(1))')
        self.assertNotIn('<script',out);self.assertNotIn('onerror',out);self.assertNotIn('href="javascript:',out)
    def test_live_latest_gold_and_original_json(self):
        oldroot,olddb=corpus.ROOT,corpus.DB
        with tempfile.TemporaryDirectory() as tmp:
            corpus.ROOT=Path(tmp);corpus.DB=Path(tmp)/'reviews.sqlite3'
            try:
                root=Path(tmp)/'COPIES_with_notes';root.mkdir();(Path(tmp)/'COPIES_without_notes').mkdir()
                for ident in ['annotated','reference','other']:
                    d=root/ident;d.mkdir();(d/'metadata.json').write_text(json.dumps({'document_id':ident,'title':ident,'grade':0,'exam':'ENA interne','year':2022}))
                    (d/'text.md').write_text('Texte OCR ancien')
                d=root/'reference'/'transcriptions_json';d.mkdir();(d/'clean.json').write_text(json.dumps({'introduction':'Texte de référence','partie_1':'Premier','partie_2':'Second'}))
                c=sqlite3.connect(corpus.DB);c.execute('CREATE TABLE revisions(id INTEGER PRIMARY KEY,document TEXT,variant TEXT,saved_at TEXT,payload TEXT)')
                state={'text':'Introduction\nPremier\nSecond','boundaries':[{'label':l,'offset':o} for l,o in [('Introduction',0),('Partie 1',13),('Partie 2',21)]]}
                c.execute('INSERT INTO revisions VALUES(1,?,?,?,?)',('annotated','text.md','today',json.dumps(state)));c.commit()
                obj=corpus.Corpus();listing=obj.listing();self.assertEqual(len(listing),3);self.assertEqual(sum(d['gold'] for d in listing),2)
                self.assertEqual(obj.docs['annotated']['grade'],0);self.assertEqual(obj.docs['annotated']['revision'],1)
                self.assertEqual(obj.docs['annotated']['parts'],{'partie_1':1,'partie_2':1});self.assertIsNone(obj.docs['annotated']['balance'])
                state['text']+=' corrigé'
                c.execute('INSERT INTO revisions VALUES(2,?,?,?,?)',('annotated','text.md','later',json.dumps(state)));c.commit();obj.refresh()
                self.assertEqual(obj.docs['annotated']['revision'],2);self.assertTrue(obj.docs['annotated']['text'].endswith('corrigé'))
                self.assertEqual((root/'annotated'/'text.md').read_text(),'Texte OCR ancien');c.close()
            finally:corpus.ROOT,corpus.DB=oldroot,olddb

if __name__=='__main__':unittest.main()
