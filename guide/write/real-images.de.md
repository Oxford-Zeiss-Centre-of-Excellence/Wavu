# Echte Bilder

## Die Idee in einfachen Worten

*Blobs* ist ein einzelnes flaches Bild. Ihre Mikroskopbilder sind oft ein
**Stapel von Bildern**: mehrere Farbkanäle, mehrere Fokusebenen (ein
Z-Stapel), vielleicht mehrere Zeitpunkte. Wavu reicht Ihrem Skript den
**ganzen Stapel** als ein einziges NumPy-Array und sagt Ihnen, wie er
gestapelt ist. Das ist, als bekämen Sie eine Kiste Objektträger zusammen mit
einem Zettel, auf dem steht, wie sie sortiert sind.

![Ein Stapel von Bildebenen: Zeit, Z, Kanal, dann Y und X](../assets/img/axes.svg){ width="640" }

## Welche Form das Array hat

Die Achsen kommen immer in dieser Reihenfolge, und jede Achse der Länge 1
fällt weg:

**T** (Zeit) · **Z** (Ebenen) · **C** (Kanäle) · **Y** · **X**, dazu eine
letzte Achse **S** der Länge 3 bei einem RGB-Farbbild.

| Bild in Fiji | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
|---|---|---|
| ein 2-D-Graustufenbild, 512 × 512 | `(512, 512)` | `"YX"` |
| 3 Kanäle | `(3, 512, 512)` | `"CYX"` |
| Z-Stapel mit 20 Ebenen, 2 Kanäle | `(20, 2, 512, 512)` | `"ZCYX"` |
| ein RGB-Foto | `(512, 512, 3)` | `"YXS"` |

„Kanal 2 jeder Ebene“ ist also `img[:, 1]` bei einem `ZCYX`-Bild. Fiji
schickt 8-Bit-, 16-Bit-, 32-Bit- oder RGB-Pixel unverändert.

## Was Sie außerdem bekommen: `ctx.meta` { #what-else-you-get-ctxmeta }

`ctx.meta["image"]` enthält, was Fiji über das für das Feld `"image"`
gewählte Bild weiß:

- `"axes"`: die Achsenbuchstaben, wie oben;
- `"pixel_um"`: die Pixelgröße in Mikrometern, falls das Bild kalibriert ist;
- `"title"`: den Fenstertitel.

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"]["axes"]
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel (Image › Duplicate…)")
    ...
```

Die Form zu prüfen und einen klaren `ValueError` auszulösen ist freundlicher,
als Ihren Code später abstürzen zu lassen: Fiji zeigt den Satz in einem
Fehlerfenster.

## Wie groß ist zu groß? { #how-big-is-too-big }

Wavu ist gemacht für **interaktives Arbeiten an einem Bild, das bequem in
den Arbeitsspeicher passt**, etwa bis **1–2 GB**. Kleine Bilder reisen in
einer einzigen Nachricht; größere werden über eine temporäre TIFF-Datei auf
Ihrer Festplatte übergeben. Sie müssen nichts tun: `inputs["image"]` ist in
beiden Fällen ein NumPy-Array.

Jenseits dieser Größe, oder für Hunderte von Dateien, ist Wavu das falsche
Werkzeug. Konvertieren Sie nach OME-Zarr und nehmen Sie besser einen
Batch-Workflow oder einen Rechencluster (HPC).

## Langsame erste Durchläufe (und wie Sie die Benutzer beruhigen) { #slow-first-runs-and-how-to-keep-users-calm }

Zwei Dinge können einen *ersten* Durchlauf langsam machen, und beide
passieren nur einmal:

1. **Die Umgebung wird gebaut.** pixi lädt die Pakete herunter, die in
   `pixi.toml` stehen. Mit PyTorch (das Cellpose braucht) können das
   **1–2 GB** und mehrere Minuten sein. Fijis Log sagt Bescheid, während es
   passiert.
2. **Modellgewichte werden heruntergeladen.** Werkzeuge wie Cellpose holen
   ihr trainiertes Modell beim ersten Gebrauch aus dem Internet. Das
   passiert *in Ihrem Skript*, also weiß Fiji nichts davon und wirkt
   vielleicht wie eingefroren.

**Schreiben Sie vor einem langsamen Schritt immer ins Log**, damit der
Benutzer weiß, was los ist:

```python
ctx.log("Loading the Cellpose model (the first time, it is downloaded)...")
ctx.progress(0.1)
model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
ctx.log("Model ready")
```

!!! tip "Ein funktionierendes Cellpose-Setup"
    Das Wavu-Repository enthält ein vollständiges Cellpose-Skript für
    Zellkerne, mit einer `pixi.toml` samt PyTorch, Cellpose und einem
    optionalen NVIDIA-GPU-Setup:
    [`examples/cellpose_nuclei`](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/tree/main/examples/cellpose_nuclei).
    Kopieren Sie seine Zeilen `[dependencies]` und `[pypi-dependencies]` in
    Ihre eigene `pixi.toml`. Macs mit Apple-Chip nutzen ihre GPU ohne
    weiteres Zutun.

## In einem Satz

Ihr Skript bekommt das ganze Bild als ein Array in der Reihenfolge
**T Z C Y X** (lesen Sie zur Sicherheit `ctx.meta`), es sollte unter etwa
1–2 GB bleiben, und vor allem Langsamen, etwa dem ersten Download eines
Modells, sollten Sie `ctx.log` aufrufen.

[Weiter: mit dem eigenen Labor teilen :material-arrow-right:](../share/with-your-lab.md){ .md-button }
