# Vom Notebook zu Wavu

## Die Idee in einfachen Worten

Eine Notebook-Zelle und ein Wavu-Skript erledigen dieselbe Arbeit; nur die
**Türen hinein und hinaus** ändern sich. Im Notebook tippen *Sie* die
Einstellungen, laden die Datei und sehen sich den Plot an. Bei Wavu füllt
**Fiji** die Einstellungen aus einem Dialog aus, reicht das bereits geöffnete
Bild weiter und zeigt an, was Sie zurückgeben. Ihre Analyse in der Mitte
bleibt gleich.

```mermaid
flowchart LR
    subgraph NB["Notebook"]
        A1["sigma = 2.0"]:::script
        A2["img = io.imread(...)"]:::script
        A3["Ihre Analyse"]:::worker
        A4["plt.imshow(labels)"]:::script
    end
    subgraph WV["Wavu-Skript"]
        B1["PARAMS → Dialog"]:::fiji
        B2["inputs['image']"]:::fiji
        B3["Ihre Analyse"]:::worker
        B4["return {'labels': labels}"]:::fiji
    end
    A1 -.-> B1
    A2 -.-> B2
    A3 -.-> B3
    A4 -.-> B4

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
```

## Die Übersetzungstabelle

| In Ihrem Notebook | In `script.py` | Was Sie in Fiji sehen |
|---|---|---|
| `sigma = 2.0` | `"sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"}` in `PARAMS`, dann `params["sigma"]` | ein Zahlenfeld **Sigma (pixels)** |
| `img = io.imread("cells.tif")` | `"image": {"type": "image"}` in `PARAMS`, dann `inputs["image"]` | eine Auswahlliste der geöffneten Bilder |
| `print("found", n)` | `ctx.log(f"found {n}")` (`print` geht auch) | eine Zeile im **Log**-Fenster |
| `plt.imshow(labels)` | `return {"labels": labels}` | ein neues Bildfenster namens *…-labels* |
| `df` (eine Tabelle) | `return {"cells": df}` | eine Results-Tabelle |

## Ein durchgespieltes Beispiel

Hier ist eine typische Notebook-Zelle, die Zellkerne per Schwellenwert
findet und zählt:

```python
from skimage import io, filters, measure

sigma = 2.0
img = io.imread("nuclei.tif")
smooth = filters.gaussian(img, sigma)
mask = smooth > filters.threshold_otsu(smooth)
labels = measure.label(mask)
print("found", labels.max(), "nuclei")
plt.imshow(labels)
```

Und dasselbe als Wavu-Skript. Ersetzen Sie den Inhalt von `script.py` durch:

```python
"""Count nuclei -- Otsu threshold after a Gaussian blur."""

PARAMS = {
    "image": {"type": "image", "label": "Nuclei image"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
}


def run(ctx, inputs, params):
    from skimage import filters, measure

    img = inputs["image"]                     # das im Dialog gewählte Bild
    smooth = filters.gaussian(img, params["sigma"])
    mask = smooth > filters.threshold_otsu(smooth)
    labels = measure.label(mask)
    ctx.log(f"found {labels.max()} nuclei")   # erscheint in Fijis Log
    return {"labels": labels}                 # öffnet sich als neues Bild
```

Das Skript braucht scikit-image, also fügen Sie zuerst
`scikit-image = "*"` zu `pixi.toml` hinzu
([wie](get-the-template.md#adding-a-package)). Speichern Sie beide Dateien,
klicken Sie auf **Stop Worker** und führen Sie es auf *Blobs* aus.

## Die drei Regeln

1. **`PARAMS` ganz oben** ist der Dialog. Jeder Eintrag wird zu einem Feld.
2. **`def run(ctx, inputs, params):`** ist der Ort, an dem gearbeitet wird.
   Bilder kommen in `inputs` an, die übrigen Einstellungen in `params`, und
   `ctx` ist Ihr direkter Draht zu Fiji (Log, Fortschrittsbalken, Abbrechen).
3. **Geben Sie ein Dictionary zurück.** Jeder Schlüssel wird zum Namen eines
   Ergebnisses (Fiji setzt den Bildnamen davor, wie bei *blobs-labels*),
   und jeder Wert wird auf die passende Art angezeigt.

!!! tip "Zwei Gewohnheiten, die Zeit sparen"
    - **Importieren Sie schwere Pakete innerhalb von `run`**, wie oben. Dann
      kann Fiji den Dialog sofort zeigen, ohne auf große Importe zu warten.
    - **Lösen Sie bei Bedienfehlern einen verständlichen Fehler aus**, zum
      Beispiel `raise ValueError("Please pick a single-channel image")`.
      Fiji zeigt die Meldung in einem Fehlerfenster.

Die erste Zeile des Docstrings (der Text in dreifachen Anführungszeichen ganz
oben) erscheint oben im Dialog; machen Sie also eine kurze Beschreibung
daraus.

## In einem Satz

Lassen Sie Ihre Analyse, wie sie ist; nehmen Sie einfach die Einstellungen
aus `params` und das Bild aus `inputs`, schreiben Sie Meldungen mit
`ctx.log` und geben Sie mit `return` zurück, was Sie sehen möchten.

[Weiter: PARAMS = Ihr Dialog :material-arrow-right:](params.md){ .md-button }
