# Glossaire

## L'idée en mots simples

Chaque domaine a son jargon. Voici chaque mot de Wavu en une ligne simple,
avec l'image du restaurant quand elle aide.

![L'analogie du restaurant : Fiji est le serveur, le worker est la cuisine, chaque recette a sa propre batterie de cuisine](../assets/img/restaurant.svg){ width="560" }

## Les mots

**Fiji**
:   Le programme d'analyse d'images que vous utilisez déjà (ImageJ avec des
    plugins). Dans Wavu, c'est le *serveur* : la boîte de dialogue entre,
    les résultats sortent.

**Wavu**
:   « Pont » en fidjien. Les entrées de menu dans Fiji plus un petit
    assistant Python, qui relient Fiji à votre script Python.

**Script**
:   Un fichier `.py` avec `PARAMS` et une fonction `run`. La *recette*.

**Dossier de script**
:   Un dossier avec un `pixi.toml` et un ou plusieurs scripts. C'est ce que
    vous choisissez dans **Run Python Script**.

**PARAMS**
:   La liste en haut d'un script qui décrit les champs de la boîte de
    dialogue. La *carte*.

**`run(ctx, inputs, params)`**
:   La fonction que Wavu appelle. `inputs` contient les images, `params` les
    autres réglages, et `ctx` est la ligne directe vers Fiji.

**ctx**
:   Abréviation de « context » (contexte) : `ctx.log`, `ctx.progress`,
    `ctx.cancelled` et compagnie.

**Worker**
:   Un petit programme Python sur *votre* ordinateur qui exécute votre script
    quand Fiji le demande. La *cuisine*. Il ne parle à Fiji que sur votre
    propre machine.

**Environnement**
:   Un dossier privé qui contient une version exacte de Python plus les
    paquets dont un script a besoin, rangé dans `.pixi` à l'intérieur du
    dossier de script. La *batterie de cuisine* de la recette : ses
    propres casseroles, couteaux et fours.

**pixi**
:   L'outil gratuit qui construit les environnements et télécharge les
    paquets, une alternative moderne à conda. Wavu le récupère pour vous.

**`pixi.toml`**
:   La *liste de la batterie de cuisine* : les paquets dont le script a
    besoin.

**Fichier de verrouillage (`pixi.lock`)**
:   Le *ticket de caisse* de la batterie de cuisine : la version exacte de
    chaque paquet. Le partager
    veut dire que tout le monde obtient le même environnement.

**conda-forge / PyPI**
:   Les deux grands « magasins » en ligne de paquets Python. pixi utilise
    conda-forge par défaut ; PyPI est le magasin de `pip`.

**Tableau NumPy**
:   La grille de nombres de Python ; c'est ainsi que votre script reçoit et
    renvoie les images.

**Labels (image de labels)**
:   Une image où chaque objet a son propre nombre entier (1, 2, 3 …) et où le
    fond vaut 0. Fiji l'affiche avec des couleurs vives au hasard.

**ROI**
:   « Region of interest » (région d'intérêt) : un contour dessiné sur une
    image. Fiji les garde dans le **ROI Manager** ; un *RoiSet* est un
    fichier zip qui en contient plein.

**Annulation coopérative**
:   Échap lève un drapeau ; votre script le vérifie et s'arrête de lui-même.

**Point d'arrêt (breakpoint)**
:   Un point rouge dans VS Code où un script en cours se met en pause pour
    que vous puissiez regarder à l'intérieur.

**Tag / release**
:   Une étiquette de version comme `v1.0.0` sur votre code, et la page de
    téléchargement que GitHub crée pour elle.

**CI**
:   « Continuous integration » (intégration continue) : le robot de GitHub
    qui teste et emballe votre code quand vous poussez un tag. Facultatif.

**Site de mise à jour (update site)**
:   Une source de téléchargement pour Fiji que vous cochez dans
    **Help › Update…** pour installer et mettre à jour des plugins.

## En une phrase

Fiji est le serveur, le worker la cuisine, votre script la recette, vos
images les ingrédients, son environnement pixi la batterie de cuisine et
`pixi.lock` le ticket de caisse.
