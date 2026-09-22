from playwright.sync_api import sync_playwright
import json,urllib.request
import os
base=os.environ.get('PHILOCORPUS_SITE_URL','http://127.0.0.1:8745')
data=json.load(urllib.request.urlopen(base+'/api/catalog'));docs=[d for d in data['copies'] if d['dissertation']];gold=[d for d in docs if d['gold'] and d['dissertation']]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base);page.wait_for_selector('#copyResults .copy-card');page.locator('nav a[href="#dissertations"]').click();page.wait_for_function('(n)=>document.querySelectorAll(".copy-card").length===n',arg=len(docs))
 page.locator('header nav a[href="#commentaires"]').click();page.wait_for_function('(n)=>document.querySelectorAll(".copy-card").length===n',arg=sum(d['genre']=='commentaire' for d in data['copies']))
 assert page.locator('header nav a[href="#commentaires"]').get_attribute('aria-current')=='page'
 page.locator('header nav a[href="#dissertations"]').click();page.wait_for_function('(n)=>document.querySelectorAll(".copy-card").length===n',arg=len(docs))
 page.select_option('#rated','no');page.wait_for_function('(n)=>document.querySelectorAll(".copy-card").length===n',arg=sum(c['grade'] is None for c in docs));page.select_option('#rated','');page.wait_for_function('(n)=>document.querySelectorAll(".copy-card").length===n',arg=len(docs));
 page.select_option('#gold','gold');page.wait_for_function('(n)=>document.querySelectorAll(".copy-card").length===n',arg=len(gold))
 page.fill('#search','justice');page.wait_for_function('(n)=>document.querySelectorAll(".copy-card").length>0 && document.querySelectorAll(".copy-card").length<n',arg=len(gold),timeout=30000)
 page.locator('.copy-card h3 a').first.click();page.wait_for_selector('.copy-prose');assert page.locator('.copy-prose').inner_text().strip()
 page.locator("#downloadMenu summary").click()
 with page.expect_download() as dl:page.locator('#downloadJson').click()
 loaded=json.loads(open(dl.value.path()).read());assert loaded['gold'];assert loaded['text']
 if page.locator('#toggleScan').count():
  page.locator('#toggleScan').click();page.wait_for_function('document.querySelector("#scanImg").naturalWidth>0 && !document.querySelector("#scanImg").hidden')
 page.screenshot(path='/tmp/philosite-reader.png')
 for resource in data['resources']:
  page.goto(base+'/#ressource/'+resource['id']);page.wait_for_selector('.resource-prose');assert len(page.locator('.resource-prose').inner_text())>1000;assert page.locator('.toc a').count()>0
  page.locator('.toc a').last.click();assert page.url.endswith('/#laboratoire/ressource/'+resource['id'])
  if resource['id']=='tableaux':assert page.locator('.resource-prose table').count()>0
 page.goto(base+'/#explorer');page.wait_for_selector('svg.scatter');assert page.locator('svg.scatter circle').count()>0
 page.select_option('#expExam','AGREG externe');page.wait_for_timeout(200);assert page.locator('svg.scatter circle').count()<len(gold)
 with page.expect_download() as dl:page.locator('#exportCsv').click()
 assert 'AGREG externe' in open(dl.value.path(),encoding='utf-8-sig').read()
 page.locator('[data-tab="plans"]').click();page.wait_for_selector('.plan-bar',timeout=60000);assert page.locator('.plan-bar').count()>0
 assert page.locator('[data-tab="passages"]').count()==0
 assert page.locator('[role="tab"]').count()==2
 page.screenshot(path='/tmp/philosite-explorer.png',full_page=False)
 page.set_viewport_size({'width':390,'height':844});page.goto(base+'/#accueil');page.wait_for_selector('#copyResults .copy-card');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path='/tmp/philosite-mobile.png',full_page=True)
 page.goto(base+'/#ressource/tableaux');page.wait_for_selector('.resource-prose table');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 print('OK navigation, corpus complet, recherche, gold, lecture, scan, export JSON/CSV, quatre ressources et sommaires, tableaux, graphique filtré, structures, absence de la comparaison et mobile.')
 b.close()
