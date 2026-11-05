# Qu'est-ce que Wavu ?

## L'idée en mots simples

Vous connaissez déjà deux mondes. Dans **Fiji**, vous ouvrez des images,
dessinez des régions et mesurez. Dans un **notebook Jupyter**, vous lancez des
outils Python comme Cellpose ou scikit-image. Passer de l'un à l'autre veut
souvent dire enregistrer des fichiers, changer de programme et tout recharger.

Wavu est un **pont** entre les deux. Vous continuez à travailler dans Fiji ;
quand vous avez besoin de Python, vous choisissez une entrée de menu,
remplissez une petite boîte de dialogue et cliquez sur OK. Le code Python
s'exécute, et les résultats reviennent dans Fiji sous forme de nouvelles
images, de tableaux ou de contours.

![L'analogie du restaurant : Fiji est le serveur, le worker est la cuisine, chaque recette a son propre garde-manger](../assets/img/restaurant.svg){ width="720" }

L'image du restaurant aide :

| Au restaurant | Dans Wavu | Ce que c'est vraiment |
|---|---|---|
| Le serveur prend votre commande | **Fiji** affiche une boîte de dialogue | les entrées du menu Wavu dans Fiji |
| La carte | **PARAMS** | une courte liste en haut du script Python |
| La cuisine | **le worker** | un petit programme Python qui tourne sur *votre* ordinateur |
| Une recette | **votre script** | un fichier `.py` avec une fonction `run` |
| Le garde-manger de chaque recette | **l'environnement** | un dossier avec exactement les paquets dont ce script a besoin |

Comme chaque recette a son propre garde-manger, installer PyTorch pour un
script ne peut jamais casser un autre script. Personne ne partage son
garde-manger, donc rien ne se gâte.

## Pour qui ?

- Vous écrivez des notebooks et avez déjà utilisé Cellpose ou scikit-image.
- Vous connaissez Fiji, et vous aimeriez que votre étape Python s'y fasse en
  *un clic*.
- Vous ne voulez **pas** apprendre Java, les astuces de conda ou Docker.

## Ce que Wavu n'est pas

!!! warning "Pas pour les grosses données"
    Wavu envoie une image à la fois, et elle doit tenir dans la mémoire de
    votre ordinateur (environ 1–2 Go au maximum). Pour de très gros volumes,
    beaucoup de fichiers ou des lames entières, utilisez plutôt un traitement
    par lots ou un cluster de calcul (HPC).

!!! warning "Pas un bac à sable de sécurité"
    Les environnements séparés isolent les *paquets*. Ils n'enferment pas un
    script. Un script peut faire tout ce que votre compte utilisateur peut
    faire : n'exécutez donc que des scripts de confiance, exactement comme
    avec un notebook.

Wavu ne remplace pas non plus votre notebook. Les notebooks sont parfaits pour
explorer ; Wavu sert au moment où la recette fonctionne et où vous voulez
l'utiliser, ou la faire utiliser par vos collègues, depuis Fiji.

## À quoi ressemble une exécution

1. Dans Fiji, ouvrez une image.
2. Choisissez **Plugins › Wavu › Run Python Script** (lancer un script
   Python) et sélectionnez un dossier de script.
3. Une boîte de dialogue apparaît. Remplissez-la et cliquez sur **OK**.
4. Des messages défilent dans la fenêtre **Log** de Fiji et la barre de
   progression avance.
5. Les résultats s'ouvrent dans Fiji.

La toute première exécution d'un script est lente, car on remplit son
garde-manger (l'environnement) : les paquets se téléchargent une seule fois.
Ensuite, il démarre vite.

## En une phrase

Wavu permet à Fiji d'envoyer une image et quelques réglages à votre script
Python, qui tourne dans son propre environnement bien rangé et renvoie
directement les résultats.

[Suite : installer Wavu dans Fiji :material-arrow-right:](install.md){ .md-button }
