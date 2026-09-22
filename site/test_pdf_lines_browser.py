"""Vérifie le contenu et le non-retour à la ligne du lecteur, sans images."""
import json,urllib.request
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8745'
entries=json.load(urllib.request.urlopen(BASE+'/api/source-texts'))
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));total=0;count=0
    # Le catalogue courant désigne les PDF réextraits par leur API détaillée.
    from source_texts import entries as local_entries
    for entry in local_entries():
        if not entry.get('lines_file'):continue
        data=json.load(urllib.request.urlopen(BASE+'/api/source-text?id='+entry['id']))
        expected=[line['text'] for line in data['lines']]
        for width in (1440,390):
            page.set_viewport_size({'width':width,'height':900})
            page.goto(BASE+'/#texte/'+entry['id']);page.wait_for_selector('.pdf-line-number')
            rows=page.locator('.pdf-lines').first
            assert rows.locator('.pdf-line-text').all_text_contents()==expected
            assert rows.locator('.pdf-line-number').all_text_contents()==[str(i) for i in range(1,len(expected)+1)]
            assert rows.locator('.pdf-line-text').evaluate_all('(els)=>els.every(e=>getComputedStyle(e).whiteSpace==="pre" && e.getClientRects().length===1)')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert page.locator('a[href^="/api/source-pdf"],a[href*="devenirenseignant"]').count()==0
        count+=1;total+=len(expected)
    assert not errors,errors
    browser.close()
print(f'OK : {count} extraits, {total} lignes identiques à l’API ; numérotation et absence de repli sur PC et mobile.')
