# Imágenes reales

## La idea en palabras sencillas

*Blobs* es una sola imagen plana. Tus imágenes de microscopio suelen ser una
**pila de imágenes**: varios canales de color, varios planos focales (un
z-stack), quizá varios puntos de tiempo. Wavu le pasa a tu script **la pila
entera** como un único array de NumPy y, cuando el visor lo sabe, te dice
cómo está apilada. Es como recibir una caja de portaobjetos junto con una
etiqueta que dice en qué orden están.

![Una pila de planos de imagen: tiempo, z, canal, y luego y y x](../assets/img/axes.svg){ width="640" }

## Qué forma tiene el array

=== "Fiji"

    Los ejes siempre vienen en este orden, y cualquier eje de longitud 1 se
    elimina:

    **T** (tiempo) · **Z** (planos) · **C** (canales) · **Y** · **X**, más un
    último eje **S** de longitud 3 para una imagen en color RGB.

    | Imagen en Fiji | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | una imagen gris 2-D, 512 × 512 | `(512, 512)` | `"YX"` |
    | 3 canales | `(3, 512, 512)` | `"CYX"` |
    | z-stack de 20 planos, 2 canales | `(20, 2, 512, 512)` | `"ZCYX"` |
    | una foto RGB | `(512, 512, 3)` | `"YXS"` |

    Así que "el canal 2 de cada plano" es `img[:, 1]` en una imagen `ZCYX`.
    Fiji envía los píxeles de 8 bits, 16 bits, 32 bits o RGB sin cambios.

=== "napari"

    Recibes los datos de la capa elegida tal cual, en el orden de ejes de la
    propia capa: una capa z-stack llega como `(20, 512, 512)`. napari suele
    abrir cada canal como su propia capa, así que elige el canal que quieras.

    | Capa en napari | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | una imagen gris 2-D | `(512, 512)` | `"YX"` |
    | un z-stack de 20 planos | `(20, 512, 512)` | `"ZYX"` si las etiquetas de ejes de la capa dicen z, y, x; si no, no se indica |
    | una foto RGB | `(512, 512, 3)` | `"YXS"` |

    Una capa **multiescala** (una pirámide de imágenes) envía su nivel de
    resolución completa. Las capas 2-D y RGB siempre llevan letras de ejes;
    las más grandes, solo cuando las etiquetas de ejes de napari son letras
    simples (t, z, c, y, x), como las ponen los lectores de OME-Zarr. Así que
    lee los ejes con `.get("axes")` y mira `img.ndim` e `img.shape`.

## Qué más recibes: `ctx.meta`

`ctx.meta["image"]` contiene lo que el visor sabe de la imagen elegida en el
campo `"image"`:

- `"axes"`: las letras de los ejes, como arriba (siempre en Fiji; en napari
  para capas 2-D y RGB, y para capas más grandes cuyas etiquetas de ejes son
  t/z/c/y/x);
- `"pixel_um"`: el tamaño de píxel en micrómetros, si se conoce: de la
  calibración de la imagen en Fiji, de la **escala** (scale) de la capa en
  napari (cuando sus dos últimos valores son iguales y distintos de 1);
- `"title"`: el título de la ventana (Fiji) o el nombre de la capa (napari).

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"].get("axes")      # None si el visor no lo indicó
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel")
    ...
```

Comprobar la forma y lanzar un `ValueError` claro es más amable que dejar que
tu código falle más tarde: Fiji muestra la frase en una ventana de error,
napari en el log del panel y en una notificación.

## ¿Cuánto es demasiado grande?

Wavu está pensado para **trabajo interactivo con una imagen que quepa
holgadamente en memoria**, aproximadamente hasta **1–2 GB**. Las imágenes
pequeñas viajan en un solo mensaje; las más grandes pasan por un archivo TIFF
temporal en tu disco. No tienes que hacer nada: `inputs["image"]` es un array
de NumPy en ambos casos. El límite es el mismo en Fiji y en napari.

!!! warning "napari: las capas grandes y perezosas se cargan enteras"
    napari puede mostrar imágenes enormes de forma perezosa (un array
    *dask*), leyendo solo la parte que está en pantalla. Wavu no puede: carga
    la capa entera en memoria antes de enviarla, así que elige una capa que
    quepa en memoria (un recorte, un canal o una copia de menor resolución).

Por encima de ese tamaño, o para cientos de archivos, Wavu no es la
herramienta adecuada. Convierte a OME-Zarr y usa un flujo de trabajo por
lotes o en un clúster (HPC).

## Primeras ejecuciones lentas (y cómo mantener tranquilos a los usuarios) { #slow-first-runs-and-how-to-keep-users-calm }

Dos cosas pueden hacer lenta una *primera* ejecución, y ambas ocurren solo
una vez:

1. **Se construye el entorno.** pixi descarga los paquetes que aparecen en
   `pixi.toml`. Con PyTorch (que necesita Cellpose) pueden ser **1–2 GB** y
   varios minutos. El Log de Fiji o el log del panel de napari lo avisan
   mientras ocurre.
2. **Se descargan los pesos del modelo.** Herramientas como Cellpose
   descargan su modelo entrenado de internet la primera vez que se usa. Esto
   ocurre *dentro de tu script*, así que el visor no sabe nada y puede
   parecer colgado.

**Escribe siempre en el log antes de un paso lento**, para que el usuario
sepa qué está pasando:

```python
ctx.log("Loading the Cellpose model (the first time, it is downloaded)...")
ctx.progress(0.1)
model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
ctx.log("Model ready")
```

!!! tip "Una configuración de Cellpose que funciona"
    El repositorio de Wavu tiene un script completo de Cellpose para
    núcleos, con un `pixi.toml` que incluye PyTorch, Cellpose y una
    configuración opcional para GPU NVIDIA:
    [`examples/cellpose_nuclei`](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/tree/main/examples/cellpose_nuclei).
    Copia sus líneas de `[dependencies]` y `[pypi-dependencies]` en tu
    propio `pixi.toml`. Los Mac con Apple silicon usan su GPU sin configurar
    nada.

## En una frase

Tu script recibe la imagen entera como un único array (en orden
**T Z C Y X** desde Fiji, en el orden propio de la capa desde napari; lee
`ctx.meta` y la forma para asegurarte), debería quedarse por debajo de unos
1–2 GB en cualquiera de los dos visores, y conviene usar `ctx.log` antes de
cualquier paso lento, como la primera descarga de un modelo.

[Siguiente: compartir como contenedor :material-arrow-right:](container.md){ .md-button }
