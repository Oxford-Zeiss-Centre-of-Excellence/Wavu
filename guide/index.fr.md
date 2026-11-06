---
title: Accueil
hide:
  - navigation
  - toc
---

# Wavu : votre Python, dans votre visualiseur d'images

*Wavu* veut dire **pont** en fidjien. Il relie le visualiseur où vous
regardez vos images, **Fiji** ou **napari**, à Python, où vivent des outils
comme Cellpose et scikit-image.

Imaginez un restaurant. **Le visualiseur est le serveur** : il prend votre
commande (une boîte de dialogue avec quelques champs), apporte vos images en
cuisine comme **ingrédients**, et rapporte l'assiette à votre table
(nouvelles images, tableaux, contours). **Le worker est la cuisine** derrière
la porte, et chaque recette a **sa propre batterie de cuisine**, ses propres
casseroles, couteaux et fours (les paquets Python) : la recette Cellpose
n'emprunte (et ne casse) jamais les ustensiles de la recette de flou. La même
recette peut être servie par l'un ou l'autre serveur.

![Les serveurs (frontends): wavu-fiji, wavu-napari → La cuisine (backend): worker wavu, votre script.py PARAMS + run(), son propre env. pixi (la batterie de cuisine) — optionnel : toute la cuisine dans un conteneur (Docker / Apptainer)](assets/img/home-model.svg){ width="1000" }

**Un dossier de script, deux visualiseurs.** Vous écrivez `script.py` une
seule fois ; les utilisateurs de Fiji comme ceux de napari le lancent, à
chaque fois dans l'environnement propre au dossier.

## Pourquoi Wavu existe { #why-this-exists }

- **Un seul environnement pour tout finit par casser.** Installez avec `pip`
  un plugin Cellpose dans l'environnement de napari : il peut amener une autre
  version de PyTorch, NumPy ou Qt ; le plugin suivant en impose d'autres, et
  napari ou l'outil d'un collègue ne démarre plus. Mélanger `conda` et `pip`
  dans un même environnement aggrave les choses.
- **Python dans Fiji, c'est encore plus dur.** Le langage de script de Fiji
  est Jython (Python 2.7, sans NumPy). Les passerelles comme PyImageJ obligent
  à accorder à la main les versions de Java, de conda et des paquets sur
  chaque machine.
- **La réponse de Wavu :** le visualiseur reste petit et propre, et chaque
  script tourne dans **son propre environnement pixi**, construit à partir de
  son propre `pixi.lock`. Les scripts ne partagent aucun paquet : ils ne
  peuvent casser ni les autres, ni napari, ni Fiji, et le même dossier
  s'installe à l'identique sur chaque ordinateur.

## Plus qu'un pont : des analyses entières, en script

Wavu est aussi un **appel de fonction** que vos propres scripts peuvent
faire. Un script Groovy, une macro ImageJ ou un notebook Python parcourt un
dossier, fait lui-même les étapes natives (ouvrir, prétraiter, mesurer,
enregistrer) et ne confie à Wavu que l'étape lourde, comme Cellpose ; Wavu
l'exécute dans son propre environnement et renvoie le résultat au script. Un
seul script, tout le dossier, à chaque fois de la même façon.

[Workflows en script :material-arrow-right:](workflows/index.md){ .md-button .md-button--primary }

## Par où voulez-vous commencer ? { #where-do-you-want-to-start }

<div class="grid cards" markdown>

-   :material-lightbulb-outline:{ .lg .middle } **Comprendre le modèle**

    ---

    Serveur, cuisine, batterie de cuisine : ce qui tourne où, et pourquoi
    vos paquets n'entrent jamais en conflit.

    [:octicons-arrow-right-24: Comment ça marche](model/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **Écrire un script**

    ---

    Transformez votre notebook en entrée de menu, en commençant par les
    tests. Récupérez le modèle prêt à l'emploi en un clic :

    [Ouvrir le modèle dans VS Code](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: Obtenir le modèle](write/get-the-template.md)

-   :material-microscope:{ .lg .middle } **L'utiliser dans Fiji**

    ---

    Installez wavu-fiji, lancez votre premier script sur une image
    d'exemple, et partagez vos outils avec votre labo sous forme d'un seul
    fichier zip.

    [:octicons-arrow-right-24: wavu-fiji](fiji/install.md)

-   :material-layers-outline:{ .lg .middle } **L'utiliser dans napari**

    ---

    Lancez napari avec le panneau Wavu ; les résultats reviennent sous forme
    de calques Image, Labels et Shapes.

    [:octicons-arrow-right-24: wavu-napari](napari/install.md)

</div>

## Bon à savoir { #good-to-know }

- **Quelle taille de données ?** L'usage interactif, c'est une image qui
  tient en mémoire, environ 1–2 Go. Avec un traitement par blocs, en flux
  (OME-Zarr), Wavu peut traiter jusqu'à environ 50 Go sur un ordinateur local,
  **avec une réserve importante** : Fiji et napari sont des visualiseurs à
  canevas, conçus pour des données en mémoire ; pendant un flux, ils ne voient
  qu'un petit aperçu ou le résultat final, restent lents et ne sont pas
  l'endroit recommandé pour le piloter. Au-delà d'environ 50 Go, utilisez un
  pipeline par lots ou HPC.
- **Chaque script a son propre environnement** : un script PyTorch et un
  script qui n'utilise que NumPy ne se gênent jamais.
- **Curieux de savoir comment c'est construit ?** La page
  [architecture](model/architecture.md) explique le worker, son protocole
  HTTP et la façon dont un visualiseur le démarre.

Vous voulez tous les détails, de l'idée au plugin Fiji publié ? Lisez le
[guide complet sur GitHub](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md) (en anglais).
