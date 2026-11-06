# Données volumineuses : analyse en flux

!!! warning "Ça marche, mais Fiji et napari ne sont pas l'endroit pour le piloter"
    Pour les **images qui tiennent en mémoire (environ 1–2 Go)**, gardez le
    chemin interactif habituel : choisissez une image, appuyez sur **OK**,
    obtenez le résultat. Rien sur cette page n'est nécessaire pour cela.

    Avec un traitement découpé en blocs et en flux (OME-Zarr), un script Wavu
    peut traiter des données **jusqu'à environ 50 Go sur un ordinateur
    local**. Mais Fiji et napari sont des visualiseurs à canevas, conçus
    autour de données gardées en mémoire : pendant un flux, ils ne voient
    qu'un **petit aperçu ou le résultat final**, ils restent lents tant qu'il
    tourne, et ce **n'est pas l'endroit recommandé pour le piloter**.
    Au-delà d'environ 50 Go, utilisez plutôt un pipeline par lots ou HPC
    (voir [la fin de cette page](#when-not-to-do-this-in-fiji-or-napari)).

!!! info "Un modèle de conception, pas une fonction intégrée"
    Tout ce qui suit décrit comment **vous** écrivez **votre propre
    script**. Wavu lui-même ne fait que passer un chemin et les paramètres à
    `run`, et renvoie le chemin que votre script lui rend. Le découpage en
    blocs, dask et OME-Zarr sont l'affaire de votre script, et ses paquets
    vivent dans son propre `pixi.toml`.

## L'idée en mots simples { #the-idea-in-plain-words }

![Un gros bloc 3-D brut sur une planche à découper est coupé au couteau en huit morceaux ; les morceaux partent en parallèle vers quatre petites sous-cuisines, chacune cuisinant un morceau à la fois ; les morceaux cuits sont assemblés sur une seule assiette en un repas complet, qui s'illumine quand il est terminé.](../assets/img/stream/sub-kitchens.svg){ width="800" }

*La grosse image est coupée en morceaux (les blocs, ou *chunks*, OME-Zarr),
et plusieurs sous-cuisines (des workers en parallèle) cuisinent chacune un
morceau à la fois : seuls quelques morceaux sont donc en mémoire en même
temps. Les morceaux cuits sont assemblés sur une seule assiette en un seul
repas : le résultat.*

Retour au restaurant. Un mariage a commandé un dîner pour cinq cents
invités. Aucun plan de travail ne peut contenir tous ces ingrédients, alors
la cuisine travaille **par fournées** : elle va chercher les ingrédients
**caisse par caisse**, cuisine plusieurs caisses à la fois sur différents
fourneaux, et envoie les assiettes dès qu'elles sont prêtes. Le serveur
n'apporte à votre table qu'une **assiette de dégustation**, pour montrer que
le plat a l'air réussi.

Pour les images, les caisses sont des **blocs** (*chunks*) : une grosse
image découpée en une grille de petits blocs. Chaque bloc est enregistré
comme **son propre petit fichier**, pour qu'un programme puisse lire un
bloc sans toucher au reste.

![Une grande image est découpée en une grille de blocs ; chaque bloc est enregistré comme son propre petit fichier dans un dossier OME-Zarr ; un lecteur ne va chercher que les blocs dont il a besoin, un fichier à la fois, et les nombres mesurés sur chacun remplissent un tableau de résultats et un graphique.](../assets/img/stream/zarr-chunking.svg){ width="800" }

*Une grosse image devient un dossier de petits fichiers, un par bloc. Un
lecteur ne va chercher que les fichiers dont il a besoin, un à la fois, et
ce qu'il mesure sur chaque bloc devient une ligne du tableau de résultats
et une barre du graphique.*

## Pourquoi OME-Zarr { #why-ome-zarr }

**OME-Zarr** (aussi appelé OME-NGFF, Next-Generation File Format) est un
format ouvert fait exactement pour cela :

- **Découpé en blocs.** Chaque bloc est son propre fichier : lire une
  région coûte une région, pas toute l'image.
- **Multi-échelle.** L'image est aussi stockée à des résolutions plus
  basses (une *pyramide*) ; un visualiseur montre d'abord le petit niveau et
  ne va chercher le détail que là où vous zoomez.
- **Adapté au cloud.** La même organisation marche dans un dossier, sur un
  partage réseau ou dans un stockage objet (S3).
- **Ouvert.** Un standard communautaire de l'OME, lu par napari, Fiji et
  Python.

Comparez avec **un seul gros TIFF** : la plupart des programmes le lisent
comme un seul fichier du début à la fin, un TIFF classique s'arrête à 4 Go
(BigTIFF lève cette limite), et il est écrit dans l'ordre par **un seul
écrivain**. Très bien pour quelques gigaoctets, pénible pour cinquante.

## Le flux dans le backend { #streaming-in-the-backend }

L'astuce : le serveur ne porte jamais les ingrédients. Votre script ne
reçoit pas de pixels ; il reçoit un **chemin**.

![Un seul magasin OME-Zarr, data.ome.zarr, avec le groupe d'entrée /image à gauche et le groupe de sortie /label à droite ; le worker lit un bloc à la fois dans sa petite boîte de mémoire, le traite, écrit le bloc résultat dans l'emplacement correspondant de /label et le relâche ; chaque bloc laisse un minuscule tableau de résultats, et à la fin ils fusionnent en un tableau assemblé à droite.](../assets/img/stream/stream-loading.svg){ width="800" }

*Un magasin (store), deux groupes : à gauche le groupe `/image`, à droite
le groupe `/label`. Un bloc à la fois passe de `/image` dans la petite
boîte de mémoire, est traité, est écrit à sa place dans `/label`, et quitte
la mémoire. Chaque bloc laisse aussi un petit tableau de résultats ; à la
fin, ils fusionnent en un seul tableau assemblé.*

Étape par étape, dans `run` :

1. **Recevoir un chemin.** Ici un paramètre texte. (Un chemin envoyé comme
   *entrée* qui n'est pas un TIFF, un CSV ou un ZIP arrive aussi sans être
   ouvert, sous forme de `pathlib.Path` ; voir
   [les données en transit](../model/architecture.md#data-on-the-wire).)
2. **L'ouvrir paresseusement.** `dask.array.from_zarr` connaît la forme, le
   type et la grille de blocs, mais n'a encore lu **aucun pixel**.
3. **Traiter bloc par bloc.** Vous décrivez le travail sur le tableau
   entier ; dask le transforme en une petite tâche par bloc.
4. **Écrire le résultat à côté de l'entrée**, pas dans `ctx.tmpdir`, qui
   est supprimé quand le worker s'arrête.
5. **Renvoyer un `Path` et un petit tableau d'aperçu.** Le chemin est
   affiché dans le Log ; l'aperçu (bien en dessous de la limite de 4 Mio
   pour l'envoi direct) s'ouvre comme une image ordinaire.

## Traitement parallèle avec dask { #parallel-processing-with-dask }

[dask](https://docs.dask.org/en/stable/array.html) est le chef de cuisine :
il distribue les caisses aux fourneaux.

![Quatre workers, dessinés comme des roues qui tournent, prennent chacun un bloc différent avec une fine bordure empruntée à ses voisins, les traitent en même temps et rognent la bordure ; chaque bloc traité retourne dans la grille de sortie, et ses nombres deviennent une nouvelle ligne d'un tableau de résultats qui grandit.](../assets/img/stream/parallel-processing.svg){ width="800" }

*Quatre workers traitent quatre blocs à la fois. Chaque bloc porte une fine
bordure venue de ses voisins (le halo), rognée ensuite. Chaque résultat
part dans deux directions : le bloc traité retourne à sa place dans la
grille de sortie (l'assemblage des blocs), et ses nombres vont dans une
nouvelle ligne du tableau de résultats (l'assemblage des résultats).*

- **`map_blocks`** applique votre fonction à chaque bloc séparément :
  parfait pour tout ce qui regarde un pixel à la fois, comme un seuil.
- **`map_overlap`** ajoute d'abord un **halo** de `depth` pixels empruntés
  aux blocs voisins, applique votre fonction, puis rogne le halo. Les
  filtres qui regardent les voisins (flou gaussien, médiane, morphologie)
  en ont besoin, sinon vous obtenez des coutures à chaque bord de bloc.
  `boundary="reflect"` indique quoi emprunter au bord extérieur de l'image.
  Pour un gaussien, un `depth` d'environ `4 × sigma` pixels suffit.

```python
import dask.array as da

image = da.from_zarr("D:/data/big.zarr", component="0")   # paresseux, rien n'est encore lu
mask = image.map_blocks(lambda block: block > 500, dtype=bool)   # pas besoin des voisins
```

**Taille des blocs.** Visez **quelques dizaines de Mo par bloc** (par
exemple 64 × 512 × 512 en `uint16` = 32 Mo). Beaucoup plus petit, et dask
passe son temps en comptabilité ; beaucoup plus gros, et chaque fourneau a
besoin de beaucoup de plan de travail. Utilisez `image.rechunk(...)` si les
blocs sur le disque sont très éloignés de cela.

**Nombre de workers.** L'ordonnanceur par défaut de dask pour les tableaux
utilise des **threads** dans un seul processus ; ils partagent la mémoire,
donc faire circuler les blocs ne coûte rien. Choisissez combien avec
`dask.config.set(num_workers=4)`. Si votre fonction est du Python pur et
n'accélère pas avec plus de threads, essayez `scheduler="processes"`.

**Règle empirique pour la mémoire.** Mémoire maximale ≈ **workers × taille
de bloc × 3 à 4** (entrée, halo, une copie en float, sortie). Quatre workers
sur des blocs de 32 Mo ont besoin d'environ un demi-gigaoctet, quelle que
soit la taille de l'image entière.

## La conception du code { #the-code-design }

Un dossier de script pour le flux est un dossier de script Wavu ordinaire.
Ajoutez les paquets à son `pixi.toml` (tous sur conda-forge) :

```toml
[dependencies]
dask = ">=2024.1"
zarr = ">=2.16"
ome-zarr = ">=0.9"     # `ome-zarr` sur conda-forge, importé comme ome_zarr
scipy = ">=1.10"
tifffile = ">=2023.1"
```

`script.py`, le squelette :

```python
"""Smooth a large OME-Zarr image chunk by chunk (Gaussian blur)."""
from pathlib import Path

import dask
import dask.array as da
import numpy as np
from dask.callbacks import Callback
from scipy import ndimage

PARAMS = {
    "store": {"type": "str", "default": "", "label": "Input OME-Zarr folder"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
    "output_format": {"type": "choice", "choices": ["ome-zarr", "tiff"], "default": "ome-zarr"},
}


class WavuProgress(Callback):
    """Report dask's finished tasks as ctx.progress, and stop when the user cancels."""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    def _start_state(self, dsk, state):
        self.total = sum(len(state[k]) for k in ("ready", "waiting", "running", "finished"))

    def _posttask(self, key, result, dsk, state, worker_id):
        self.ctx.progress(len(state["finished"]) / max(self.total, 1))
        self.ctx.check_cancelled()          # lève wavu.Cancelled, ce qui arrête dask


def run(ctx, inputs, params):
    store = Path(params["store"])
    sigma = params["sigma"]
    image = da.from_zarr(str(store), component="0")    # pleine résolution, paresseux
    ctx.log(f"{image.shape} {image.dtype}, chunks {image.chunksize}")

    depth = int(4 * sigma) + 1                         # le halo dont un gaussien a besoin
    smoothed = image.astype(np.float32).map_overlap(
        ndimage.gaussian_filter, depth=depth, boundary="reflect", sigma=sigma)

    with dask.config.set(scheduler="threads", num_workers=4):
        if params["output_format"] == "ome-zarr":
            out = store.with_name(store.stem + "-smoothed.zarr")
            write_ome_zarr(smoothed, out, ctx)
        else:
            out = store.with_name(store.stem + "-smoothed.tif")
            write_tiff(smoothed, out, ctx)

        z = smoothed.shape[0] // 2                     # aperçu : plan du milieu, sous-échantillonné
        step = max(1, max(smoothed.shape[1:]) // 512)
        preview = smoothed[z, ::step, ::step].compute()
    return {"result": out, "preview": preview}
```

Les deux écrivains. **OME-Zarr** (par défaut) écrit bloc par bloc, en
parallèle, et construit la pyramide de résolutions :

```python
def write_ome_zarr(arr, out, ctx):
    import zarr
    from ome_zarr.io import parse_url
    from ome_zarr.writer import write_image

    root = zarr.group(store=parse_url(str(out), mode="w").store)
    with WavuProgress(ctx):
        write_image(arr, group=root, axes="zyx", storage_options={"chunks": arr.chunksize})
```

**TIFF** passe par **un seul écrivain**, plan après plan : c'est donc plus
lent, impossible à paralléliser, et le résultat est un seul gros fichier
que la plupart des visualiseurs lisent en entier. Ici, les vérifications
de progression et d'annulation se trouvent dans la boucle :

```python
def write_tiff(arr, out, ctx):
    import tifffile

    cz = arr.chunksize[0]

    def planes():                                      # un bloc de plans à la fois
        for z0 in range(0, arr.shape[0], cz):
            ctx.check_cancelled()
            ctx.progress(z0 / arr.shape[0])
            yield from arr[z0:z0 + cz].compute()

    tifffile.imwrite(out, planes(), shape=arr.shape, dtype=arr.dtype, bigtiff=True)
```

Le squelette suppose une image 3-D `zyx` dont le niveau en pleine
résolution est `0`, comme dans un OME-Zarr à image unique. Pour des données
4-D ou 5-D, adaptez `axes` et la tranche d'aperçu.

**L'appeler.** Le format de sortie n'est qu'un paramètre : il fait donc
partie de l'appel, et vaut OME-Zarr par défaut :

=== "Groovy (Fiji)"

    ```groovy
    def r = wavu.run(folder, "script",          // folder : le dossier de script
            [store: "D:/data/big.zarr", output_format: "ome-zarr"], [:])
    println r.files.result          // le chemin du nouvel OME-Zarr
    ```

=== "Python"

    ```python
    from wavu.client import Worker

    with Worker.start("path/to/stream-folder", on_log=print) as w:
        res = w.run("script", {"store": "D:/data/big.zarr", "output_format": "ome-zarr"})
        out = res.outputs["result"].value        # un pathlib.Path
        preview = res.outputs["preview"].value   # un petit tableau NumPy
    ```

`store` est un simple paramètre texte : ce doit donc être un chemin que
**le worker** peut voir. Wavu traduit les chemins des entrées pour un
conteneur, mais pas les paramètres texte : pour un worker dans un
conteneur, tapez le chemin tel que le conteneur le voit.

**Regarder le résultat.** Ouvrez-le paresseusement, pour que seule la
partie visible soit lue : dans napari avec le lecteur
[napari-ome-zarr](https://github.com/ome/napari-ome-zarr)
(`viewer.open(out, plugin="napari-ome-zarr")`), dans Fiji avec
**File › Import › HDF5/N5/Zarr/OME-NGFF…** (les plugins N5). La mise en
garde du début reste valable : parcourir fonctionne, analyser le tout dans
le visualiseur, non.

## Quand ne pas le faire dans Fiji ou napari { #when-not-to-do-this-in-fiji-or-napari }

- **Au-delà d'environ 50 Go**, beaucoup de fichiers ou beaucoup d'heures :
  lancez le même code découpé en blocs comme **tâche par lots** sur une
  station de travail, sans aucun visualiseur
  (`pixi run wavu run script.py --param store=D:/data/big.zarr` dans un
  terminal), sur un **cluster HPC** (l'ordonnanceur distribué de dask
  répartit les blocs sur de nombreuses machines), ou dans le **cloud**, à
  côté des données en stockage objet.
- **Quand le résultat doit être un seul TIFF** plus gros que la mémoire :
  possible, mais lent ; préférez OME-Zarr et ne convertissez que la partie
  dont vous avez besoin.

## En une phrase { #in-one-sentence }

Pour des données trop grosses pour la mémoire, donnez à votre script un
**chemin** au lieu de pixels, laissez dask cuisiner l'OME-Zarr bloc par
bloc sur plusieurs fourneaux, écrivez le résultat à côté de l'entrée et
n'envoyez au visualiseur qu'une assiette de dégustation, pendant que Wavu
lui-même se contente de faire entrer et sortir le chemin.
