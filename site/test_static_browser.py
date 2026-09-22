import json,os,urllib.request
from playwright.sync_api import sync_playwright
BASE=os.environ.get('PHILOCORPUS_SITE_URL','http://127.0.0.1:8746')
catalog=json.load(urllib.request.urlopen(BASE+'/data/catalog.json'))
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1440,'height':1000});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE);page.wait_for_selector('.copy-card');assert page.locator('.copy-card').count()==sum(c['dissertation'] for c in catalog['copies'])
 page.fill('#search','justice');page.wait_for_function('document.querySelectorAll(".copy-card").length>0 && document.querySelectorAll(".copy-card").length<100')
 page.locator('.copy-card h3 a').first.click();page.wait_for_selector('#copyText');assert not page.locator('#toggleScan').count()
 page.locator('#downloadMenu summary').click()
 with page.expect_download() as d:page.click('#downloadJson')
 assert json.load(open(d.value.path()))['text']
 for route,selector in [('laboratoire/explorer','svg.scatter'),('laboratoire/auteurs','#authorRanking table'),('laboratoire/references','#refTable'),('laboratoire/ressource/methode','.resource-prose'),('textes','.resource-card')]:
  page.goto(BASE+'/#'+route);page.wait_for_selector(selector)
 page.locator('.resource-card').first.click();page.wait_for_selector('.source-prose')
 page.goto(BASE+'/#laboratoire/explorer');page.wait_for_selector('[data-tab="plans"]');page.click('[data-tab="plans"]');page.wait_for_selector('#balanceTable')
 sources=page.evaluate('async()=>await staticApi("/api/source-texts")')
 attached=next(s for s in sources if s.get('document_ids'))
 page.goto(BASE+'/#copie/'+attached['document_ids'][0]);page.wait_for_selector('#sourcePane');assert page.locator('#copyText .copy-title').count()==1
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 b.close()
print('OK version statique : bibliothèques, recherche, lecture, téléchargement, trois analyses, méthode, textes sources et mobile.')
