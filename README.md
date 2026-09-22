# PhiloCorpus

Bibliothèque de copies de philosophie et laboratoire d’analyse exploratoire.

Site : https://philocorpus.vercel.app

## Contenu

- `public/` : site complet prêt à servir, avec les copies, leurs métadonnées, les références détectées, les textes commentés et les ressources de méthode.
- `Textes_philosophiques/` : fichiers Markdown des œuvres et extraits fournis, préservés dans leur version originale.
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
git add public site Textes_philosophiques vercel.json README.md .gitignore
git commit -m "Actualiser le corpus"
git push origin main
```

Après le push, déclencher un déploiement Vercel depuis GitHub (`gitSource` de type `github`, `repoId` 1381178495, `ref` `main`) sur le projet `prj_E2kpjKLrQbGWR7r0w0oSF4610En4`. Le déploiement depuis GitHub fonctionne ; le déclenchement automatique à chaque push nécessite de connecter ce dépôt dans les réglages Git du projet Vercel.

La synchronisation préserve le dossier `.git`. Les ajouts locaux doivent avoir des métadonnées et une transcription reconnues par le corpus. Un simple ajout sur le PC ne modifie pas le site public : il faut exporter puis pousser les fichiers. Les changements de code se font dans le dossier `site` du corpus original avant export, pour éviter qu’un prochain export écrase une modification directe de `public`.

## Vérification

```bash
PHILOCORPUS_SITE_URL=http://localhost:8746 python3 -B site/test_static_browser.py
```

Les tests de navigateur nécessitent Playwright et Chromium. Le logo emploie EB Garamond, dont la licence est incluse dans `public/fonts`.
