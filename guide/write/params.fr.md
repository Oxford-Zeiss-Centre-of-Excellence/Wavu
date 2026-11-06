# PARAMS = votre boîte de dialogue

## L'idée en mots simples

`PARAMS`, c'est la **carte** que votre serveur tend au client. Vous listez
ce qu'on peut choisir, et le visualiseur dessine les champs pour vous : Fiji
sous forme de boîte de dialogue, napari sous forme de formulaire dans le
panneau Wavu. Pas de boutons ni de fenêtres à programmer, et le même
`PARAMS` fonctionne dans les deux. Chaque entrée a un **nom** (ce
qu'utilise votre code), un **type** (quel genre de champ), une valeur par
**défaut** (ce qui est rempli au départ) et un **libellé** facultatif (le
texte que l'utilisateur lit).

```mermaid
flowchart LR
    P["Entrée de PARAMS<br/>&quot;sigma&quot;: {type: float,<br/>default: 2.0,<br/>label: Sigma (pixels)}"]:::script
    D["Champ de dialogue / formulaire<br/>Sigma (pixels) [2.000]"]:::fiji
    R["Dans run() :<br/>params[&quot;sigma&quot;] == 2.0"]:::worker
    P --> D --> R

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
```

## Tous les types de champ dans un seul exemple

```python
"""Field types demo -- one of each."""

PARAMS = {
    "image":  {"type": "image", "label": "Nuclei image"},
    "sigma":  {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
    "n":      {"type": "int",   "default": 3},
    "name":   {"type": "str",   "default": "cells"},
    "fast":   {"type": "bool",  "default": True},
    "method": {"type": "choice", "choices": ["otsu", "li"], "default": "otsu"},
}
```

Chaque visualiseur en fait ses propres champs ; votre code reçoit les mêmes
valeurs :

| `type` | Champ dans Fiji | Champ dans napari | Ce que `run` reçoit |
|---|---|---|---|
| `float` | case numérique (3 décimales) | case numérique avec décimales | un nombre décimal, p. ex. `2.0`, dans `params` |
| `int` | case numérique (sans décimales) | case de nombre entier | un nombre entier, p. ex. `3`, dans `params` |
| `str` | case de texte | case de texte | du texte, p. ex. `"cells"`, dans `params` |
| `bool` | case à cocher | case à cocher | `True` ou `False`, dans `params` |
| `choice` | liste déroulante | liste déroulante | le texte choisi, p. ex. `"otsu"`, dans `params` |
| `image` | liste déroulante des **images ouvertes** | liste déroulante des **calques Image et Labels** | un tableau NumPy dans **`inputs`** (pas `params`) |

La liste déroulante des calques de napari se met à jour toute seule quand
vous ajoutez ou supprimez un calque.

## Les petits caractères

- **`default` est obligatoire** pour tous les types sauf `image`. Pour
  `choice`, on peut l'omettre ; le premier élément est alors utilisé.
- **`choices`** est obligatoire pour `choice` : une liste des options.
- **`label` est facultatif.** Sans lui, les deux visualiseurs affichent le
  nom avec une majuscule au début et les `_` remplacés par des espaces :
  `min_area` devient *Min area*.
- Les **noms** doivent être des noms Python valides : lettres, chiffres et
  `_`, sans commencer par un chiffre.
- **Les valeurs sont vérifiées** avant que votre code ne tourne. Un mauvais
  type ou une option inconnue est refusé avec un message : `run` reçoit donc
  toujours des valeurs propres, du type déclaré.
- La **première ligne de la docstring** en haut de `script.py` s'affiche en
  haut de la boîte de dialogue de Fiji et dans le panneau napari.
- La boîte de dialogue de Fiji ajoute une case supplémentaire,
  **Debug in VS Code**, pour le [débogage](../help/debug-in-vscode.md).
  Laissez-la décochée normalement.

!!! info "Un champ `image` a besoin d'une image ouverte"
    Si votre script a un champ `image` et que rien n'est ouvert, Wavu
    s'arrête avec un message : dans Fiji *"… needs an image -- open one
    first"*, dans napari *"…: open an image layer first"*. Ouvrez une image
    et relancez.

## Deux images ? Deux champs

Vous voulez une image des noyaux *et* une image du cytoplasme ? Ajoutez deux
entrées `image`. Chacune devient sa propre liste déroulante, et chacune
arrive dans `inputs` sous son propre nom :

```python
PARAMS = {
    "nuclei": {"type": "image", "label": "Nuclei"},
    "cyto":   {"type": "image", "label": "Cytoplasm"},
}

def run(ctx, inputs, params):
    nuc, cyto = inputs["nuclei"], inputs["cyto"]
    ...
```

## En une phrase

Écrivez une ligne de `PARAMS` par réglage, avec un type et une valeur par
défaut, et Fiji ou napari construit les champs et vous donne les valeurs
vérifiées dans `params` (les images dans `inputs`).

[Suite : ce que vous pouvez renvoyer :material-arrow-right:](outputs.md){ .md-button }
