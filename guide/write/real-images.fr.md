# Les vraies images

## L'idée en mots simples

*Blobs* est une seule image plate. Vos images de microscope sont souvent une
**pile d'images** : plusieurs canaux de couleur, plusieurs plans focaux (une
pile en z, ou z-stack), parfois plusieurs instants. Wavu donne à votre script
la **pile entière** sous forme d'un seul tableau NumPy et, quand le
visualiseur le sait, vous dit comment elle est empilée. C'est comme recevoir
une boîte de lames avec une étiquette qui indique dans quel ordre elles sont
rangées.

![Une pile de plans d'image : temps, z, canal, puis y et x](../assets/img/axes.svg){ width="640" }

## La forme du tableau

=== "Fiji"

    Les axes viennent toujours dans cet ordre, et tout axe de longueur 1 est
    supprimé :

    **T** (temps) · **Z** (plans) · **C** (canaux) · **Y** · **X**, plus un
    dernier axe **S** de longueur 3 pour une image couleur RVB.

    | Image dans Fiji | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | une image grise 2-D, 512 × 512 | `(512, 512)` | `"YX"` |
    | 3 canaux | `(3, 512, 512)` | `"CYX"` |
    | pile en z de 20 plans, 2 canaux | `(20, 2, 512, 512)` | `"ZCYX"` |
    | une photo RVB | `(512, 512, 3)` | `"YXS"` |

    Ainsi, « le canal 2 de chaque plan » s'écrit `img[:, 1]` pour une image
    `ZCYX`. Fiji envoie les pixels 8 bits, 16 bits, 32 bits ou RVB tels
    quels.

=== "napari"

    Vous recevez les données du calque choisi telles quelles, dans l'ordre
    des axes propre au calque : un calque pile en z arrive sous la forme
    `(20, 512, 512)`. napari ouvre en général chaque canal comme un calque
    séparé ; choisissez donc le canal que vous voulez.

    | Calque dans napari | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | une image grise 2-D | `(512, 512)` | `"YX"` |
    | une pile en z de 20 plans | `(20, 512, 512)` | `"ZYX"` si les étiquettes d'axes du calque disent z, y, x ; sinon non défini |
    | une photo RVB | `(512, 512, 3)` | `"YXS"` |

    Un calque **multi-échelle** (une pyramide d'images) envoie son niveau en
    pleine résolution. Les calques 2-D et RVB ont toujours des lettres
    d'axes ; les calques plus grands seulement quand les étiquettes d'axes de
    napari sont de simples lettres (t, z, c, y, x), comme les lecteurs
    OME-Zarr les définissent. Lisez donc les axes avec `.get("axes")` et
    regardez `img.ndim` et `img.shape`.

## Ce que vous recevez en plus : `ctx.meta` { #what-else-you-get-ctxmeta }

`ctx.meta["image"]` contient ce que le visualiseur sait de l'image choisie
pour le champ `"image"` :

- `"axes"` : les lettres des axes, comme ci-dessus (toujours dans Fiji ;
  dans napari pour les calques 2-D et RVB, et pour les calques plus grands
  dont les étiquettes d'axes sont t/z/c/y/x) ;
- `"pixel_um"` : la taille de pixel en micromètres, si elle est connue :
  d'après la calibration de l'image dans Fiji, d'après l'**échelle** (scale)
  du calque dans napari (quand ses deux dernières valeurs sont égales et
  différentes de 1) ;
- `"title"` : le titre de la fenêtre (Fiji) ou le nom du calque (napari).

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"].get("axes")      # None si le visualiseur ne l'a pas indiqué
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel")
    ...
```

Vérifier la forme et lever une `ValueError` claire est plus aimable que de
laisser votre code planter plus loin : Fiji affiche la phrase dans une
fenêtre d'erreur, napari dans le journal du panneau et dans une
notification.

## Jusqu'à quelle taille ? { #how-big-is-too-big }

Wavu est fait pour le **travail interactif sur une image qui tient
confortablement en mémoire**, environ jusqu'à **1–2 Go**. Les petites images
voyagent dans un seul message ; les plus grosses passent par un fichier TIFF
temporaire sur votre disque. Vous n'avez rien à faire : `inputs["image"]` est
un tableau NumPy dans les deux cas. La limite est la même dans Fiji et
napari.

!!! warning "napari : les gros calques paresseux sont chargés en entier"
    napari peut afficher d'énormes images de façon paresseuse (un tableau
    *dask*), en ne lisant que la partie à l'écran. Wavu ne le peut pas : il
    charge tout le calque en mémoire avant de l'envoyer ; choisissez donc un
    calque qui tient en mémoire (un recadrage, un seul canal ou une copie en
    plus basse résolution).

Au-delà de cette taille, ou pour des centaines de fichiers, Wavu n'est pas le
bon outil. Convertissez en OME-Zarr et utilisez plutôt un traitement par lots
ou un cluster de calcul (HPC).

## Premières exécutions lentes (et comment rassurer les utilisateurs) { #slow-first-runs-and-how-to-keep-users-calm }

Deux choses peuvent rendre une *première* exécution lente, et les deux
n'arrivent qu'une fois :

1. **L'environnement est construit.** pixi télécharge les paquets listés
   dans `pixi.toml`. Avec PyTorch (nécessaire à Cellpose), cela peut faire
   **1–2 Go** et plusieurs minutes. Le Log de Fiji ou le journal du panneau
   napari le signale pendant ce temps.
2. **Les poids du modèle sont téléchargés.** Des outils comme Cellpose
   récupèrent leur modèle entraîné sur Internet la première fois qu'il sert.
   Cela se passe *dans votre script* : le visualiseur n'en sait rien et peut
   sembler bloqué.

**Écrivez toujours dans le journal avant une étape lente**, pour que
l'utilisateur sache ce qui se passe :

```python
ctx.log("Loading the Cellpose model (the first time, it is downloaded)...")
ctx.progress(0.1)
model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
ctx.log("Model ready")
```

!!! tip "Une configuration Cellpose qui marche"
    Le dépôt Wavu contient un script Cellpose complet pour les noyaux, avec
    un `pixi.toml` qui inclut PyTorch, Cellpose et une configuration
    facultative pour GPU NVIDIA :
    [`examples/cellpose_nuclei`](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/tree/main/examples/cellpose_nuclei).
    Copiez ses lignes `[dependencies]` et `[pypi-dependencies]` dans votre
    propre `pixi.toml`. Les Mac à puce Apple utilisent leur GPU sans rien
    configurer.

## En une phrase

Votre script reçoit l'image entière en un seul tableau (dans l'ordre
**T Z C Y X** depuis Fiji, dans l'ordre propre au calque depuis napari ;
lisez `ctx.meta` et la forme pour en être sûr), elle doit rester sous
environ 1–2 Go dans l'un comme l'autre visualiseur, et vous devriez appeler
`ctx.log` avant toute étape lente, comme le premier téléchargement d'un
modèle.

[Suite : partager sous forme de conteneur :material-arrow-right:](container.md){ .md-button }
