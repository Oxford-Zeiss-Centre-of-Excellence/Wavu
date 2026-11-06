# Log, Fortschritt und Abbrechen

## Die Idee in einfachen Worten

Wenn die Küche viel zu tun hat, sagt Ihnen ein guter Kellner, wie es steht:
„Ihre Suppe ist auf dem Herd“, „gleich fertig“. Und wenn Sie es sich anders
überlegen, können Sie abbestellen, aber der Koch entscheidet, wann er sicher
mit dem Rühren aufhören kann.

In Wavu ist `ctx` dieser Draht zwischen Küche und Tisch:

- `ctx.log("…")` schickt eine Meldung ins **Log**.
- `ctx.progress(0.5)` stellt den **Fortschrittsbalken** auf die Hälfte.
- `ctx.cancelled()` sagt Ihnen, ob der Benutzer **anhalten** möchte.

Ihr Code ist in beiden Viewern derselbe; nur wo etwas erscheint, ist
verschieden:

| | Fiji | napari |
|---|---|---|
| `ctx.log` und `print` | das **Log**-Fenster | das Log-Feld im Wavu-Panel |
| `ctx.progress` | Fijis Fortschrittsbalken, dazu *Wavu: script 40%* in der Statusleiste | der Fortschrittsbalken im Wavu-Panel |
| wie der Benutzer abbricht | **Esc** drücken | **Cancel** im Panel drücken |
| ein Fehler in Ihrem Code | ein Fehlerfenster, Details im Log | `Error: …` im Log des Panels, dazu eine Benachrichtigung |

```mermaid
flowchart RL
    S["Ihr run()"]:::script
    L["Log<br/>(Log-Fenster · Panel-Log)"]:::fiji
    P["Fortschrittsbalken"]:::fiji
    E["Esc · Cancel-Button"]:::fiji
    S -- "ctx.log(...)" --> L
    S -- "ctx.progress(0..1)" --> P
    E -. "ctx.cancelled() wird True" .-> S

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
```

## Ins Log schreiben { #logging }

```python
ctx.log(f"Segmenting a {img.shape} image")
```

Die Zeile erscheint sofort im Log, während Ihr Code noch läuft. Ein
einfaches `print(...)` in `run` tut dasselbe. Schreiben Sie *vor* jedem
langsamen Schritt ins Log, damit der Benutzer weiß, dass nichts hängt.

## Fortschritt { #progress }

Geben Sie eine Zahl von `0.0` (noch nichts getan) bis `1.0` (fertig) an:

```python
for i, plane in enumerate(planes):
    ...                                   # eine Ebene bearbeiten
    ctx.progress((i + 1) / len(planes))
```

Der Fortschrittsbalken füllt sich. In Fiji zeigt außerdem die Statusleiste
unten im Hauptfenster den Skriptnamen und einen Prozentwert, etwa
*Wavu: script 40%*.

## Abbrechen: warum Ihr Code mithelfen muss { #cancel-why-your-code-has-to-help }

Klicken Sie in Fiji auf ein Fiji-Fenster und drücken Sie **Esc**; im Log
steht *Cancelling script…*. Drücken Sie in napari **Cancel** im Wavu-Panel;
im Log steht *Cancelling...* und, sobald Ihr Skript angehalten hat,
*Cancelled.* Python lässt sich aber mitten in einer Berechnung
nicht sicher von außen unterbrechen, deshalb **setzt** Wavu nur **eine
Flagge** (ein Signal). Ihr Code schaut an sinnvollen Stellen nach dieser Flagge und hört
höflich auf. Das nennt man **kooperatives Abbrechen**.

Die Vorlage macht das in ihrer Schleife:

```python
for i, plane in enumerate(planes):
    if ctx.cancelled():
        ctx.log("Cancelled")
        return {}
    ...
```

Kürzer geht es mit `ctx.check_cancelled()`: Es beendet den Durchlauf sofort,
wenn der Benutzer abgebrochen hat (es löst einen speziellen Fehler `wavu.Cancelled`
aus, den Wavu stillschweigend behandelt).

```python
ctx.check_cancelled()       # zwischen zwei langsamen Schritten
masks = model.eval(img)
ctx.check_cancelled()
```

!!! warning "Abbrechen während eines einzigen langen Aufrufs"
    Verbringt Ihr Skript fünf Minuten in einem einzigen Aufruf, etwa einem
    großen `model.eval(...)`, wirken Esc oder **Cancel** erst, *nachdem* dieser Aufruf
    zurückkehrt. Teilen Sie die Arbeit auf (Ebene für Ebene, Kachel für
    Kachel), dann fühlt sich das Abbrechen sofort an.

## Ein Muster zum Abschreiben

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

(`smooth_image`, `segment` und `measure` stehen für Ihre eigenen Funktionen.)

## In einem Satz

Mit `ctx.log` reden Sie, mit `ctx.progress` zeigen Sie, wie weit Sie sind,
und wenn Sie zwischen den Schritten `ctx.cancelled()` prüfen, können Esc (Fiji)
oder **Cancel** (napari) Ihr Skript anhalten.

[Weiter: echte Bilder :material-arrow-right:](real-images.md){ .md-button }
