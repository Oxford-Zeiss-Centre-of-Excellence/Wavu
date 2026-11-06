# Log, progression et annulation

## L'idée en mots simples

Quand la cuisine est occupée, un bon serveur vous dit où on en est : « votre
soupe est sur le feu », « c'est presque prêt ». Et si vous changez d'avis,
vous pouvez annuler, mais c'est le cuisinier qui décide quand il peut
arrêter de remuer sans risque.

Dans Wavu, `ctx` est cette ligne entre la cuisine et la table :

- `ctx.log("…")` envoie un message au **journal** (log).
- `ctx.progress(0.5)` amène la **barre de progression** à mi-chemin.
- `ctx.cancelled()` vous dit si l'utilisateur a demandé d'**arrêter**.

Votre code est le même dans les deux visualiseurs ; seul l'endroit où les
choses s'affichent change :

| | Fiji | napari |
|---|---|---|
| `ctx.log` et `print` | la fenêtre **Log** | la zone de journal du panneau Wavu |
| `ctx.progress` | la barre de progression de Fiji, plus *Wavu: script 40%* dans la barre d'état | la barre de progression du panneau Wavu |
| comment l'utilisateur annule | appuyer sur **Échap** (Esc) | appuyer sur **Cancel** dans le panneau |
| une erreur dans votre code | une fenêtre d'erreur, détails dans le Log | `Error: …` dans le journal du panneau, plus une notification |

```mermaid
flowchart RL
    S["votre run()"]:::script
    L["journal<br/>(fenêtre Log · journal du panneau)"]:::fiji
    P["barre de progression"]:::fiji
    E["Échap · bouton Cancel"]:::fiji
    S -- "ctx.log(...)" --> L
    S -- "ctx.progress(0..1)" --> P
    E -. "ctx.cancelled() devient True" .-> S

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
```

## Écrire dans le Log { #logging }

```python
ctx.log(f"Segmenting a {img.shape} image")
```

La ligne apparaît immédiatement dans le journal, pendant que votre code
tourne encore. Un simple `print(...)` dans `run` fait la même chose. Écrivez
dans le journal *avant* toute étape lente, pour que l'utilisateur sache que
rien n'est bloqué.

## Progression { #progress }

Donnez un nombre entre `0.0` (rien n'est fait) et `1.0` (terminé) :

```python
for i, plane in enumerate(planes):
    ...                                   # traiter un plan
    ctx.progress((i + 1) / len(planes))
```

La barre de progression se remplit. Dans Fiji, la barre d'état en bas de la
fenêtre principale affiche aussi le nom du script et un pourcentage, comme
*Wavu: script 40%*.

## Annuler : pourquoi votre code doit aider { #cancel-why-your-code-has-to-help }

Dans Fiji, cliquez sur une fenêtre de Fiji et appuyez sur **Échap** ; le Log
affiche *Cancelling script…*. Dans napari, appuyez sur **Cancel** dans le
panneau Wavu ; le journal affiche *Cancelling...* puis, une fois votre
script arrêté, *Cancelled.* Mais on ne peut pas interrompre Python
proprement de l'extérieur au milieu d'un calcul : Wavu se contente donc de
**lever un drapeau**. Votre code regarde ce drapeau aux moments opportuns et
s'arrête poliment. On appelle cela l'**annulation coopérative**.

Le modèle le fait dans sa boucle :

```python
for i, plane in enumerate(planes):
    if ctx.cancelled():
        ctx.log("Cancelled")
        return {}
    ...
```

Plus court : `ctx.check_cancelled()` arrête l'exécution sur-le-champ si
l'utilisateur a annulé (il lève une erreur spéciale, `wavu.Cancelled`, que
Wavu gère en silence).

```python
ctx.check_cancelled()       # entre deux étapes lentes
masks = model.eval(img)
ctx.check_cancelled()
```

!!! warning "Annuler pendant un seul long appel"
    Si votre script passe cinq minutes dans un seul appel, comme un gros
    `model.eval(...)`, Échap ou **Cancel** ne prend effet qu'*après* le
    retour de cet appel. Découper le travail (plan par plan, tuile par
    tuile) rend l'annulation quasi instantanée.

## Un modèle à copier

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    ctx.log("Step 1/3: smoothing")
    smooth = smooth_image(img)
    ctx.progress(0.3)
    ctx.check_cancelled()

    ctx.log("Step 2/3: segmenting")
    labels = segment(smooth)
    ctx.progress(0.8)
    ctx.check_cancelled()

    ctx.log("Step 3/3: measuring")
    table = measure(labels, img)
    ctx.progress(1.0)
    return {"labels": labels, "cells": table}
```

(`smooth_image`, `segment` et `measure` représentent vos propres fonctions.)

## En une phrase

Utilisez `ctx.log` pour parler, `ctx.progress` pour montrer où vous en êtes,
et vérifiez `ctx.cancelled()` entre les étapes pour qu'Échap (Fiji) ou
**Cancel** (napari) puisse arrêter votre script.

[Suite : les vraies images :material-arrow-right:](real-images.md){ .md-button }
