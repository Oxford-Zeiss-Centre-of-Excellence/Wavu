# Imágenes reales

## La idea en palabras sencillas

*Blobs* es una sola imagen plana. Tus imágenes de microscopio suelen ser una
**pila de imágenes**: varios canales de color, varios planos focales (un
z-stack), quizá varios puntos de tiempo. Wavu le pasa a tu script **la pila
entera** como un único array de NumPy, y te dice cómo está apilada. Es como
recibir una caja de portaobjetos junto con una etiqueta que dice en qué orden
están.

![Una pila de planos de imagen: tiempo, z, canal, y luego y y x](../assets/img/axes.svg){ width="640" }

## Qué forma tiene el array

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

Así que "el canal 2 de cada plano" es `img[:, 1]` en una imagen `ZCYX`. Fiji
envía los píxeles de 8 bits, 16 bits, 32 bits o RGB sin cambios.

## Qué más recibes: `ctx.meta`

`ctx.meta["image"]` contiene lo que Fiji sabe de la imagen elegida en el
campo `"image"`:

- `"axes"`: las letras de los ejes, como arriba;
- `"pixel_um"`: el tamaño de píxel en micrómetros, si la imagen está
  calibrada;
- `"title"`: el título de la ventana.

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"]["axes"]
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel (Image › Duplicate…)")
    ...
```

Comprobar la forma y lanzar un `ValueError` claro es más amable que dejar que
tu código falle más tarde: Fiji muestra la frase en una ventana de error.

## ¿Cuánto es demasiado grande?

Wavu está pensado para **trabajo interactivo con una imagen que quepa
holgadamente en memoria**, aproximadamente hasta **1–2 GB**. Las imágenes
pequeñas viajan en un solo mensaje; las más grandes pasan por un archivo TIFF
temporal en tu disco. No tienes que hacer nada: `inputs["image"]` es un array
de NumPy en ambos casos.

Por encima de ese tamaño, o para cientos de archivos, Wavu no es la
herramienta adecuada. Convierte a OME-Zarr y usa un flujo de trabajo por
lotes o en un clúster (HPC).

## Primeras ejecuciones lentas (y cómo mantener tranquilos a los usuarios) { #slow-first-runs-and-how-to-keep-users-calm }

Dos cosas pueden hacer lenta una *primera* ejecución, y ambas ocurren solo
una vez:

1. **Se construye el entorno.** pixi descarga los paquetes que aparecen en
   `pixi.toml`. Con PyTorch (que necesita Cellpose) pueden ser **1–2 GB** y
   varios minutos. El Log de Fiji lo avisa mientras ocurre.
2. **Se descargan los pesos del modelo.** Herramientas como Cellpose
   descargan su modelo entrenado de internet la primera vez que se usa. Esto
   ocurre *dentro de tu script*, así que Fiji no sabe nada y puede parecer
   colgado.

**Escribe siempre en el Log antes de un paso lento**, para que el usuario
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

Tu script recibe la imagen entera como un array en orden **T Z C Y X** (lee
`ctx.meta` para asegurarte), debería quedarse por debajo de unos 1–2 GB, y
conviene usar `ctx.log` antes de cualquier paso lento, como la primera
descarga de un modelo.

[Siguiente: probar sin Fiji :material-arrow-right:](test-without-fiji.md){ .md-button }
