# Echte Bilder

## Die Idee in einfachen Worten

*Blobs* ist ein einzelnes flaches Bild. Ihre Mikroskopbilder sind oft ein
**Stapel von Bildern**: mehrere Farbkanäle, mehrere Fokusebenen (ein
Z-Stapel), vielleicht mehrere Zeitpunkte. Wavu reicht Ihrem Skript den
**ganzen Stapel** als ein einziges NumPy-Array und sagt Ihnen, wenn der
Viewer es weiß, wie er gestapelt ist. Das ist, als bekämen Sie eine Kiste Objektträger zusammen mit
einem Zettel, auf dem steht, wie sie sortiert sind.

![Ein Stapel von Bildebenen: Zeit, Z, Kanal, dann Y und X](../assets/img/axes.svg){ width="640" }

## Welche Form das Array hat

=== "Fiji"

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

=== "napari"

    Sie bekommen die Daten des gewählten Layers so, wie sie sind, in der
    Achsenreihenfolge des Layers: Ein Z-Stapel-Layer kommt als
    `(20, 512, 512)` an. napari öffnet meist jeden Kanal als eigenen Layer,
    wählen Sie also den Kanal, den Sie brauchen.

    | Layer in napari | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | ein 2-D-Graustufenbild | `(512, 512)` | `"YX"` |
    | ein Z-Stapel mit 20 Ebenen | `(20, 512, 512)` | `"ZYX"`, wenn die Achsenbeschriftungen des Layers z, y, x lauten; sonst nicht gesetzt |
    | ein RGB-Foto | `(512, 512, 3)` | `"YXS"` |

    Ein **Multiscale**-Layer (eine Bildpyramide) schickt seine Stufe mit voller
    Auflösung. 2-D- und RGB-Layer kommen immer mit Achsenbuchstaben; größere
    Layer nur, wenn die Achsenbeschriftungen in napari einfache Buchstaben
    sind (t, z, c, y, x), wie sie OME-Zarr-Reader setzen. Lesen Sie die Achsen
    also mit `.get("axes")` und schauen Sie auf `img.ndim` und `img.shape`.

## Was Sie außerdem bekommen: `ctx.meta` { #what-else-you-get-ctxmeta }

`ctx.meta["image"]` enthält, was der Viewer über das für das Feld `"image"`
gewählte Bild weiß:

- `"axes"`: die Achsenbuchstaben, wie oben (in Fiji immer; in napari bei 2-D-
  und RGB-Layern sowie bei größeren Layern, deren Achsenbeschriftungen
  t/z/c/y/x lauten);
- `"pixel_um"`: die Pixelgröße in Mikrometern, falls bekannt: aus der
  Kalibrierung des Bildes in Fiji, aus der **scale** des Layers in napari
  (wenn deren letzte zwei Werte gleich und nicht 1 sind);
- `"title"`: den Fenstertitel (Fiji) oder den Layernamen (napari).

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"].get("axes")      # None, wenn der Viewer es nicht angab
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel")
    ...
```

Die Form zu prüfen und einen klaren `ValueError` auszulösen ist freundlicher,
als Ihren Code später abstürzen zu lassen: Fiji zeigt den Satz in einem
Fehlerfenster, napari im Log des Panels und in einer Benachrichtigung.

??? tip "Achsenreihenfolge: T C Z Y X empfohlen (Speicher, Transport, Rechnen)"

    Wavu ordnet nichts um: Fiji sendet **T Z C Y X** (die Reihenfolge der
    ImageJ-Hyperstacks), napari sendet die Reihenfolge des Layers, und Fiji
    erwartet Ergebnisse in seiner Reihenfolge zurück. In Ihrem Skript haben
    Sie freie Wahl. Wir empfehlen **T C Z Y X**; hier die Wahlmöglichkeiten
    je Ebene:

    | Ebene | empfohlen | Alternativen | die Alternative wählen, wenn |
    |---|---|---|---|
    | **Speicher** (Dateien auf der Festplatte) | OME-Zarr in **T C Z Y X** (oder C Z Y X, Z Y X) | ImageJ-TIFF in **T Z C Y X** | kleine Daten, die Sie meist in Fiji öffnen (ein ImageJ-TIFF kann nur seine eigene Reihenfolge speichern) |
    | **Transport** (Wavu ↔ Ihr Skript) | am Anfang von `run()` in **T C Z Y X**, C-zusammenhängend, umwandeln; vor der Rückgabe zurückwandeln | behalten, was Wavu liefert (**T Z C Y X** aus Fiji) | Verarbeitung Ebene für Ebene (Filter, Schwellenwerte), bei der die Reihenfolge keine Rolle spielt |
    | **Rechnen** (NumPy, PyTorch, GPU) | **T C Z Y X**: ein Zeitpunkt ist `(C, Z, Y, X)`, mit Batch-Achse PyTorchs `(N, C, D, H, W)` | **channels last** (B Z Y X C) nur im GPU-Speicher: `tensor.to(memory_format=torch.channels_last_3d)`; Standard bei TensorFlow/Keras | 3-D-Faltungen in gemischter Genauigkeit auf neueren NVIDIA-GPUs; Keras-Modelle |

    Warum T C Z Y X? Vier Dinge ziehen an der Achsenreihenfolge, und diese
    dient allen:

    1. **Das Mikroskop.** Die Kamera liest jeweils ein **Y × X**-Bild aus (am
       schnellsten), ein Piezotisch fährt in **Z**, Filter oder Laser
       wechseln **C**, und das Zeitintervall **T** ist am langsamsten. Y, X
       ganz innen und Z daneben zu halten folgt der Art, wie die Daten
       aufgenommen werden, und hält das 3-D-Volumen zusammen. (Die genaue
       Z/C-Schleifenreihenfolge unterscheidet sich zwischen Aufbauten.)
    2. **Speicher und Chunks.** NumPy- und Zarr-Arrays sind *C-zusammenhängend*:
       die letzte Achse ändert sich am schnellsten. Mit T C Z Y X ist ein
       Chunk wie `(1, 1, 64, 512, 512)` ein kompakter 3-D-Block **eines
       Kanals**, sodass das Lesen nur von Kanal 0 (etwa DAPI) nur diese
       Dateien liest; mit verschachtelten Kanälen holt jeder Lesezugriff alle
       Kanäle. Die
       [OME-NGFF-Spezifikation](https://ngff.openmicroscopy.org/0.4/#axes-md)
       verlangt deshalb zuerst die Zeit, dann den Kanal, dann den Raum
       (Versionen 0.4 und 0.5; ein Vorschlag, das zu lockern,
       [RFC-3](https://ngff.openmicroscopy.org/rfc/3/index.html), wird noch
       geprüft). Fiji, napari und Bio-Formats lesen es alle. Daten auf der
       Festplatte werden jahrzehntelang aufbewahrt; GPUs wechseln alle paar
       Jahre.
    3. **Deep Learning.** `(C, Z, Y, X)` plus eine Batch-Achse ist genau, was
       [PyTorchs `Conv3d`](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv3d.html)
       erwartet, `(N, C, D, H, W)`. `torch.from_numpy()` auf einem
       C-zusammenhängenden Array teilt dessen Speicher: nichts wird kopiert.
    4. **Die GPU.** NVIDIA-Tensor-Cores können 3-D-Faltungen in gemischter
       Genauigkeit (FP16/BF16) schneller ausführen, wenn die Kanäle ganz
       innen liegen („channels last“). Konvertieren Sie **nur im
       GPU-Speicher**, direkt vor den aufwendigen Schichten; die Form bleibt
       `(N, C, D, H, W)`, nur die Strides ändern sich. Machen Sie Ergebnisse
       wieder zusammenhängend (`.contiguous()`), bevor sie die GPU verlassen.
       Die Vorliebe des Chips erreicht nie die Dateien.

    Hin- und Rückumwandlung in Ihrem Skript:

    ```python
    import numpy as np
    import wavu

    def to_tczyx(img, axes):
        """Reorder to T, C, Z, Y, X (only the axes present). Returns (array, new axes)."""
        new = "".join(a for a in "TCZYX" if a in axes)
        return np.ascontiguousarray(np.transpose(img, [axes.index(a) for a in new])), new

    def back(arr, axes_now, axes_wanted):
        """Reorder a result back, e.g. to the input's own order before returning it."""
        return np.ascontiguousarray(np.transpose(arr, [axes_now.index(a) for a in axes_wanted]))

    def run(ctx, inputs, params):
        axes = ctx.meta["image"].get("axes") or "YX"    # aus Fiji z. B. "TZCYX" oder "ZCYX"
        x, ours = to_tczyx(inputs["image"], axes)       # z. B. (C, Z, Y, X), "CZYX"
        # PyTorch: ein Zeitpunkt mit Batch-Achse, ohne Kopie
        #   batch = torch.from_numpy(x)[None]           # (1, C, Z, Y, X) bei "CZYX"
        y = x * 2                                       # Ihre Berechnung, gleiches Layout heraus
        return {"result": wavu.Image(back(y, ours, axes), axes=axes)}
    ```

    (RGB-Bilder, deren Achsen auf `S` enden, sind hier ausgelassen: wandeln
    Sie sie zuerst in Graustufen um oder trennen Sie die Farben. Kommt ein
    napari-Layer ohne `axes` an, kennen Sie seine Reihenfolge am besten:
    geben Sie die Buchstaben selbst an.)

## Wie groß ist zu groß? { #how-big-is-too-big }

Wavu ist gemacht für **interaktives Arbeiten an einem Bild, das bequem in
den Arbeitsspeicher passt**, etwa bis **1–2 GB**. Kleine Bilder reisen in
einer einzigen Nachricht; größere werden über eine temporäre TIFF-Datei auf
Ihrer Festplatte übergeben. Sie müssen nichts tun: `inputs["image"]` ist in
beiden Fällen ein NumPy-Array. Die Grenze ist in Fiji und napari dieselbe.

!!! warning "napari: große Lazy-Layer werden vollständig geladen"
    napari kann riesige Bilder „lazy“ anzeigen (ein *dask*-Array) und dabei
    nur den sichtbaren Teil lesen. Wavu kann das nicht: Es lädt den ganzen
    Layer in den Arbeitsspeicher, bevor es ihn schickt. Wählen Sie also einen
    Layer, der in den Speicher passt (einen Ausschnitt, einen Kanal oder eine
    Kopie mit geringerer Auflösung).

Jenseits dieser Größe konvertieren Sie nach OME-Zarr und lassen das Skript
die Daten Stück für Stück lesen: Die
[Streaming-Analyse](../workflows/large-data.md) schafft bis etwa 50 GB auf
einem lokalen Computer. Das funktioniert, aber es wird nicht empfohlen, sie
aus Fiji oder napari zu steuern. Für Hunderte von Dateien siehe
[Batch-Verarbeitung](../workflows/batch.md); ab etwa 50 GB nehmen Sie einen
Batch- oder HPC-Workflow.

## Langsame erste Durchläufe (und wie Sie die Benutzer beruhigen) { #slow-first-runs-and-how-to-keep-users-calm }

Zwei Dinge können einen *ersten* Durchlauf langsam machen, und beide
passieren nur einmal:

1. **Die Umgebung wird gebaut.** pixi lädt die Pakete herunter, die in
   `pixi.toml` stehen. Mit PyTorch (das Cellpose braucht) können das
   **1–2 GB** und mehrere Minuten sein. Fijis Log oder das Log des napari-Panels
   sagt Bescheid, während es passiert.
2. **Modellgewichte werden heruntergeladen.** Werkzeuge wie Cellpose holen
   ihr trainiertes Modell beim ersten Gebrauch aus dem Internet. Das
   passiert *in Ihrem Skript*, also weiß der Viewer nichts davon und wirkt
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

Ihr Skript bekommt das ganze Bild als ein Array (aus Fiji in der Reihenfolge
**T Z C Y X**, aus napari in der Reihenfolge des Layers; lesen Sie zur
Sicherheit `ctx.meta` und die Form; wir empfehlen, es in **T C Z Y X**
umzuordnen, die Reihenfolge von OME-NGFF und PyTorch), es sollte in beiden Viewern unter etwa
1–2 GB bleiben, und vor allem Langsamen, etwa dem ersten Download eines
Modells, sollten Sie `ctx.log` aufrufen.

[Weiter: als Container teilen :material-arrow-right:](container.md){ .md-button }
