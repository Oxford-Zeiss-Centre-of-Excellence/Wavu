# Große Daten: Streaming-Analyse

!!! warning "Es funktioniert, aber Fiji und napari sind nicht der Ort, um es zu steuern"
    Für **Bilder, die in den Arbeitsspeicher passen (etwa 1–2 GB)**, bleiben
    Sie beim normalen interaktiven Weg: Bild wählen, **OK** drücken,
    Ergebnis bekommen. Nichts auf dieser Seite ist dafür nötig.

    Mit blockweiser, gestreamter Verarbeitung (OME-Zarr) kann ein
    Wavu-Skript Daten **bis etwa 50 GB auf einem lokalen Computer**
    durcharbeiten. Aber Fiji und napari sind Canvas-basierte Betrachter,
    gebaut für Daten im Arbeitsspeicher: Während eines Streams sehen sie nur
    eine **kleine Vorschau oder das Endergebnis**, sie bleiben langsam,
    solange er läuft, und sie sind **nicht der empfohlene Ort, um ihn zu
    steuern**. Ab etwa 50 GB nehmen Sie besser eine Batch- oder
    HPC-Pipeline (siehe [das Ende dieser Seite](#when-not-to-do-this-in-fiji-or-napari)).

!!! info "Ein Entwurfsmuster, keine eingebaute Funktion"
    Alles Folgende beschreibt, wie **Sie** **Ihr eigenes Skript** schreiben.
    Wavu selbst übergibt nur einen Pfad und die Parameter an `run` und gibt
    den Pfad zurück, den Ihr Skript liefert. Chunks, dask und OME-Zarr sind
    Sache Ihres Skripts, und seine Pakete stehen in seiner eigenen
    `pixi.toml`.

## Die Idee in einfachen Worten { #the-idea-in-plain-words }

![Ein großer roher 3-D-Block auf einem Schneidebrett wird mit einem Messer in acht Stücke geschnitten; die Stücke gehen parallel an vier kleine Nebenküchen, die jeweils ein Stück auf einmal kochen; die gekochten Stücke werden auf einem Teller zur fertigen Mahlzeit zusammengesetzt, die leuchtet, wenn sie vollständig ist.](../assets/img/stream/sub-kitchens.svg){ width="800" }

*Das große Bild wird in Stücke geschnitten (die OME-Zarr-Chunks), und
mehrere Nebenküchen (parallele Worker) kochen jeweils ein Stück auf
einmal, sodass immer nur wenige Stücke gleichzeitig im Speicher sind. Die
gekochten Stücke werden auf einem Teller zu einer Mahlzeit
zusammengesetzt: dem Ergebnis.*

Zurück ins Restaurant. Eine Hochzeit hat ein Abendessen für fünfhundert
Gäste bestellt. Keine Arbeitsfläche fasst all diese Zutaten, also arbeitet
die Küche **in Durchgängen**: Sie holt die Zutaten **Kiste für Kiste**,
kocht mehrere Kisten gleichzeitig auf verschiedenen Herden und schickt die
Teller hinaus, sobald sie fertig sind. Der Kellner bringt an Ihren Tisch
nur einen **Probierteller**, um zu zeigen, dass das Gericht richtig
aussieht.

Bei Bildern sind die Kisten **Chunks**: ein großes Bild, zerlegt in ein
Raster kleiner Blöcke. Jeder Chunk wird als **eigene kleine Datei**
gespeichert, sodass ein Programm einen Chunk lesen kann, ohne den Rest
anzufassen.

![Ein großes Bild wird in ein Raster von Chunks zerlegt; jeder Chunk wird als eigene kleine Datei in einem OME-Zarr-Ordner gespeichert; ein Leser holt nur die Chunks, die er braucht, eine Datei nach der anderen, und die an jedem gemessenen Zahlen füllen eine Ergebnistabelle und einen Plot.](../assets/img/stream/zarr-chunking.svg){ width="800" }

*Aus einem großen Bild wird ein Ordner kleiner Dateien, eine pro Chunk. Ein
Leser holt nur die Dateien, die er braucht, eine nach der anderen, und was
er an jedem Chunk misst, wird zu einer Zeile der Ergebnistabelle und einem
Balken im Plot.*

## Warum OME-Zarr { #why-ome-zarr }

**OME-Zarr** (auch OME-NGFF genannt, Next-Generation File Format) ist ein
offenes Format genau dafür:

- **In Chunks.** Jeder Chunk ist eine eigene Datei; eine Region zu lesen
  kostet also eine Region, nicht das ganze Bild.
- **Multiskalig.** Das Bild wird zusätzlich in niedrigeren Auflösungen
  gespeichert (einer *Pyramide*); ein Betrachter zeigt zuerst die kleine
  Stufe und holt Details nur dort, wo Sie hineinzoomen.
- **Cloud-tauglich.** Derselbe Aufbau funktioniert in einem Ordner, auf
  einer Netzwerkfreigabe oder in einem Objektspeicher (S3).
- **Offen.** Ein Community-Standard von OME, lesbar mit napari, Fiji und
  Python.

Zum Vergleich **ein großes TIFF**: Die meisten Programme lesen es als eine
Datei von vorn bis hinten, ein klassisches TIFF endet bei 4 GB (BigTIFF
hebt diese Grenze auf), und es wird der Reihe nach von **einem einzigen
Schreiber** geschrieben. Gut für ein paar Gigabyte, mühsam für fünfzig.

## Streaming im Backend { #streaming-in-the-backend }

Der Trick: Der Kellner trägt die Zutaten nie selbst. Ihr Skript bekommt
keine Pixel; es bekommt einen **Pfad**.

![Ein OME-Zarr-Store, data.ome.zarr, mit der Eingabegruppe /image links und der Ausgabegruppe /label rechts; der Worker liest jeweils einen Chunk in seine kleine Speicherbox, verarbeitet ihn, schreibt den Ergebnis-Chunk in den passenden Platz von /label und lässt ihn los; jeder Chunk hinterlässt eine winzige Ergebnistabelle, und am Ende werden diese rechts zu einer zusammengesetzten Tabelle vereint.](../assets/img/stream/stream-loading.svg){ width="800" }

*Ein Store, zwei Gruppen: links die Gruppe `/image`, rechts die Gruppe
`/label`. Jeweils ein Chunk geht von `/image` in die kleine Speicherbox,
wird verarbeitet, an seinen Platz in `/label` geschrieben und verlässt den
Speicher. Jeder Chunk hinterlässt außerdem eine kleine Ergebnistabelle; am
Ende werden sie zu einer zusammengesetzten Tabelle vereint.*

Schritt für Schritt, innerhalb von `run`:

1. **Einen Pfad bekommen.** Hier ein Textparameter. (Ein Pfad, der als
   *Eingabe* geschickt wird und kein TIFF, CSV oder ZIP ist, kommt
   ebenfalls ungeöffnet an, als `pathlib.Path`; siehe
   [Daten auf der Leitung](../model/architecture.md#data-on-the-wire).)
2. **Ihn verzögert (lazy) öffnen.** `dask.array.from_zarr` kennt Form, Typ
   und Chunk-Raster, hat aber noch **keine Pixel** gelesen.
3. **Chunk für Chunk verarbeiten.** Sie beschreiben die Arbeit am ganzen
   Array; dask macht daraus eine kleine Aufgabe pro Chunk.
4. **Das Ergebnis neben die Eingabe schreiben**, nicht in `ctx.tmpdir`, das
   gelöscht wird, wenn der Worker stoppt.
5. **Einen `Path` und ein kleines Vorschau-Array zurückgeben.** Der Pfad
   erscheint im Log; die Vorschau (deutlich unter der 4-MiB-Grenze für die
   direkte Übertragung) öffnet sich als gewöhnliches Bild.

## Parallele Verarbeitung mit dask { #parallel-processing-with-dask }

[dask](https://docs.dask.org/en/stable/array.html) ist der Küchenchef: Er
verteilt die Kisten auf die Herde.

![Vier Worker, als sich drehende Räder gezeichnet, nehmen jeweils einen anderen Chunk zusammen mit einem schmalen, von den Nachbarn geliehenen Rand, verarbeiten sie gleichzeitig und schneiden den Rand ab; jeder verarbeitete Chunk kommt zurück ins Ausgaberaster, und seine Zahlen werden zu einer neuen Zeile einer wachsenden Ergebnistabelle.](../assets/img/stream/parallel-processing.svg){ width="800" }

*Vier Worker verarbeiten vier Chunks gleichzeitig. Jeder Chunk trägt einen
schmalen Rand von seinen Nachbarn (den Halo), der danach abgeschnitten
wird. Jedes Ergebnis geht in zwei Richtungen: der verarbeitete Chunk zurück
an seinen Platz im Ausgaberaster (das Zusammensetzen der Chunks) und seine
Zahlen in eine neue Zeile der Ergebnistabelle (das Zusammensetzen der
Ergebnisse).*

- **`map_blocks`** wendet Ihre Funktion auf jeden Chunk einzeln an: richtig
  für alles, was jeweils nur ein Pixel betrachtet, etwa einen
  Schwellenwert.
- **`map_overlap`** fügt zuerst einen **Halo** von `depth` Pixeln hinzu,
  geliehen von den Nachbar-Chunks, wendet Ihre Funktion an und schneidet
  den Halo dann wieder ab. Filter, die Nachbarn betrachten (Gauß-Filter,
  Median, Morphologie), brauchen das, sonst entstehen Nähte an jeder
  Chunk-Grenze. `boundary="reflect"` legt fest, was am äußeren Bildrand
  geliehen wird. Für einen Gauß-Filter reicht ein `depth` von etwa
  `4 × sigma` Pixeln.

```python
import dask.array as da

image = da.from_zarr("D:/data/big.zarr", component="0")   # lazy, noch nichts gelesen
mask = image.map_blocks(lambda block: block > 500, dtype=bool)   # keine Nachbarn nötig
```

**Chunk-Größe.** Peilen Sie **einige zehn MB pro Chunk** an (zum Beispiel
64 × 512 × 512 `uint16` = 32 MB). Viel kleiner, und dask verbringt seine
Zeit mit Buchhaltung; viel größer, und jeder Herd braucht viel
Arbeitsfläche. Benutzen Sie `image.rechunk(...)`, wenn die Chunks auf der
Festplatte weit danebenliegen.

**Anzahl der Worker.** dasks Standard-Scheduler für Arrays nutzt
**Threads** in einem Prozess; sie teilen sich den Speicher, also kostet das
Weiterreichen von Chunks nichts. Wie viele, wählen Sie mit
`dask.config.set(num_workers=4)`. Wenn Ihre Funktion reines Python ist und
mit mehr Threads nicht schneller wird, probieren Sie
`scheduler="processes"`.

**Faustregel für den Speicher.** Spitzenspeicher ≈ **Worker × Chunk-Größe ×
3 bis 4** (Eingabe, Halo, eine Float-Kopie, Ausgabe). Vier Worker mit
32-MB-Chunks brauchen etwa ein halbes Gigabyte, egal wie groß das ganze
Bild ist.

## Der Aufbau des Codes { #the-code-design }

Ein Skriptordner fürs Streaming ist ein gewöhnlicher Wavu-Skriptordner.
Fügen Sie die Pakete zu seiner `pixi.toml` hinzu (alle auf conda-forge):

```toml
[dependencies]
dask = ">=2024.1"
zarr = ">=2.16"
ome-zarr = ">=0.9"     # conda-forge `ome-zarr`, importiert als ome_zarr
scipy = ">=1.10"
tifffile = ">=2023.1"
```

`script.py`, das Gerüst:

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
        self.ctx.check_cancelled()          # löst wavu.Cancelled aus, was dask stoppt


def run(ctx, inputs, params):
    store = Path(params["store"])
    sigma = params["sigma"]
    image = da.from_zarr(str(store), component="0")    # volle Auflösung, lazy
    ctx.log(f"{image.shape} {image.dtype}, chunks {image.chunksize}")

    depth = int(4 * sigma) + 1                         # der Halo, den ein Gauß-Filter braucht
    smoothed = image.astype(np.float32).map_overlap(
        ndimage.gaussian_filter, depth=depth, boundary="reflect", sigma=sigma)

    with dask.config.set(scheduler="threads", num_workers=4):
        if params["output_format"] == "ome-zarr":
            out = store.with_name(store.stem + "-smoothed.zarr")
            write_ome_zarr(smoothed, out, ctx)
        else:
            out = store.with_name(store.stem + "-smoothed.tif")
            write_tiff(smoothed, out, ctx)

        z = smoothed.shape[0] // 2                     # Vorschau: mittlere Ebene, verkleinert
        step = max(1, max(smoothed.shape[1:]) // 512)
        preview = smoothed[z, ::step, ::step].compute()
    return {"result": out, "preview": preview}
```

Die beiden Schreiber. **OME-Zarr** (der Standard) schreibt Chunk für Chunk,
parallel, und baut die Auflösungspyramide:

```python
def write_ome_zarr(arr, out, ctx):
    import zarr
    from ome_zarr.io import parse_url
    from ome_zarr.writer import write_image

    root = zarr.group(store=parse_url(str(out), mode="w").store)
    with WavuProgress(ctx):
        write_image(arr, group=root, axes="zyx", storage_options={"chunks": arr.chunksize})
```

**TIFF** läuft über **einen einzigen Schreiber**, Ebene für Ebene; es ist
also langsamer, kann nicht parallel laufen, und das Ergebnis ist eine große
Datei, die die meisten Betrachter als Ganzes lesen. Hier sitzen die
Fortschritts- und Abbruchprüfungen in der Schleife:

```python
def write_tiff(arr, out, ctx):
    import tifffile

    cz = arr.chunksize[0]

    def planes():                                      # jeweils ein Block von Ebenen
        for z0 in range(0, arr.shape[0], cz):
            ctx.check_cancelled()
            ctx.progress(z0 / arr.shape[0])
            yield from arr[z0:z0 + cz].compute()

    tifffile.imwrite(out, planes(), shape=arr.shape, dtype=arr.dtype, bigtiff=True)
```

Das Gerüst geht von einem 3-D-Bild `zyx` aus, dessen Stufe mit voller
Auflösung `0` ist, wie in einem OME-Zarr mit einem einzigen Bild. Für 4-D-
oder 5-D-Daten passen Sie `axes` und den Vorschau-Ausschnitt entsprechend
an.

**Der Aufruf.** Das Ausgabeformat ist nur ein Parameter; es gehört also zum
Aufruf und ist standardmäßig OME-Zarr:

=== "Groovy (Fiji)"

    ```groovy
    def r = wavu.run(folder, "script",          // folder: der Skriptordner
            [store: "D:/data/big.zarr", output_format: "ome-zarr"], [:])
    println r.files.result          // der Pfad des neuen OME-Zarr
    ```

=== "Python"

    ```python
    from wavu.client import Worker

    with Worker.start("path/to/stream-folder", on_log=print) as w:
        res = w.run("script", {"store": "D:/data/big.zarr", "output_format": "ome-zarr"})
        out = res.outputs["result"].value        # ein pathlib.Path
        preview = res.outputs["preview"].value   # ein kleines NumPy-Array
    ```

`store` ist ein einfacher Textparameter, also muss es ein Pfad sein, den
**der Worker** sehen kann. Wavu übersetzt die Pfade von Eingaben für einen
Container, aber nicht Textparameter: Für einen Worker in einem Container
tippen Sie den Pfad so ein, wie der Container ihn sieht.

**Das Ergebnis ansehen.** Öffnen Sie es lazy, sodass nur der sichtbare Teil
gelesen wird: in napari mit dem Reader
[napari-ome-zarr](https://github.com/ome/napari-ome-zarr)
(`viewer.open(out, plugin="napari-ome-zarr")`), in Fiji mit
**File › Import › HDF5/N5/Zarr/OME-NGFF…** (den N5-Plugins). Der Vorbehalt
vom Anfang gilt weiterhin: Durchblättern geht, das Ganze im Betrachter zu
analysieren nicht.

## Wann Sie das nicht in Fiji oder napari tun sollten { #when-not-to-do-this-in-fiji-or-napari }

- **Ab etwa 50 GB**, bei vielen Dateien oder vielen Stunden: Lassen Sie
  denselben Chunk-Code als **Batch-Job** auf einer Workstation laufen, ganz
  ohne Betrachter (`pixi run wavu run script.py --param store=D:/data/big.zarr`
  in einem Terminal), auf einem **HPC-Cluster** (dasks verteilter Scheduler
  verteilt die Chunks auf viele Maschinen) oder in der **Cloud** direkt
  neben den Daten im Objektspeicher.
- **Wenn das Ergebnis ein einziges TIFF** sein muss, das größer als der
  Arbeitsspeicher ist: möglich, aber langsam; nehmen Sie lieber OME-Zarr
  und konvertieren Sie nur den Teil, den Sie brauchen.

## In einem Satz { #in-one-sentence }

Für Daten, die zu groß für den Arbeitsspeicher sind, geben Sie Ihrem Skript
einen **Pfad** statt Pixeln, lassen dask das OME-Zarr Chunk für Chunk auf
mehreren Herden kochen, schreiben das Ergebnis neben die Eingabe und
schicken dem Betrachter nur einen Probierteller, während Wavu selbst nur
den Pfad hinein- und wieder hinausreicht.
