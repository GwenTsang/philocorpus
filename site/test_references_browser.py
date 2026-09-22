"""Compare les graphiques, filtres et exports aux données du catalogue."""
import csv,io,json,urllib.request
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8745'
copies=json.load(urllib.request.urlopen(BASE+'/api/catalog'))['copies']
rows=[c for c in copies if c['dissertation'] and c['grade'] is not None and 0<=c['grade']<=20 and c['authors_status']=='current' and c['has_text'] and c['words']>0 and not c['warnings']]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    page=b.new_page(viewport={'width':1440,'height':1000});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/#laboratoire/auteurs')
    page.locator('.laboratory-nav a[href="#laboratoire/references"]').click()
    page.wait_for_selector('#refTable')
    assert page.locator('#refTable tbody tr').count()==len(rows)
    assert page.locator('svg.scatter circle').count()==len(rows)
    assert page.locator('.laboratory-nav [aria-current="page"]').inner_text()=='Références & note'
    for metric in ['distinct','density','mentions']:
        page.select_option('#refMetric',metric)
        assert page.locator('svg.scatter circle').count()==len(rows)
    with page.expect_download() as result:page.click('#refExport')
    with open(result.value.path(),encoding='utf-8-sig') as f:export=list(csv.DictReader(f,delimiter=';'))
    expected={c['id']:c for c in rows}
    assert {c['id'] for c in export}==set(expected)
    for c in export:
        source=expected[c['id']];mentions=sum(a['count'] for a in source['authors'])
        assert int(c['mentions'])==mentions
        assert int(c['distinct'])==len({a['id'] for a in source['authors']})
        assert abs(float(c['density'])-1000*mentions/source['words'])<1e-9
    exam=rows[0]['exam'];page.select_option('#refExam',exam)
    assert page.locator('#refTable tbody tr').count()==sum(c['exam']==exam for c in rows)
    year=next(c['year'] for c in rows if c['exam']==exam and c['year'])
    page.select_option('#refYear',str(year));page.select_option('#refGold','gold')
    assert page.locator('#refTable tbody tr').count()==sum(c['exam']==exam and c['year']==year and c['gold'] for c in rows)
    page.select_option('#refExam','');page.select_option('#refYear','');page.select_option('#refGold','')
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.locator('#refTable tbody a').first.click();page.wait_for_selector('#copyText')
    assert not errors,errors
    b.close()
print(f'OK : {len(rows)} copies, navigation, trois mesures, filtres, export exact et mobile.')
