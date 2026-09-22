import re,unittest
from html.parser import HTMLParser
from unittest.mock import patch
from corpus import Corpus
from method_examples import EXAMPLES
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.summary=False
 def handle_starttag(self,tag,attrs):
  if tag=='summary':self.summary=True
 def handle_endtag(self,tag):
  if tag=='summary':self.summary=False
 def handle_data(self,data):
  if not self.summary:self.parts.append(data)
def content(html):
 p=Text();p.feed(html);return re.sub(r'\s+','',''.join(p.parts))
class ExamplesTests(unittest.TestCase):
 def test_examples_preserve_entire_resource(self):
  actual=Corpus().resource('methode')['html']
  with patch('method_examples.prepare_examples',side_effect=lambda text:(text,{})):
   original=Corpus().resource('methode')['html']
  self.assertEqual(content(actual),content(original))
  self.assertEqual(actual.count('<details class="method-example">'),len(EXAMPLES))
  self.assertNotIn('<details open',actual)
  self.assertNotIn('PHILOCORPUS_EXAMPLE',actual)
if __name__=='__main__':unittest.main()
