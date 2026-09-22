#!/usr/bin/env python3
"""Synchronise les seuls fichiers publiables vers le checkout GitHub dédié."""
import json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
TARGET=ROOT/'deployment'/'github'
def main():
 TARGET.mkdir(parents=True,exist_ok=True)
 for name in ['public','site']:
  if (TARGET/name).exists():shutil.rmtree(TARGET/name)
 shutil.copytree(ROOT/'deployment/vercel/public',TARGET/'public')
 shutil.copytree(HERE,TARGET/'site',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 config={'$schema':'https://openapi.vercel.sh/vercel.json','framework':None,'buildCommand':'','installCommand':'','outputDirectory':'public','headers':[{'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'}]}]}
 (TARGET/'vercel.json').write_text(json.dumps(config,indent=2)+'\n')
 (TARGET/'.gitignore').write_text('.vercel/\n.env\n.env.*\n__pycache__/\n*.pyc\n*.sqlite*\n*.pdf\n')
 (TARGET/'README.md').write_text('''# PhiloCorpus

Bibliothèque de copies de philosophie et laboratoire d’analyse exploratoire.

Site : https://philocorpus.vercel.app

## Contenu

- `public/` : site complet prêt à servir, avec les copies, leurs métadonnées, les références détectées, les textes commentés et les ressources de méthode.
- `site/` : sources de l’application locale, exporteur statique et tests. Les outils Python attendent le corpus local et la base de l’atelier ; ils ne sont pas exécutés par Vercel.
- `vercel.json` : déploiement statique du dossier `public`, sans dépendances à installer.

Les PDF et l’historique de l’atelier sont conservés uniquement dans le corpus local. La version publiée reste en lecture seule. Les mentions d’auteurs sont des repérages automatiques ; les statistiques décrivent un échantillon sélectionné, déséquilibré et hétérogène.

## Lire localement

```bash
python3 -m http.server 8746 --directory public
```

Ouvrir http://localhost:8746. Aucun serveur Python applicatif ni clé API n’est nécessaire pour lire cette version.

## Publier les nouvelles copies depuis le corpus local

Depuis la racine du corpus original :

```bash
python3 -B site/build_static.py
python3 -B site/prepare_github.py
cd deployment/github
git add public site vercel.json README.md .gitignore
git commit -m "Actualiser le corpus"
git push origin main
```

La synchronisation préserve le dossier `.git`. Les ajouts locaux doivent avoir des métadonnées et une transcription reconnues par le corpus. Un simple ajout sur le PC ne modifie pas le site public : il faut exporter puis pousser les fichiers. Les changements de code se font dans le dossier `site` du corpus original avant export, pour éviter qu’un prochain export écrase une modification directe de `public`.

## Vérification

```bash
PHILOCORPUS_SITE_URL=http://localhost:8746 python3 -B site/test_static_browser.py
```

Les tests de navigateur nécessitent Playwright et Chromium. Le logo emploie EB Garamond, dont la licence est incluse dans `public/fonts`.
''')
 files=[p for p in TARGET.rglob('*') if p.is_file() and '.git' not in p.parts]
 assert not any(p.suffix.lower() in ['.pdf','.sqlite3'] for p in files)
 print('Checkout public préparé :',TARGET,';',len(files),'fichiers')
if __name__=='__main__':main()
