# PhiloCorpus — site de méthodologie

Depuis `/home/gwen/PhiloCorpus` :

```bash
python3 -B site/server.py
```

Ouvrir **http://127.0.0.1:8745** : la bibliothèque s’affiche directement. La méthode dispose de son propre onglet principal. Le site est indépendant de l’atelier de correction (port 8742) et de l’ancienne bibliothèque (port 8741). Ctrl C arrête ce serveur. Il fonctionne localement, sans service distant ni clé API.

## Navigation

- **Bibliothèque** : toutes les copies des deux collections, recherche dans les titres et le texte, filtres de type (dissertation/commentaire), concours, session, gold, avec ou sans note ; lecture par sections, scan à côté du texte, téléchargement Markdown/JSON et impression.
- **Méthode** : ressources intégrales, sommaires, tableaux et notes de bas de page. Les espaces de mise en page et l’ancien sommaire de l’export bureautique sont adaptés à la navigation web. Les fichiers sources sont préservés ; leur téléchargement direct n’est pas proposé.
- **Laboratoire → Explorer le corpus** : dissertations gold, filtres par concours/session, nuage de points longueur-note et corrélation, proportions des sections et export des mesures CSV.

## Sources et mises à jour

Le site est **en lecture seule**. Il lit les `metadata.json`, scans et transcriptions des dossiers `COPIES_with_notes` et `COPIES_without_notes`, ainsi que `viewer/atelier/data/reviews.sqlite3`.

Une copie apparaît une seule fois, même avec plusieurs variantes. Les JSON autoritatifs préexistants sont prioritaires. Sinon, la dernière révision annotée parmi les dernières versions de chaque variante est retenue comme texte gold, conformément au choix du propriétaire. Un brouillon sans repères ne remplace pas une version annotée. Les anciennes versions exportées `atelier__*.json` ne remplacent pas la base de l’atelier, plus récente.

Les limites UTF-16 sont appliquées avant le nettoyage des commentaires de pages, séparateurs étoilés, entités HTML et balises de soulignement. Les sous-repères personnalisés ne tronquent pas une grande partie. Les repères coïncidents sont conservés. Aucun plan, annonce ou conclusion n’est inventé. Les exports indiquent explicitement que les positions d’origine se réfèrent au texte de l’atelier avant nettoyage ; elles ne sont pas des positions dans le texte nettoyé.

Les nouvelles sauvegardes sont détectées à la prochaine requête. **Actualiser les copies** recharge aussi le cache du navigateur. Il n’est pas nécessaire de réexporter les annotations manuellement.

## Ajouter des copies, y compris non notées

Ajouter un dossier dans la collection appropriée avec son `metadata.json` normalisé, un `document_id` unique, la transcription et éventuellement son PDF. Une note absente se note `null`, jamais `0`. La classification dissertation/commentaire suit le nom du dossier dans les deux collections : « commentaire » ou « explication », sans distinction de casse, désigne un commentaire ; les autres dossiers sont classés comme dissertations. La classification est enregistrée dans `metadata.json` sous `genre`, sans modifier `type_epreuve`. Pour un nouveau dossier sans champ `genre`, le site utilise la règle du nom en repli. Les sources sans annotation restent lisibles mais n’entrent pas automatiquement dans le gold.

Les nouveaux dossiers dotés de métadonnées sont détectés lors de l’actualisation. Redémarrer le site après remplacement isolé d’une transcription ou d’un scan sans modification de ses métadonnées.

## Ajouter une ressource

Déposer le Markdown dans le corpus puis ajouter une entrée à [resources.json](resources.json) :

```json
{
  "id": "une-nouvelle-ressource",
  "title": "Titre visible",
  "description": "Une phrase de présentation.",
  "file": "Nom du document.md"
}
```

`id` doit être unique ; `file` est relatif au dossier PhiloCorpus. Les titres Markdown forment le sommaire. Les quatre ressources initiales bénéficient de quelques adaptations de mise en page propres à leur format d’origine. Le bouton d’actualisation fait apparaître la nouvelle ressource.

## Interpréter les mesures

Les mots sont des séquences alphanumériques Unicode. Un mot avec apostrophe ou trait d’union interne compte pour une unité. Le balisage ne compte pas ; aucun comptage de « références philosophiques » n’est déduit automatiquement.

Le graphique longueur-note exclut les notes manquantes, textes absents et limites signalées à vérifier. Les copies sans note restent utilisables pour lire ou comparer des structures lorsqu’elles sont gold. Les proportions décrivent les sections effectivement délimitées. L’équilibre (plus courte / plus longue partie) n’est calculé que si la conclusion est isolée, au moins deux parties sont présentes et aucune limite n’est signalée à vérifier. Cette restriction évite de traiter une conclusion potentiellement intégrée comme faisant nécessairement partie du développement.

Une corrélation n’est pas une règle de notation. Les copies ont été sélectionnées et les concours/sessions diffèrent ; les filtres permettent de réduire ces mélanges, sans rendre l’échantillon représentatif.

## Vérifications

```bash
python3 -B site/test_corpus.py
node --check site/app.js
```

Les tests utilisent un corpus temporaire pour contrôler la lecture des versions gold et leur mise à jour. Ils vérifient aussi les offsets UTF-16, les repères coïncidents, les plans sans troisième partie, le nettoyage, le comptage et la neutralisation du HTML exécutable. Le parcours navigateur peut être lancé avec `python3 -B site/test_browser.py` lorsque le serveur est actif (Playwright et Chromium nécessaires).

Dépendances Python : voir `requirements.txt`. Elles sont déjà installées dans l’environnement de développement. Pour une autre machine : `python3 -m pip install -r site/requirements.txt`.

### Statistiques P1 / P2 / P3

Laboratoire → Explorer le corpus → Équilibre des parties : proportions moyennes (chaque copie pèse autant), rapport médian partie la plus courte / la plus longue, écart de proportions en points, tableau individuel et corrélation avec la note. Seules les copies avec trois parties non vides et sans alerte de découpage sont incluses. Les plans à deux parties sont exclus de cette analyse. Les copies sans note restent dans les statistiques de structure, mais pas dans le graphique ni la corrélation avec la note.

La conclusion est facultative : les copies sans repère de conclusion sont incluses par défaut, avec un filtre permettant de restreindre le calcul aux conclusions isolées. Aucune conclusion ni transition manquante n’est inventée ou retranchée. L’export CSV de cet onglet contient les trois longueurs, pourcentages et mesures, pour la population effectivement filtrée. Les mesures historiques `balance` de l’API restent distinctes ; cet onglet utilise `part_ratio` calculé sur exactement P1/P2/P3.

Vérifier les formules : `node site/test_balance.cjs`.

Chaque section des exports et de la lecture structurée forme désormais un seul bloc : les retours à la ligne internes sont remplacés par des espaces après le nettoyage. Les séparations entre sections demeurent. Les textes de travail et les offsets d’annotation originaux sont conservés.

### Auteurs cités

`#laboratoire/auteurs` classe les auteurs par mentions ou par nombre de dissertations, avec filtres concours, session et corpus gold. Le pourcentage utilise les copies disposant d’annotations à jour, y compris celles sans mention. Cliquer sur un auteur ouvre la liste des copies ; leur panneau « Auteurs convoqués » affiche les contextes par section.

Les fichiers `annotations_references/automatic_authors.json` sont lus sans modification. Leur empreinte est comparée au texte actuel : les annotations périmées sont signalées et exclues des comptes. Les annotations humaines antérieures ne sont pas fusionnées avec cette couche automatique. Pour régénérer celle-ci : `python3 -B reference_rules/annotate.py --apply`.

Vérification navigateur : `python3 -B site/test_authors_browser.py` (serveur local sur 8745).

La navigation principale propose Dissertations (`#dissertations`), Commentaires (`#commentaires`, incluant les explications de texte) et Laboratoire. Les deux bibliothèques utilisent le champ `genre` ; recherche, filtres et tri sont conservés. Les anciens liens `#bibliotheque` et `#accueil` ouvrent les dissertations.

## Textes commentés

Le lecteur des commentaires affiche le texte source au-dessus de la copie lorsque le rapprochement est établi. Sur mobile, le texte source précède la copie. Le bouton « Masquer le texte commenté » permet de se concentrer sur la copie. Les textes restent séparés des mesures et des annotations du candidat.

Le catalogue `Textes_commentaires_de_textes/catalogue.json` relie explicitement les extraits aux identifiants des copies. `anthologie.json` contient les conversions Word sans rattachement présumé. La bibliothèque des commentaires propose un lien vers `#textes`, avec deux collections ; `#texte/<id>` ouvre un extrait seul et les copies associées. Les nouvelles API sont `/api/source-texts`, `/api/source-text?id=...` et `/api/source-pdf?id=...`. L’API document ajoute `commented_text` (objet ou null). Les notes de bas de page ont des identifiants distincts de ceux de la copie.

Vérification : `python3 -B -m unittest discover -s site -p test_source_texts.py`.

## Textes Philosophiques

L’onglet principal `#textes-philosophiques` présente les Markdown de `Textes_philosophiques/` séparément des copies et des textes commentés. Recherche par auteur/titre, filtre de langue et lecteur `#oeuvre/<id>` avec sommaire et notes cliquables. Les textes longs sont chargés seulement à l’ouverture. Le corps Markdown est rendu sans réécriture ; seul le front matter de métadonnées est retiré de l’affichage. Le fichier exact et son empreinte restent présents dans les données exportées.

`philosophical_texts.py` contient les métadonnées des sept textes initiaux. Tout nouveau `.md` du dossier est inclus à la prochaine génération, avec son nom de fichier comme titre par défaut ; compléter les métadonnées pour renseigner auteur et langue. Le sommaire utilise les titres Markdown déjà présents. L’étendue de l’édition est précisée pour Comte (1re et 2e leçons) ; le lecteur n’affirme pas que toutes les œuvres sont intégrales ni dans leur langue de première publication.

Vérification : `python3 -B site/test_works_browser.py` sur l’export servi au port 8746, ou avec `PHILOCORPUS_SITE_URL` pour le site publié.

Les ressources de méthode utilisent `#methode/ressource/<id>`. Les anciennes adresses `#laboratoire/methode` et `#laboratoire/ressource/<id>` redirigent vers cette section indépendante.
