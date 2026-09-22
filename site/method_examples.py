"""Délimitations éditoriales des exemples ; aucune détection par mots-clés génériques."""
import html

# Les phrases de principe restent en dehors de ces plages.
EXAMPLES=[
 ('Définir la guerre', 'Par ex. si l’on pose la définition.', '\n\nVeillez ensuite'),
 ('Suis-je le maître de ma propre vie ?', 'Par exemple dans le sujet ***« Suis-je le maître de ma propre vie ? »***', '\n\nPour le sujet'),
 ('Les sens du travail et de la paix', 'Pour le sujet ***« Le travail libère-t-il ? »***', 'Il convient de ne conserver'),
 ('La présence', '***Sujet « La présence ».***', '**Exercice 1**'),
 ('La critique du professeur', 'Certains syntagmes, comme « La critique du professeur »', '\n\nFormellement, face'),
 ('La nature est-elle le contraire de la culture ?', '***Sujet :*** **« *La nature est-elle le contraire de la culture ?* »**', '\n\nPour les sujets du type (3)'),
 ('Le rôle des sciences humaines', '***Sujet : « Quel rôle jouent les sciences humaines vis-à-vis des sciences ? »***', '\n\n&nbsp;Vous pouvez aussi'),
 ('L’artiste sait-il ce qu’il fait ?', 'Par exemple, le sujet ***« L’artiste sait-il ce qu’il fait ? »***', '\n\n'),
 ('Plan dialectique : durée et valeur', '| *Sujet : N’y a t-il que ce qui dure qui ait de la valeur ?*', '\n\n'),
 ('Le mauvais goût', '| *Sujet : Le mauvais goût*', '\n\n'),
 ('L’artificiel', '| *Sujet : L’artificiel*', '\n\n'),
 ('Plan Janus : peut-on définir l’être humain ?', 'Exemple de plan janus avec le sujet', '\n\nLe principe du plan Janus'),
 ('Plan Janus : faut-il définir l’être humain ?', 'Avec par exemple **« *Faut-il* *définir l’être humain* »**', '\n\nPourquoi ne pas inverser'),
 ('Plan Janus : justifier une décision au nom de la science', 'Exemple d’application du plan Janus sur le sujet', '\n\n## **1.4.'),
 ('Politique et violence', '| Sujet : Politique et violence |', '\n\n'),
]

def prepare_examples(text):
    replacements={}
    for index,(title,start,end) in enumerate(EXAMPLES):
        # Délimitation explicite : ne jamais englober une section par défaut.
        if text.count(start)!=1:continue
        a=text.index(start);b=text.find(end,a+len(start))
        if b<0:continue
        opening=f'PHILOCORPUS_EXAMPLE_OPEN_{index}'
        closing=f'PHILOCORPUS_EXAMPLE_CLOSE_{index}'
        text=text[:a]+'\n\n'+opening+'\n\n'+text[a:b].strip()+'\n\n'+closing+'\n\n'+text[b:]
        replacements[f'<p>{opening}</p>']=f'<details class="method-example"><summary>Exemple : {html.escape(title)}</summary><div class="method-example-body">'
        replacements[f'<p>{closing}</p>']='</div></details>'
    return text,replacements
