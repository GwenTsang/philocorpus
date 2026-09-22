"""Fidélité des sept textes publiés, navigation, sommaires, notes et mobile."""
import hashlib,json,os,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=os.environ.get('PHILOCORPUS_SITE_URL','http://127.0.0.1:8746')
works=json.load(urllib.request.urlopen(BASE+'/data/works.json'))
assert len(works)==len(list(Path('Textes_philosophiques').glob('*.md')))
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE+'/#textes-philosophiques');page.wait_for_selector('#workResults a')
 assert page.locator('#workResults a').count()==len(works)
 assert page.locator('header nav [aria-current="page"]').inner_text()=='Textes Philosophiques'
 page.fill('#workSearch','Descartes');assert page.locator('#workResults a').count()==2
 page.fill('#workSearch','');page.select_option('#workLanguage','de');assert page.locator('#workResults a').count()==3
 for w in works:
  d=json.load(urllib.request.urlopen(BASE+'/data/works/'+w['id']+'.json'));src=Path('Textes_philosophiques')/w['filename']
  assert d['text']==src.read_text(encoding='utf-8-sig')
  assert d['sha256']==hashlib.sha256(src.read_bytes()).hexdigest()
  page.goto(BASE+'/#oeuvre/'+w['id']);page.wait_for_selector('.work-prose')
  assert page.locator('.work-prose').get_attribute('lang')==w['language']
  assert page.locator('.work-prose').evaluate('(e)=>e.innerHTML') # Full body present
  assert page.locator('[data-work-anchor]').count()==len(d['toc'])
  page.locator('.work-contents summary').click();page.locator('[data-work-anchor]').last.click();assert page.url.endswith('/#oeuvre/'+w['id'])
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.set_viewport_size({'width':1440,'height':1000})
  assert page.locator('header nav [aria-current="page"]').inner_text()=='Textes Philosophiques'
 assert not errors,errors
 b.close()
print(f'OK : {len(works)} textes identiques aux sources ; recherche, filtre, lecture, sommaires et mobile.')
