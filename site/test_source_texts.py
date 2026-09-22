import json
import urllib.request
from pathlib import Path
import unittest
import source_texts
from corpus import Corpus

class SourceTextTests(unittest.TestCase):
    def test_manifest_and_links(self):
        c=Corpus();c.refresh();entries=source_texts.entries();ids=set();linked=set()
        for e in entries:
            self.assertNotIn(e['id'],ids);ids.add(e['id'])
            self.assertTrue(source_texts.local_path(e['source']['file']).is_file())
            d=source_texts.document(e);self.assertGreater(len(d['text']),120)
            self.assertNotIn('<script',d['html'])
            for ident in e['document_ids']:
                self.assertNotIn(ident,linked);linked.add(ident)
                self.assertEqual(c.docs[ident]['genre'],'commentaire')
                self.assertEqual(c.document(ident)['commented_text']['id'],e['id'])
        self.assertEqual(len(linked),25)
        self.assertEqual(sum(e.get('collection')=='anthologie' for e in entries),474)
        self.assertIsNone(source_texts.source_for('missing'))
    def test_footnotes_and_path_safety(self):
        t=source_texts.document(source_texts.get_source('condillac-animaux-2021'))
        self.assertEqual(t['line_count'],43)
        self.assertEqual(len(t['lines']),43)
        self.assertIn('class="pdf-line-number"',t['html'])
        self.assertNotIn('<script',t['html'])
        with self.assertRaises(ValueError):source_texts.local_path('../outside')

if __name__=='__main__':unittest.main()
