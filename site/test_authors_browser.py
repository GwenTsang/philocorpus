"""Vérification des comptes, filtres et extraits de références dans le navigateur."""
import json
import urllib.request
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8745'
copies=json.load(urllib.request.urlopen(BASE+'/api/catalog'))['copies']
rows=[c for c in copies if c['authors_status']=='current']
assert rows
occurrences=sum(a['count'] for c in rows for a in c['authors'])
author_ids={a['id'] for c in rows for a in c['authors']}
kant_copies=[c for c in rows if any(a['name']=='Kant' for a in c['authors'])]
# Le catalogue peut évoluer entre deux exécutions : comparer l’interface aux données actuelles.
if not kant_copies:kant_copies=[c for c in rows if any('Kant' in a['name'] for a in c['authors'])]
kant_count=sum(a['count'] for c in kant_copies for a in c['authors'] if 'Kant' in a['name'])
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    page=browser.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/#laboratoire/auteurs')
    page.wait_for_selector('[data-author]')
    assert page.locator('[data-author]').count()==len(author_ids)
    assert f'{occurrences} mentions' in page.locator('#authorCoverage').inner_text()
    page.fill('#authorQuery','kant')
    assert page.locator('[data-author]').count()==1
    assert str(kant_count) in page.locator('#authorRanking').inner_text()
    page.locator('[data-author]').click()
    assert page.locator('#authorCopies .copy-card').count()==len(kant_copies)
    page.locator('#authorCopies .copy-card h3 a').first.click()
    page.wait_for_selector('.author-panel')
    page.locator('.author-panel > summary').click()
    page.locator('.author-entry > summary').first.click()
    assert page.locator('.author-context mark').first.is_visible()
    page.goto(BASE+'/#laboratoire/auteurs')
    page.wait_for_selector('[data-author]')
    page.select_option('#authorGold','gold')
    page.select_option('#authorExam','AGREG externe')
    expected=[c for c in rows if c['gold'] and c['exam']=='AGREG externe']
    assert page.locator('#authorCoverage').inner_text().startswith(str(len(expected))+' dissertations')
    page.fill('#authorQuery','inexistantxyz')
    assert page.locator('#authorRanking .empty').is_visible()
    page.set_viewport_size({'width':390,'height':844})
    page.fill('#authorQuery','')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert not errors,errors
    browser.close()
print('OK : comptes, copies par auteur, contextes, filtres, état vide, mobile.')
