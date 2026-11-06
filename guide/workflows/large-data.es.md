# Datos grandes: análisis en flujo

!!! warning "Funciona, pero Fiji y napari no son el lugar para dirigirlo"
    Para **imágenes que caben en memoria (unos 1–2 GB)**, sigue usando el
    camino interactivo normal: elige una imagen, pulsa **OK** y obtén el
    resultado. Nada de esta página hace falta para eso.

    Con procesamiento por bloques y en flujo (OME-Zarr), un script de Wavu
    puede trabajar con datos **de hasta unos 50 GB en un ordenador local**.
    Pero Fiji y napari son visores basados en un lienzo, pensados para datos
    en memoria: durante un flujo solo ven una **pequeña vista previa o el
    resultado final**, van lentos mientras dura y **no son el lugar
    recomendado para dirigirlo**. Por encima de unos 50 GB, usa en su lugar
    un pipeline por lotes o en HPC (mira
    [el final de esta página](#when-not-to-do-this-in-fiji-or-napari)).

!!! info "Un patrón de diseño, no una función integrada"
    Todo lo que sigue es cómo escribes **tú** **tu propio script**. Wavu
    solo pasa una ruta y los parámetros a `run`, y devuelve la ruta que tu
    script le entrega. Los bloques, dask y OME-Zarr son asunto de tu script,
    y sus paquetes viven en su propio `pixi.toml`.

## La idea en palabras sencillas

![Un gran bloque 3-D en bruto sobre una tabla de cortar se trocea con un cuchillo en ocho piezas; las piezas van en paralelo a cuatro pequeñas subcocinas, cada una cocinando una pieza a la vez; las piezas cocinadas se montan en un plato como la comida terminada, que brilla cuando está completa.](../assets/img/stream/sub-kitchens.svg){ width="800" }

*La imagen grande se trocea en piezas (los bloques, o chunks, de OME-Zarr),
y varias subcocinas (workers en paralelo) cocinan cada una una pieza a la
vez, así que solo hay unas pocas piezas en memoria al mismo tiempo. Las
piezas cocinadas se montan en un plato como una sola comida: el resultado.*

Volvamos al restaurante. Una boda ha pedido la cena para quinientos
invitados. En ninguna encimera caben todos esos ingredientes, así que la cocina
trabaja **por tandas**: va trayendo los ingredientes **caja a caja**, cocina
varias cajas a la vez en distintos fogones y saca los platos según están
listos. El camarero solo trae a tu mesa un **plato de degustación**, para
enseñarte que el plato tiene buena pinta.

Para las imágenes, las cajas son los **bloques** (*chunks*): una imagen
grande cortada en una cuadrícula de bloques pequeños. Cada bloque se guarda
como **su propio archivo pequeño**, así que un programa puede leer un bloque
sin tocar el resto.

![Una imagen grande se corta en una cuadrícula de bloques; cada bloque se guarda como su propio archivo pequeño en una carpeta OME-Zarr; un lector trae solo los bloques que necesita, un archivo cada vez, y los números medidos en cada uno llenan una tabla de resultados y una gráfica.](../assets/img/stream/zarr-chunking.svg){ width="800" }

*Una imagen grande se convierte en una carpeta de archivos pequeños, uno
por bloque. Un lector trae solo los archivos que necesita, uno cada vez, y
lo que mide en cada bloque se convierte en una fila de la tabla de
resultados y en una barra de la gráfica.*

## Por qué OME-Zarr

**OME-Zarr** (también llamado OME-NGFF, Next-Generation File Format) es un
formato abierto pensado justo para esto:

- **Por bloques.** Cada bloque es su propio archivo, así que leer una región
  cuesta una región, no la imagen entera.
- **Multiescala.** La imagen también se guarda a resoluciones más bajas (una
  *pirámide*); un visor muestra primero el nivel pequeño y solo trae detalle
  donde haces zoom.
- **Apto para la nube.** La misma estructura funciona en una carpeta, en una
  unidad de red o en almacenamiento de objetos (S3).
- **Abierto.** Un estándar comunitario de OME, que leen napari, Fiji y
  Python.

Compáralo con **un TIFF grande**: la mayoría de los programas lo leen como
un solo archivo de principio a fin, un TIFF clásico se para en 4 GB
(BigTIFF quita ese límite), y se escribe en orden a través de **un solo
escritor**. Bien para unos pocos gigabytes, un suplicio para cincuenta.

## Flujo en el backend

El truco es que el camarero nunca carga con los ingredientes. Tu script no
recibe píxeles; recibe una **ruta**.

![Un almacén OME-Zarr, data.ome.zarr, con el grupo de entrada /image a la izquierda y el grupo de salida /label a la derecha; el worker lee un bloque cada vez en su pequeña caja de memoria, lo procesa, escribe el bloque resultante en el hueco correspondiente de /label y lo suelta; cada bloque deja una pequeña tabla de resultados, y al final se juntan en una tabla montada a la derecha.](../assets/img/stream/stream-loading.svg){ width="800" }

*Un almacén, dos grupos: a la izquierda el grupo `/image`, a la derecha el
grupo `/label`. Un bloque cada vez va de `/image` a la pequeña caja de
memoria, se procesa, se escribe en su hueco de `/label` y sale de la
memoria. Cada bloque deja además una pequeña tabla de resultados; al final
se juntan en una sola tabla montada.*

Paso a paso, dentro de `run`:

1. **Recibe una ruta.** Aquí, un parámetro de texto. (Una ruta enviada como
   *entrada* que no sea TIFF, CSV ni ZIP también llega sin abrir, como un
   `pathlib.Path`; mira [los datos en tránsito](../model/architecture.md#data-on-the-wire).)
2. **Ábrela de forma perezosa.** `dask.array.from_zarr` conoce la forma, el
   tipo y la cuadrícula de bloques, pero todavía **no ha leído ningún
   píxel**.
3. **Procesa bloque a bloque.** Describes el trabajo sobre el array entero;
   dask lo convierte en una pequeña tarea por bloque.
4. **Escribe el resultado junto a la entrada**, no en `ctx.tmpdir`, que se
   borra cuando el worker se detiene.
5. **Devuelve un `Path` y un pequeño array de vista previa.** La ruta se
   escribe en el Log; la vista previa (muy por debajo del límite de 4 MiB
   para datos en línea) se abre como una imagen normal.

## Procesamiento en paralelo con dask

[dask](https://docs.dask.org/en/stable/array.html) es el jefe de cocina:
reparte las cajas entre los fogones.

![Cuatro workers, dibujados como ruedas que giran, toman cada uno un bloque distinto junto con un borde fino prestado de sus vecinos, los procesan a la vez y recortan el borde; cada bloque procesado vuelve a la cuadrícula de salida, y sus números se convierten en una fila nueva de una tabla de resultados que va creciendo.](../assets/img/stream/parallel-processing.svg){ width="800" }

*Cuatro workers procesan cuatro bloques a la vez. Cada bloque lleva un
borde fino de sus vecinos (el halo), que después se recorta. Cada resultado
va por dos caminos: el bloque procesado vuelve a su sitio en la cuadrícula
de salida (el montaje de bloques), y sus números a una fila nueva de la
tabla de resultados (el montaje de resultados).*

- **`map_blocks`** ejecuta tu función en cada bloque por separado: lo
  adecuado para todo lo que mira un píxel cada vez, como un umbral.
- **`map_overlap`** añade primero un **halo** de `depth` píxeles prestado de
  los bloques vecinos, ejecuta tu función y luego recorta el halo. Los
  filtros que miran a los vecinos (desenfoque gaussiano, mediana,
  morfología) lo necesitan, o te salen costuras en cada borde de bloque.
  `boundary="reflect"` dice qué tomar prestado en el borde exterior de la
  imagen. Para un gaussiano, basta con un `depth` de unos `4 × sigma`
  píxeles.

```python
import dask.array as da

image = da.from_zarr("D:/data/big.zarr", component="0")   # perezoso, aún no se ha leído nada
mask = image.map_blocks(lambda block: block > 500, dtype=bool)   # no hacen falta vecinos
```

**Tamaño de bloque.** Apunta a **decenas de MB por bloque** (por ejemplo,
64 × 512 × 512 `uint16` = 32 MB). Mucho más pequeño y dask pierde el tiempo
en papeleo; mucho más grande y cada fogón necesita mucho sitio en la
encimera. Usa `image.rechunk(...)` si los bloques en disco se alejan mucho
de eso.

**Número de workers.** El planificador por defecto de dask para arrays usa
**hilos** en un solo proceso; comparten memoria, así que pasarse bloques no
cuesta nada. Elige cuántos con `dask.config.set(num_workers=4)`. Si tu
función es Python puro y no va más rápido con más hilos, prueba
`scheduler="processes"`.

**Regla práctica de memoria.** Pico de memoria ≈ **workers × tamaño de
bloque × 3 a 4** (entrada, halo, una copia en float, salida). Cuatro
workers con bloques de 32 MB necesitan alrededor de medio gigabyte, sea
cual sea el tamaño de la imagen entera.

## El diseño del código

Una carpeta de script para flujo es una carpeta de script de Wavu normal.
Añade los paquetes a su `pixi.toml` (todos en conda-forge):

```toml
[dependencies]
dask = ">=2024.1"
zarr = ">=2.16"
ome-zarr = ">=0.9"     # `ome-zarr` de conda-forge, se importa como ome_zarr
scipy = ">=1.10"
tifffile = ">=2023.1"
```

`script.py`, el esqueleto:

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
        self.ctx.check_cancelled()          # lanza wavu.Cancelled, que detiene dask


def run(ctx, inputs, params):
    store = Path(params["store"])
    sigma = params["sigma"]
    image = da.from_zarr(str(store), component="0")    # resolución completa, perezoso
    ctx.log(f"{image.shape} {image.dtype}, chunks {image.chunksize}")

    depth = int(4 * sigma) + 1                         # el halo que necesita un gaussiano
    smoothed = image.astype(np.float32).map_overlap(
        ndimage.gaussian_filter, depth=depth, boundary="reflect", sigma=sigma)

    with dask.config.set(scheduler="threads", num_workers=4):
        if params["output_format"] == "ome-zarr":
            out = store.with_name(store.stem + "-smoothed.zarr")
            write_ome_zarr(smoothed, out, ctx)
        else:
            out = store.with_name(store.stem + "-smoothed.tif")
            write_tiff(smoothed, out, ctx)

        z = smoothed.shape[0] // 2                     # vista previa: plano central, reducido
        step = max(1, max(smoothed.shape[1:]) // 512)
        preview = smoothed[z, ::step, ::step].compute()
    return {"result": out, "preview": preview}
```

Los dos escritores. **OME-Zarr** (el predeterminado) escribe bloque a
bloque, en paralelo, y construye la pirámide de resoluciones:

```python
def write_ome_zarr(arr, out, ctx):
    import zarr
    from ome_zarr.io import parse_url
    from ome_zarr.writer import write_image

    root = zarr.group(store=parse_url(str(out), mode="w").store)
    with WavuProgress(ctx):
        write_image(arr, group=root, axes="zyx", storage_options={"chunks": arr.chunksize})
```

**TIFF** pasa por **un solo escritor**, plano tras plano, así que es más
lento, no puede ir en paralelo, y el resultado es un único archivo grande
que la mayoría de los visores leen entero. Aquí las comprobaciones de
progreso y de cancelación van dentro del bucle:

```python
def write_tiff(arr, out, ctx):
    import tifffile

    cz = arr.chunksize[0]

    def planes():                                      # un bloque de planos cada vez
        for z0 in range(0, arr.shape[0], cz):
            ctx.check_cancelled()
            ctx.progress(z0 / arr.shape[0])
            yield from arr[z0:z0 + cz].compute()

    tifffile.imwrite(out, planes(), shape=arr.shape, dtype=arr.dtype, bigtiff=True)
```

El esqueleto supone una imagen 3-D `zyx` cuyo nivel de resolución completa
es `0`, como en un OME-Zarr de una sola imagen. Para datos 4-D o 5-D,
cambia `axes` y el corte de la vista previa para que encajen.

**Llamarlo.** El formato de salida es solo un parámetro, así que forma parte
de la llamada y por defecto es OME-Zarr:

=== "Groovy (Fiji)"

    ```groovy
    def r = wavu.run(folder, "script",          // folder: la carpeta del script
            [store: "D:/data/big.zarr", output_format: "ome-zarr"], [:])
    println r.files.result          // la ruta del nuevo OME-Zarr
    ```

=== "Python"

    ```python
    from wavu.client import Worker

    with Worker.start("path/to/stream-folder", on_log=print) as w:
        res = w.run("script", {"store": "D:/data/big.zarr", "output_format": "ome-zarr"})
        out = res.outputs["result"].value        # un pathlib.Path
        preview = res.outputs["preview"].value   # un pequeño array de NumPy
    ```

`store` es un parámetro de texto normal, así que tiene que ser una ruta que
**el worker** pueda ver. Wavu traduce las rutas de las entradas para un
contenedor, pero no los parámetros de texto: para un worker en un
contenedor, escribe la ruta tal como la ve el contenedor.

**Ver el resultado.** Ábrelo de forma perezosa, para que solo se lea la
parte visible: en napari con el lector
[napari-ome-zarr](https://github.com/ome/napari-ome-zarr)
(`viewer.open(out, plugin="napari-ome-zarr")`), en Fiji con
**File › Import › HDF5/N5/Zarr/OME-NGFF…** (los plugins de N5). La
advertencia del principio sigue en pie: navegar funciona; analizarlo todo
dentro del visor, no.

## Cuándo no hacerlo en Fiji ni en napari { #when-not-to-do-this-in-fiji-or-napari }

- **Por encima de unos 50 GB**, muchos archivos o muchas horas: ejecuta el
  mismo código por bloques como un **trabajo por lotes** en una estación de
  trabajo, sin ningún visor
  (`pixi run wavu run script.py --param store=D:/data/big.zarr` en una
  terminal), en un **clúster HPC** (el planificador distribuido de dask
  reparte los bloques entre muchas máquinas), o en la **nube**, junto a los
  datos en almacenamiento de objetos.
- **Cuando el resultado tiene que ser un único TIFF** más grande que la
  memoria: es posible, pero lento; mejor usa OME-Zarr y convierte solo la
  parte que necesites.

## En una frase

Para datos demasiado grandes para la memoria, dale a tu script una **ruta**
en lugar de píxeles, deja que dask cocine el OME-Zarr bloque a bloque en
varios fogones, escribe el resultado junto a la entrada y manda al visor
solo un plato de degustación, mientras Wavu se limita a pasar la ruta de
entrada y la de salida.
